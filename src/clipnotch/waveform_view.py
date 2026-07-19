import numpy as np
from PySide6.QtCore import Signal, QSize
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget

from clipnotch.marker_model import Interval

BASE_PX_PER_SEC = 100
INCLUDED_COLOR = QColor(60, 160, 60)
EXCLUDED_COLOR = QColor(120, 120, 120)
MARKER_COLOR = QColor(220, 50, 50)
PLAYHEAD_COLOR = QColor(240, 240, 30)


def ms_to_x(position_ms: int, duration_ms: int, width_px: int) -> int:
    if duration_ms <= 0:
        return 0
    return int(position_ms / duration_ms * width_px)


def x_to_ms(x_px: int, duration_ms: int, width_px: int) -> int:
    if width_px <= 0:
        return 0
    return int(x_px / width_px * duration_ms)


class WaveformView(QWidget):
    position_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._peaks: np.ndarray = np.zeros((0, 2), dtype=np.int16)
        self._duration_ms = 0
        self._markers: list[int] = []
        self._intervals: list[Interval] = []
        self._playhead_ms = 0
        self._zoom = 1.0
        self.setMinimumHeight(120)
        # Deliberately NoFocus (the default): MainWindow is the sole keyboard-shortcut
        # owner. If this widget took focus itself, Qt's Tab/arrow-key handling would
        # apply to it (and to its QScrollArea ancestor) instead of reaching
        # MainWindow.keyPressEvent/event(), silently breaking every shortcut.

    def set_data(self, peaks: np.ndarray, duration_ms: int) -> None:
        self._peaks = peaks
        self._duration_ms = duration_ms
        self._apply_zoom_width()
        self.update()

    def set_markers(self, markers: list[int]) -> None:
        self._markers = markers
        self.update()

    def set_intervals(self, intervals: list[Interval]) -> None:
        self._intervals = intervals
        self.update()

    def set_playhead(self, position_ms: int) -> None:
        self._playhead_ms = position_ms
        self.update()

    def set_zoom(self, factor: float) -> None:
        self._zoom = factor
        self._apply_zoom_width()
        self.update()

    def _apply_zoom_width(self) -> None:
        width = int(self._duration_ms / 1000 * BASE_PX_PER_SEC * self._zoom)
        self.setMinimumWidth(max(width, 1))

    def sizeHint(self) -> QSize:
        return QSize(self.minimumWidth(), self.minimumHeight())

    def mousePressEvent(self, event) -> None:
        ms = x_to_ms(event.position().x(), self._duration_ms, self.width())
        self.position_clicked.emit(ms)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        width = self.width()
        height = self.height()
        mid_y = height // 2

        for interval in self._intervals:
            x_start = ms_to_x(interval.start_ms, self._duration_ms, width)
            x_end = ms_to_x(interval.end_ms, self._duration_ms, width)
            color = INCLUDED_COLOR if interval.included else EXCLUDED_COLOR
            painter.fillRect(x_start, 0, max(x_end - x_start, 1), height, color.lighter(300))

        if len(self._peaks) > 0:
            painter.setPen(QPen(QColor(20, 20, 20)))
            n_buckets = len(self._peaks)
            for i, (lo, hi) in enumerate(self._peaks):
                x = int(i / n_buckets * width)
                y1 = mid_y - int(hi / 32768 * mid_y)
                y2 = mid_y - int(lo / 32768 * mid_y)
                painter.drawLine(x, y1, x, y2)

        painter.setPen(QPen(MARKER_COLOR, 2))
        for marker_ms in self._markers:
            x = ms_to_x(marker_ms, self._duration_ms, width)
            painter.drawLine(x, 0, x, height)

        painter.setPen(QPen(PLAYHEAD_COLOR, 2))
        x = ms_to_x(self._playhead_ms, self._duration_ms, width)
        painter.drawLine(x, 0, x, height)
