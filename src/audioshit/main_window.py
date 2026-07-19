from pathlib import Path
import wave

from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QScrollArea,
    QFileDialog,
)

from audioshit.marker_model import MarkerModel
from audioshit.waveform import compute_peaks
from audioshit.waveform_view import WaveformView
from audioshit.interval_table import IntervalTable
from audioshit.player import AudioPlayer
from audioshit.download_worker import DownloadWorker
from audioshit.export import export_intervals

SMALL_STEP_MS = 100
LARGE_STEP_MS = 1000
WAVEFORM_BUCKETS = 2000
ZOOM_STEP = 1.5


def _wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as wf:
        return int(wf.getnframes() / wf.getframerate() * 1000)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("audioshit")

        self.marker_model: MarkerModel | None = None
        self.playhead_ms = 0
        self.wav_path: Path | None = None
        self.source_name = "track"
        self.output_dir = Path.cwd()
        self._zoom = 1.0

        self.player = AudioPlayer(self)
        self.waveform_view = WaveformView()
        self.interval_table = IntervalTable()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste a YouTube URL and press Enter")
        self.url_input.returnPressed.connect(self._on_url_submitted)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["wav", "mp3", "flac"])

        self.export_button = QPushButton("Export (Ctrl+S)")
        self.export_button.clicked.connect(self._on_export_clicked)

        choose_folder_button = QPushButton("Choose output folder...")
        choose_folder_button.clicked.connect(self._on_choose_output_folder)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.waveform_view)
        scroll_area.setWidgetResizable(False)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.url_input)

        export_bar = QHBoxLayout()
        export_bar.addWidget(self.format_combo)
        export_bar.addWidget(choose_folder_button)
        export_bar.addWidget(self.export_button)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(scroll_area, stretch=2)
        layout.addWidget(self.interval_table, stretch=1)
        layout.addLayout(export_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.waveform_view.position_clicked.connect(self._set_playhead)

        self.setFocusPolicy(Qt.StrongFocus)

    def _on_url_submitted(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            return
        dest_dir = Path.cwd() / ".audioshit_downloads"
        self._worker = DownloadWorker(url, dest_dir, self)
        self._worker.finished.connect(self.load_audio_file)
        self._worker.start()

    def load_audio_file(self, wav_path: Path) -> None:
        self.wav_path = wav_path
        self.source_name = wav_path.stem
        duration_ms = _wav_duration_ms(wav_path)
        self.marker_model = MarkerModel(duration_ms)
        self.playhead_ms = 0
        self.player.load(wav_path)

        peaks = compute_peaks(wav_path, WAVEFORM_BUCKETS)
        self.waveform_view.set_data(peaks, duration_ms)
        self._refresh_views()

    def _refresh_views(self) -> None:
        if self.marker_model is None:
            return
        self.waveform_view.set_markers(self.marker_model.markers)
        self.waveform_view.set_intervals(self.marker_model.intervals())
        self.waveform_view.set_playhead(self.playhead_ms)
        self.interval_table.refresh(self.marker_model.intervals())

    def _set_playhead(self, position_ms: int) -> None:
        self.playhead_ms = position_ms
        self._refresh_views()

    def _on_choose_output_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Choose output folder", str(self.output_dir))
        if chosen:
            self.output_dir = Path(chosen)

    def _on_export_clicked(self) -> None:
        if self.marker_model is None or self.wav_path is None:
            return
        ext = self.format_combo.currentText()
        export_intervals(
            self.wav_path,
            self.source_name,
            self.marker_model.intervals(),
            self.output_dir,
            ext,
        )

    def event(self, event) -> bool:
        # Qt's focus-chain machinery intercepts Tab/Backtab in QWidget.event()
        # before keyPressEvent is ever invoked, moving focus between widgets
        # instead of delivering the key. Handle those keys here so Tab/Shift+Tab
        # reach our marker-jump logic instead of being consumed by focus traversal.
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            self.keyPressEvent(event)
            return True
        return super().event(event)

    def keyPressEvent(self, event) -> None:
        if self.marker_model is None:
            super().keyPressEvent(event)
            return

        key = event.key()
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        ctrl = bool(event.modifiers() & Qt.ControlModifier)
        duration_ms = self.marker_model.duration_ms

        if key == Qt.Key_Right:
            step = LARGE_STEP_MS if shift else SMALL_STEP_MS
            self.playhead_ms = min(duration_ms, self.playhead_ms + step)
            self._refresh_views()
        elif key == Qt.Key_Left:
            step = LARGE_STEP_MS if shift else SMALL_STEP_MS
            self.playhead_ms = max(0, self.playhead_ms - step)
            self._refresh_views()
        elif key == Qt.Key_Space:
            if self.player.position() and self.player._player.isPlaying():
                self.player.stop()
            else:
                self.player.play_from(self.playhead_ms)
        elif key == Qt.Key_M:
            self.marker_model.add_marker(self.playhead_ms)
            self._refresh_views()
        elif key in (Qt.Key_Backspace, Qt.Key_Delete):
            self.marker_model.remove_nearest_marker(self.playhead_ms)
            self._refresh_views()
        elif key in (Qt.Key_Tab, Qt.Key_Backtab):
            if shift or key == Qt.Key_Backtab:
                target = self.marker_model.prev_marker(self.playhead_ms)
            else:
                target = self.marker_model.next_marker(self.playhead_ms)
            if target is not None:
                self.playhead_ms = target
                self._refresh_views()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            interval = self.marker_model.interval_containing(self.playhead_ms)
            if interval is not None:
                self.player.play_once_range(interval.start_ms, interval.end_ms)
        elif key == Qt.Key_X:
            self.marker_model.toggle_interval_at(self.playhead_ms)
            self._refresh_views()
        elif ctrl and key == Qt.Key_S:
            self._on_export_clicked()
        elif key in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom *= ZOOM_STEP
            self.waveform_view.set_zoom(self._zoom)
        elif key == Qt.Key_Minus:
            self._zoom /= ZOOM_STEP
            self.waveform_view.set_zoom(self._zoom)
        else:
            super().keyPressEvent(event)
