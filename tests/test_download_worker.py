from pathlib import Path
from unittest.mock import patch
from clipnotch.download_worker import DownloadWorker, url_cache_key


def test_url_cache_key_is_deterministic_and_url_specific():
    key_a = url_cache_key("https://youtube.com/watch?v=abc")
    key_b = url_cache_key("https://youtube.com/watch?v=abc")
    key_c = url_cache_key("https://youtube.com/watch?v=xyz")
    assert key_a == key_b
    assert key_a != key_c


def test_worker_emits_wav_path_and_source_name_on_cache_miss(qtbot, tmp_path):
    downloaded = tmp_path / "Some Video Title.m4a"
    downloaded.touch()

    def fake_run_ffmpeg(cmd):
        Path(cmd[-1]).touch()

    url = "https://youtube.com/watch?v=abc"
    expected_wav = tmp_path / f"{url_cache_key(url)}.wav"

    with patch("clipnotch.download_worker.download_audio", return_value=downloaded), \
         patch("clipnotch.download_worker.run_ffmpeg", side_effect=fake_run_ffmpeg):
        worker = DownloadWorker(url, tmp_path)
        with qtbot.waitSignal(worker.converted, timeout=5000) as blocker:
            worker.start()

    assert blocker.args[0] == expected_wav
    assert blocker.args[1] == "Some Video Title"
    assert (tmp_path / f"{url_cache_key(url)}.name").read_text(encoding="utf-8") == "Some Video Title"


def test_worker_skips_download_on_cache_hit(qtbot, tmp_path):
    url = "https://youtube.com/watch?v=abc"
    cache_key = url_cache_key(url)
    cached_wav = tmp_path / f"{cache_key}.wav"
    cached_wav.touch()
    (tmp_path / f"{cache_key}.name").write_text("Cached Title", encoding="utf-8")

    with patch("clipnotch.download_worker.download_audio") as mock_download, \
         patch("clipnotch.download_worker.run_ffmpeg") as mock_run_ffmpeg:
        worker = DownloadWorker(url, tmp_path)
        with qtbot.waitSignal(worker.converted, timeout=5000) as blocker:
            worker.start()

    mock_download.assert_not_called()
    mock_run_ffmpeg.assert_not_called()
    assert blocker.args[0] == cached_wav
    assert blocker.args[1] == "Cached Title"


def test_worker_emits_failed_on_exception(qtbot, tmp_path):
    with patch("clipnotch.download_worker.download_audio", side_effect=RuntimeError("network down")):
        worker = DownloadWorker("https://youtube.com/watch?v=abc", tmp_path)
        with qtbot.waitSignal(worker.failed, timeout=5000) as blocker:
            worker.start()

    assert "network down" in blocker.args[0]
