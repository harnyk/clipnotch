import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from clipnotch.ffmpeg_ops import check_ffmpeg_available
from clipnotch.main_window import MainWindow


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)

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
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
