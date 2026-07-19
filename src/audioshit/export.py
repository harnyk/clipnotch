from pathlib import Path
from audioshit.marker_model import Interval
from audioshit.ffmpeg_ops import build_export_cmd, run_ffmpeg


def format_timecode(ms: int) -> str:
    total_seconds, millis = divmod(ms, 1000)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}-{seconds:02d}-{millis:03d}"


def build_export_filename(source_name: str, start_ms: int, end_ms: int, ext: str) -> str:
    return f"{source_name}_{format_timecode(start_ms)}_{format_timecode(end_ms)}.{ext}"


def export_intervals(
    wav_path: Path,
    source_name: str,
    intervals: list[Interval],
    output_dir: Path,
    ext: str,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    exported: list[Path] = []
    for interval in intervals:
        if not interval.included:
            continue
        filename = build_export_filename(source_name, interval.start_ms, interval.end_ms, ext)
        output_path = output_dir / filename
        cmd = build_export_cmd(wav_path, interval.start_ms, interval.end_ms, output_path)
        run_ffmpeg(cmd)
        exported.append(output_path)
    return exported
