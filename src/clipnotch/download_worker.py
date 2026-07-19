from pathlib import Path
from PySide6.QtCore import QThread, Signal
from clipnotch.ytdlp_ops import download_audio
from clipnotch.ffmpeg_ops import build_convert_to_wav_cmd, run_ffmpeg


class DownloadWorker(QThread):
    converted = Signal(Path)
    failed = Signal(str)

    def __init__(self, url: str, dest_dir: Path, parent=None):
        super().__init__(parent)
        self._url = url
        self._dest_dir = dest_dir

    def run(self) -> None:
        try:
            downloaded_path = download_audio(self._url, self._dest_dir)
            wav_path = downloaded_path.with_suffix(".wav")
            run_ffmpeg(build_convert_to_wav_cmd(downloaded_path, wav_path))
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            self.failed.emit(str(exc))
            return
        self.converted.emit(wav_path)
