import hashlib
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from clipnotch.ytdlp_ops import download_audio
from clipnotch.ffmpeg_ops import build_convert_to_wav_cmd, run_ffmpeg


def url_cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


class DownloadWorker(QThread):
    converted = Signal(Path, str)
    failed = Signal(str)

    def __init__(self, url: str, dest_dir: Path, parent=None):
        super().__init__(parent)
        self._url = url
        self._dest_dir = dest_dir

    def run(self) -> None:
        self._dest_dir.mkdir(parents=True, exist_ok=True)
        cache_key = url_cache_key(self._url)
        wav_path = self._dest_dir / f"{cache_key}.wav"
        name_path = self._dest_dir / f"{cache_key}.name"

        if wav_path.exists() and name_path.exists():
            self.converted.emit(wav_path, name_path.read_text(encoding="utf-8").strip())
            return

        try:
            downloaded_path = download_audio(self._url, self._dest_dir)
            run_ffmpeg(build_convert_to_wav_cmd(downloaded_path, wav_path))
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            self.failed.emit(str(exc))
            return

        source_name = downloaded_path.stem
        name_path.write_text(source_name, encoding="utf-8")
        self.converted.emit(wav_path, source_name)
