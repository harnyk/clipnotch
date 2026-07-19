from pathlib import Path
from unittest.mock import patch, MagicMock
from clipnotch.ytdlp_ops import download_audio


def test_download_audio_returns_downloaded_path(tmp_path):
    fake_info = {"id": "abc123", "ext": "m4a"}
    expected_path = tmp_path / "Some Title.m4a"
    expected_path.touch()

    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value = fake_ydl
    fake_ydl.__exit__.return_value = False
    fake_ydl.extract_info.return_value = fake_info
    fake_ydl.prepare_filename.return_value = str(expected_path)

    with patch("clipnotch.ytdlp_ops.yt_dlp.YoutubeDL", return_value=fake_ydl) as ydl_cls:
        result = download_audio("https://youtube.com/watch?v=abc123", tmp_path)

    assert result == expected_path
    fake_ydl.extract_info.assert_called_once_with(
        "https://youtube.com/watch?v=abc123", download=True
    )
    ydl_cls.assert_called_once()
