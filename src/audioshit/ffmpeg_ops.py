import shutil
import subprocess
from pathlib import Path


def build_convert_to_wav_cmd(input_path: Path, output_path: Path) -> list[str]:
    return ["ffmpeg", "-y", "-i", str(input_path), "-ac", "1", "-ar", "44100", str(output_path)]


def build_export_cmd(input_wav: Path, start_ms: int, end_ms: int, output_path: Path) -> list[str]:
    start_s = start_ms / 1000
    duration_s = (end_ms - start_ms) / 1000
    return [
        "ffmpeg", "-y",
        "-i", str(input_wav),
        "-ss", f"{start_s:.3f}",
        "-t", f"{duration_s:.3f}",
        str(output_path),
    ]


def run_ffmpeg(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({' '.join(cmd)}): {result.stderr}")


def check_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None
