from pathlib import Path
from unittest.mock import patch
from audioshit.download_worker import DownloadWorker


def test_worker_emits_finished_with_wav_path(qtbot, tmp_path):
    downloaded = tmp_path / "video.m4a"
    downloaded.touch()
    expected_wav = downloaded.with_suffix(".wav")

    def fake_run_ffmpeg(cmd):
        Path(cmd[-1]).touch()

    with patch("audioshit.download_worker.download_audio", return_value=downloaded), \
         patch("audioshit.download_worker.run_ffmpeg", side_effect=fake_run_ffmpeg):
        worker = DownloadWorker("https://youtube.com/watch?v=abc", tmp_path)
        with qtbot.waitSignal(worker.converted, timeout=5000) as blocker:
            worker.start()

    assert blocker.args[0] == expected_wav


def test_worker_emits_failed_on_exception(qtbot, tmp_path):
    with patch("audioshit.download_worker.download_audio", side_effect=RuntimeError("network down")):
        worker = DownloadWorker("https://youtube.com/watch?v=abc", tmp_path)
        with qtbot.waitSignal(worker.failed, timeout=5000) as blocker:
            worker.start()

    assert "network down" in blocker.args[0]
