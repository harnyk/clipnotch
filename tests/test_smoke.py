from unittest.mock import patch, MagicMock


def test_package_imports():
    import clipnotch  # noqa: F401


def test_main_returns_error_code_when_ffmpeg_missing(qtbot, monkeypatch):
    import sys
    from clipnotch.main import main

    monkeypatch.setattr(sys, "argv", ["clipnotch"])

    with patch("clipnotch.main.check_ffmpeg_available", return_value=False), \
         patch("clipnotch.main.QMessageBox.critical"):
        exit_code = main()

    assert exit_code == 1


def test_parse_args_returns_url_when_provided():
    from clipnotch.main import parse_args

    args = parse_args(["https://youtu.be/xyz"])
    assert args.url == "https://youtu.be/xyz"


def test_parse_args_url_defaults_to_none():
    from clipnotch.main import parse_args

    args = parse_args([])
    assert args.url is None


def test_main_starts_download_when_url_given_on_command_line(monkeypatch):
    import sys
    from clipnotch import main as main_module

    monkeypatch.setattr(sys, "argv", ["clipnotch", "https://youtu.be/xyz"])
    mock_window = MagicMock()

    with patch("clipnotch.main.QApplication") as mock_qapp_cls, \
         patch("clipnotch.main.check_ffmpeg_available", return_value=True), \
         patch("clipnotch.main.MainWindow", return_value=mock_window):
        mock_qapp_cls.instance.return_value = None
        mock_app = MagicMock()
        mock_qapp_cls.return_value = mock_app
        mock_app.exec.return_value = 0

        exit_code = main_module.main()

    mock_window.start_download.assert_called_once_with("https://youtu.be/xyz")
    assert exit_code == 0
