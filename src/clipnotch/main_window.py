from pathlib import Path
import os
import tempfile
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
    QMessageBox,
)

from clipnotch.marker_model import MarkerModel
from clipnotch.waveform import compute_peaks
from clipnotch.waveform_view import WaveformView, ms_to_x
from clipnotch.interval_table import IntervalTable
from clipnotch.player import AudioPlayer
from clipnotch.download_worker import DownloadWorker
from clipnotch.export import export_intervals

SMALL_STEP_MS = 100
LARGE_STEP_MS = 1000
WAVEFORM_BUCKETS = 2000
ZOOM_STEP = 1.5
MIN_ZOOM = 0.25
MAX_ZOOM = 8.0
DOWNLOAD_CACHE_DIR = Path(tempfile.gettempdir()) / "clipnotch"
WINDOW_TITLE = "clipnotch"


def _wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as wf:
        return int(wf.getnframes() / wf.getframerate() * 1000)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)

        self.marker_model: MarkerModel | None = None
        self.playhead_ms = 0
        self.nav_point_ms = 0  # where Space-stop returns playback to; shown in blue
        self.loop_mode = False  # toggled by U; affects Enter's interval preview
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

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.waveform_view)
        self.scroll_area.setWidgetResizable(False)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.url_input)

        export_bar = QHBoxLayout()
        export_bar.addWidget(self.format_combo)
        export_bar.addWidget(choose_folder_button)
        export_bar.addWidget(self.export_button)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.scroll_area, stretch=2)
        layout.addWidget(self.interval_table, stretch=1)
        layout.addLayout(export_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.waveform_view.position_clicked.connect(self._set_playhead)
        self.player.position_changed.connect(self._on_player_position_changed)

        self.interval_table.setFocusPolicy(Qt.NoFocus)
        self.export_button.setFocusPolicy(Qt.NoFocus)
        choose_folder_button.setFocusPolicy(Qt.NoFocus)
        self.format_combo.setFocusPolicy(Qt.NoFocus)

        self.setFocusPolicy(Qt.StrongFocus)

    def _on_url_submitted(self) -> None:
        self.start_download(self.url_input.text().strip())

    def start_download(self, url: str) -> None:
        if not url:
            return
        self.url_input.setText(url)
        self._worker = DownloadWorker(url, DOWNLOAD_CACHE_DIR, self)
        self._worker.converted.connect(self.load_audio_file)
        self._worker.failed.connect(self._on_download_failed)
        self._worker.start()

    def _on_download_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Download failed", message)

    def load_audio_file(self, wav_path: Path, source_name: str | None = None) -> None:
        try:
            resolved_source_name = source_name if source_name is not None else wav_path.stem
            duration_ms = _wav_duration_ms(wav_path)
            marker_model = MarkerModel(duration_ms)
            peaks = compute_peaks(wav_path, WAVEFORM_BUCKETS)
        except Exception as exc:
            QMessageBox.critical(self, "Failed to load audio", str(exc))
            return

        self.wav_path = wav_path
        self.source_name = resolved_source_name
        self.marker_model = marker_model
        self.playhead_ms = 0
        self.nav_point_ms = 0
        self.player.load(wav_path)

        self.waveform_view.set_data(peaks, duration_ms)
        self._refresh_views()
        self.setFocus()

    def _on_player_position_changed(self, position_ms: int) -> None:
        self.playhead_ms = position_ms
        self._refresh_views()

    def _refresh_views(self) -> None:
        if self.marker_model is None:
            return
        self.waveform_view.set_markers(self.marker_model.markers)
        self.waveform_view.set_intervals(self.marker_model.intervals())
        self.waveform_view.set_playhead(self.playhead_ms)
        self.waveform_view.set_nav_point(self.nav_point_ms)
        self.interval_table.refresh(self.marker_model.intervals())
        self._ensure_playhead_visible()

    def _ensure_playhead_visible(self) -> None:
        if self.marker_model is None:
            return
        x = ms_to_x(self.playhead_ms, self.marker_model.duration_ms, self.waveform_view.width())
        self.scroll_area.ensureVisible(x, self.waveform_view.height() // 2, 50, 0)

    def _set_playhead(self, position_ms: int) -> None:
        self.playhead_ms = position_ms
        self._refresh_views()
        self.setFocus()

    def _on_choose_output_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Choose output folder", str(self.output_dir))
        if chosen:
            self.output_dir = Path(chosen)

    def _on_export_clicked(self) -> None:
        if self.marker_model is None or self.wav_path is None:
            return
        ext = self.format_combo.currentText()

        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not os.access(self.output_dir, os.W_OK):
            QMessageBox.critical(self, "Export failed", f"Cannot write to {self.output_dir}")
            return

        try:
            exported = export_intervals(
                self.wav_path,
                self.source_name,
                self.marker_model.intervals(),
                self.output_dir,
                ext,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return

        if not exported:
            QMessageBox.information(self, "Export complete", "No intervals were marked for export.")
        else:
            QMessageBox.information(
                self, "Export complete", f"Exported {len(exported)} file(s) to {self.output_dir}"
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
            if self.player.is_playing():
                self.player.stop()
                self.playhead_ms = self.nav_point_ms
                self._refresh_views()
            elif self.loop_mode:
                interval = self.marker_model.interval_containing(self.playhead_ms)
                if interval is not None:
                    self.player.play_looping(self.playhead_ms, interval.start_ms, interval.end_ms)
                else:
                    self.player.play_from(self.playhead_ms)
            else:
                self.player.play_from(self.playhead_ms)
        elif key == Qt.Key_S and not ctrl:
            # Stop in place: unlike Space, this does not rewind to the nav point
            # and does not move the nav point either.
            if self.player.is_playing():
                self.player.stop()
                self._refresh_views()
        elif key == Qt.Key_M:
            self.marker_model.add_marker(self.playhead_ms)
            self._refresh_views()
        elif key == Qt.Key_K:
            target = self.marker_model.prev_interval_start(self.playhead_ms)
            if target is not None:
                self.playhead_ms = target
                self.nav_point_ms = target
                self._refresh_views()
        elif key == Qt.Key_L:
            target = self.marker_model.next_interval_start(self.playhead_ms)
            if target is not None:
                self.playhead_ms = target
                self.nav_point_ms = target
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
            self.nav_point_ms = self.playhead_ms
            self._refresh_views()
        elif key == Qt.Key_U:
            self.loop_mode = not self.loop_mode
            self.setWindowTitle(f"{WINDOW_TITLE} [loop]" if self.loop_mode else WINDOW_TITLE)
        elif key == Qt.Key_X:
            self.marker_model.toggle_interval_at(self.playhead_ms)
            self._refresh_views()
        elif ctrl and key == Qt.Key_S:
            self._on_export_clicked()
        elif key in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom = max(MIN_ZOOM, min(MAX_ZOOM, self._zoom * ZOOM_STEP))
            self.waveform_view.set_zoom(self._zoom)
        elif key == Qt.Key_Minus:
            self._zoom = max(MIN_ZOOM, min(MAX_ZOOM, self._zoom / ZOOM_STEP))
            self.waveform_view.set_zoom(self._zoom)
        else:
            super().keyPressEvent(event)
