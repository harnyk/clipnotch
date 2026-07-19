from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from audioshit.ffmpeg_ops import (
    build_convert_to_wav_cmd,
    build_export_cmd,
    run_ffmpeg,
    check_ffmpeg_available,
)


def test_build_convert_to_wav_cmd():
    cmd = build_convert_to_wav_cmd(Path("in.m4a"), Path("out.wav"))
    assert cmd == ["ffmpeg", "-y", "-i", "in.m4a", "-ac", "1", "-ar", "44100", "out.wav"]


def test_build_export_cmd():
    cmd = build_export_cmd(Path("track.wav"), 1250, 4000, Path("out.wav"))
    assert cmd == [
        "ffmpeg", "-y",
        "-i", "track.wav",
        "-ss", "1.250",
        "-t", "2.750",
        "out.wav",
    ]


def test_run_ffmpeg_raises_on_failure():
    fake_result = MagicMock(returncode=1, stderr="boom")
    with patch("audioshit.ffmpeg_ops.subprocess.run", return_value=fake_result):
        with pytest.raises(RuntimeError, match="boom"):
            run_ffmpeg(["ffmpeg", "-bad"])


def test_run_ffmpeg_succeeds_silently():
    fake_result = MagicMock(returncode=0, stderr="")
    with patch("audioshit.ffmpeg_ops.subprocess.run", return_value=fake_result):
        run_ffmpeg(["ffmpeg", "-version"])


def test_check_ffmpeg_available_true_when_found():
    with patch("audioshit.ffmpeg_ops.shutil.which", return_value="/usr/bin/ffmpeg"):
        assert check_ffmpeg_available() is True


def test_check_ffmpeg_available_false_when_missing():
    with patch("audioshit.ffmpeg_ops.shutil.which", return_value=None):
        assert check_ffmpeg_available() is False
