import wave
from pathlib import Path
from audioshit.export import format_timecode, build_export_filename, export_intervals
from audioshit.marker_model import Interval


def test_format_timecode():
    assert format_timecode(12450) == "00-12-450"
    assert format_timecode(75000) == "01-15-000"


def test_build_export_filename():
    name = build_export_filename("lecture", 12450, 14200, "wav")
    assert name == "lecture_00-12-450_00-14-200.wav"


def test_export_intervals_writes_only_included_files(tmp_path, test_wav_path):
    intervals = [
        Interval(0, 300, included=False),
        Interval(300, 700, included=True),
        Interval(700, 1000, included=False),
    ]
    output_dir = tmp_path / "out"

    result = export_intervals(test_wav_path, "test_tone", intervals, output_dir, "wav")

    assert len(result) == 1
    expected_name = "test_tone_00-00-300_00-00-700.wav"
    assert result[0].name == expected_name
    assert result[0].exists()

    with wave.open(str(result[0]), "rb") as wf:
        duration_s = wf.getnframes() / wf.getframerate()
    assert 0.35 <= duration_s <= 0.45
