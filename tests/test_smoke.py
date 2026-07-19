from unittest.mock import patch


def test_package_imports():
    import clipnotch  # noqa: F401


def test_main_returns_error_code_when_ffmpeg_missing(qtbot):
    from clipnotch.main import main

    with patch("clipnotch.main.check_ffmpeg_available", return_value=False), \
         patch("clipnotch.main.QMessageBox.critical"):
        exit_code = main()

    assert exit_code == 1
