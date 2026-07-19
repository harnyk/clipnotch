from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from audioshit.main_window import MainWindow, SMALL_STEP_MS, LARGE_STEP_MS


def _load_window_with_tone(qtbot, test_wav_path):
    window = MainWindow()
    qtbot.addWidget(window)
    window.load_audio_file(test_wav_path)
    return window


def test_load_audio_file_sets_up_marker_model(qtbot, test_wav_path):
    window = _load_window_with_tone(qtbot, test_wav_path)
    assert window.marker_model is not None
    assert window.marker_model.duration_ms > 0


def test_right_arrow_moves_playhead_forward(qtbot, test_wav_path):
    window = _load_window_with_tone(qtbot, test_wav_path)
    start = window.playhead_ms
    QTest.keyClick(window, Qt.Key_Right)
    assert window.playhead_ms == start + SMALL_STEP_MS


def test_shift_right_arrow_moves_playhead_by_large_step(qtbot, test_wav_path):
    window = _load_window_with_tone(qtbot, test_wav_path)
    start = window.playhead_ms
    QTest.keyClick(window, Qt.Key_Right, Qt.ShiftModifier)
    assert window.playhead_ms == start + LARGE_STEP_MS


def test_m_key_adds_marker_at_playhead(qtbot, test_wav_path):
    window = _load_window_with_tone(qtbot, test_wav_path)
    QTest.keyClick(window, Qt.Key_Right)
    QTest.keyClick(window, Qt.Key_M)
    assert window.playhead_ms in window.marker_model.markers


def test_x_key_toggles_current_interval(qtbot, test_wav_path):
    window = _load_window_with_tone(qtbot, test_wav_path)
    QTest.keyClick(window, Qt.Key_X)
    interval = window.marker_model.interval_containing(window.playhead_ms)
    assert interval.included is True
    QTest.keyClick(window, Qt.Key_X)
    interval = window.marker_model.interval_containing(window.playhead_ms)
    assert interval.included is False


def test_tab_jumps_to_next_marker(qtbot, test_wav_path):
    window = _load_window_with_tone(qtbot, test_wav_path)
    window.marker_model.add_marker(300)
    window.marker_model.add_marker(700)
    window.playhead_ms = 0
    QTest.keyClick(window, Qt.Key_Tab)
    assert window.playhead_ms == 300


def test_backspace_removes_nearest_marker(qtbot, test_wav_path):
    window = _load_window_with_tone(qtbot, test_wav_path)
    window.marker_model.add_marker(300)
    window.playhead_ms = 310
    QTest.keyClick(window, Qt.Key_Backspace)
    assert window.marker_model.markers == []


def test_export_button_calls_export_intervals(qtbot, test_wav_path, tmp_path):
    from unittest.mock import patch

    window = _load_window_with_tone(qtbot, test_wav_path)
    window.marker_model.add_marker(300)
    window.marker_model.toggle_interval_at(100)
    window.output_dir = tmp_path

    with patch("audioshit.main_window.export_intervals", return_value=[]) as mock_export, \
         patch("audioshit.main_window.QMessageBox.information"):
        window.export_button.click()

    mock_export.assert_called_once()
