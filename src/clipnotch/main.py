import argparse
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from clipnotch.ffmpeg_ops import check_ffmpeg_available
from clipnotch.main_window import MainWindow


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="clipnotch")
    parser.add_argument("url", nargs="?", default=None, help="YouTube URL to load immediately on startup")
    return parser.parse_args(argv)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    args = parse_args(sys.argv[1:])

    if not check_ffmpeg_available():
        QMessageBox.critical(
            None,
            "ffmpeg not found",
            "ffmpeg was not found on your PATH. Install ffmpeg and restart clipnotch.",
        )
        return 1

    window = MainWindow()
    window.resize(1000, 500)
    window.show()

    if args.url:
        window.start_download(args.url)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
