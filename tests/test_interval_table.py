from clipnotch.interval_table import IntervalTable
from clipnotch.marker_model import Interval


def test_refresh_populates_rows(qtbot):
    table = IntervalTable()
    qtbot.addWidget(table)
    intervals = [
        Interval(0, 3000, included=False),
        Interval(3000, 7500, included=True),
    ]

    table.refresh(intervals)

    assert table.rowCount() == 2
    assert table.item(0, 0).text() == "00-00-000"
    assert table.item(0, 1).text() == "00-03-000"
    assert table.item(0, 3).text() == "excluded"
    assert table.item(1, 3).text() == "included"


def test_refresh_clears_previous_rows(qtbot):
    table = IntervalTable()
    qtbot.addWidget(table)
    table.refresh([Interval(0, 1000, included=False)] * 3)
    table.refresh([Interval(0, 1000, included=False)])
    assert table.rowCount() == 1
