import numpy as np
import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from clipnotch.waveform_view import WaveformView, ms_to_x, x_to_ms


def test_ms_to_x_and_back():
    assert ms_to_x(5000, 10_000, 200) == 100
    assert x_to_ms(100, 10_000, 200) == 5000


def test_ms_to_x_zero_duration_returns_zero():
    assert ms_to_x(100, 0, 200) == 0


def test_x_to_ms_zero_width_returns_zero():
    assert x_to_ms(100, 10_000, 0) == 0


def test_set_data_stores_duration(qtbot):
    view = WaveformView()
    qtbot.addWidget(view)
    peaks = np.zeros((50, 2), dtype=np.int16)
    view.set_data(peaks, duration_ms=10_000)
    assert view._duration_ms == 10_000
    assert view._peaks.shape == (50, 2)


def test_click_emits_position_clicked(qtbot):
    view = WaveformView()
    qtbot.addWidget(view)
    view.resize(200, 100)
    view.set_data(np.zeros((50, 2), dtype=np.int16), duration_ms=1_000)

    with qtbot.waitSignal(view.position_clicked, timeout=1000) as blocker:
        QTest.mouseClick(view, Qt.LeftButton, pos=QPoint(100, 50))

    assert blocker.args[0] == pytest.approx(500, abs=100)


def test_set_zoom_changes_min_width(qtbot):
    view = WaveformView()
    qtbot.addWidget(view)
    view.set_data(np.zeros((50, 2), dtype=np.int16), duration_ms=10_000)
    width_at_1x = view.minimumWidth()
    view.set_zoom(2.0)
    assert view.minimumWidth() == width_at_1x * 2


def test_set_nav_point_stores_position(qtbot):
    view = WaveformView()
    qtbot.addWidget(view)
    view.set_data(np.zeros((50, 2), dtype=np.int16), duration_ms=10_000)
    view.set_nav_point(2500)
    assert view._nav_point_ms == 2500
