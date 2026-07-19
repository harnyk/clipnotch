from unittest.mock import patch


def test_package_imports():
    import audioshit  # noqa: F401


def test_main_returns_error_code_when_ffmpeg_missing(qtbot):
    from audioshit.main import main

    with patch("audioshit.main.check_ffmpeg_available", return_value=False), \
         patch("audioshit.main.QMessageBox.critical"):
        exit_code = main()

    assert exit_code == 1
