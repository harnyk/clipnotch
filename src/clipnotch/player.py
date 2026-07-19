from pathlib import Path
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioPlayer(QObject):
    position_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._stop_at_ms: int | None = None
        self._loop_range: tuple[int, int] | None = None
        self._player.positionChanged.connect(self._on_position_changed)

    def load(self, path: Path) -> None:
        self._player.setSource(QUrl.fromLocalFile(str(path)))

    def play_from(self, position_ms: int) -> None:
        self._stop_at_ms = None
        self._loop_range = None
        self._player.setPosition(position_ms)
        self._player.play()

    def play_once_range(self, start_ms: int, end_ms: int) -> None:
        self._stop_at_ms = end_ms
        self._loop_range = None
        self._player.setPosition(start_ms)
        self._player.play()

    def play_looping_range(self, start_ms: int, end_ms: int) -> None:
        self._stop_at_ms = None
        self._loop_range = (start_ms, end_ms)
        self._player.setPosition(start_ms)
        self._player.play()

    def stop(self) -> None:
        self._stop_at_ms = None
        self._loop_range = None
        self._stop_without_resetting_position()

    def position(self) -> int:
        return self._player.position()

    def is_playing(self) -> bool:
        return self._player.isPlaying()

    def _stop_without_resetting_position(self) -> None:
        # QMediaPlayer.stop() seeks back to position 0 and emits
        # positionChanged(0); block that so callers' notion of "current
        # position" (e.g. MainWindow.playhead_ms) isn't silently clobbered.
        self._player.blockSignals(True)
        self._player.stop()
        self._player.blockSignals(False)

    def _on_position_changed(self, position: int) -> None:
        self.position_changed.emit(position)
        if self._stop_at_ms is not None and position >= self._stop_at_ms:
            self._stop_without_resetting_position()
            self._stop_at_ms = None
        elif self._loop_range is not None:
            start_ms, end_ms = self._loop_range
            if position >= end_ms:
                self._player.setPosition(start_ms)
