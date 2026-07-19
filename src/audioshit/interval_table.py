from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
from audioshit.marker_model import Interval
from audioshit.export import format_timecode


class IntervalTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Start", "End", "Duration (ms)", "Status"])

    def refresh(self, intervals: list[Interval]) -> None:
        self.setRowCount(len(intervals))
        for row, interval in enumerate(intervals):
            self.setItem(row, 0, QTableWidgetItem(format_timecode(interval.start_ms)))
            self.setItem(row, 1, QTableWidgetItem(format_timecode(interval.end_ms)))
            duration = interval.end_ms - interval.start_ms
            self.setItem(row, 2, QTableWidgetItem(str(duration)))
            status = "included" if interval.included else "excluded"
            self.setItem(row, 3, QTableWidgetItem(status))
