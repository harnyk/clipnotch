from pathlib import Path
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

READY_MEDIA_STATUSES = (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia)


class AudioPlayer(QObject):
    position_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._loop_range: tuple[int, int] | None = None
        self._pending_seek_ms: int | None = None
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)

    def load(self, path: Path) -> None:
        self._pending_seek_ms = None
        self._player.setSource(QUrl.fromLocalFile(str(path)))

    def play_from(self, position_ms: int) -> None:
        self._loop_range = None
        self._seek_and_play(position_ms)

    def play_looping(self, position_ms: int, loop_start_ms: int, loop_end_ms: int) -> None:
        # Starts playback at position_ms (which may be anywhere inside the loop
        # range, not necessarily loop_start_ms); once playback reaches loop_end_ms
        # it wraps back to loop_start_ms and keeps playing.
        self._loop_range = (loop_start_ms, loop_end_ms)
        self._seek_and_play(position_ms)

    def stop(self) -> None:
        self._loop_range = None
        self._pending_seek_ms = None
        self._stop_without_resetting_position()

    def position(self) -> int:
        return self._player.position()

    def is_playing(self) -> bool:
        return self._player.isPlaying()

    def _seek_and_play(self, position_ms: int) -> None:
        if self._player.mediaStatus() in READY_MEDIA_STATUSES:
            self._pending_seek_ms = None
            self._player.setPosition(position_ms)
            self._player.play()
        else:
            # QMediaPlayer.setPosition() is silently dropped while media is still
            # loading (mediaStatus other than Loaded/Buffered) — defer the seek
            # until mediaStatusChanged reports it's actually ready, instead of
            # letting play() silently start from position 0.
            self._pending_seek_ms = position_ms

    def _on_media_status_changed(self, status) -> None:
        if self._pending_seek_ms is not None and status in READY_MEDIA_STATUSES:
            position_ms = self._pending_seek_ms
            self._pending_seek_ms = None
            self._player.setPosition(position_ms)
            self._player.play()

    def _stop_without_resetting_position(self) -> None:
        # QMediaPlayer.stop() seeks back to position 0 and emits
        # positionChanged(0); block that so callers' notion of "current
        # position" (e.g. MainWindow.playhead_ms) isn't silently clobbered.
        self._player.blockSignals(True)
        self._player.stop()
        self._player.blockSignals(False)

    def _on_position_changed(self, position: int) -> None:
        self.position_changed.emit(position)
        if self._loop_range is not None:
            loop_start_ms, loop_end_ms = self._loop_range
            if position >= loop_end_ms:
                self._player.setPosition(loop_start_ms)
