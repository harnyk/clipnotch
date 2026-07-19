from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from clipnotch.main_window import MainWindow, SMALL_STEP_MS, LARGE_STEP_MS


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


def test_l_and_k_navigate_between_intervals(qtbot, test_wav_path):
    window = _load_window_with_tone(qtbot, test_wav_path)
    window.marker_model.add_marker(300)
    window.marker_model.add_marker(700)
    window.playhead_ms = 0

    QTest.keyClick(window, Qt.Key_L)
    assert window.playhead_ms == 300

    QTest.keyClick(window, Qt.Key_L)
    assert window.playhead_ms == 700

    QTest.keyClick(window, Qt.Key_L)
    assert window.playhead_ms == 700  # already the last interval, no-op

    QTest.keyClick(window, Qt.Key_K)
    assert window.playhead_ms == 300

    QTest.keyClick(window, Qt.Key_K)
    assert window.playhead_ms == 0

    QTest.keyClick(window, Qt.Key_K)
    assert window.playhead_ms == 0  # already the first interval, no-op


def test_backspace_removes_nearest_marker(qtbot, test_wav_path):
    window = _load_window_with_tone(qtbot, test_wav_path)
    window.marker_model.add_marker(300)
    window.playhead_ms = 310
    QTest.keyClick(window, Qt.Key_Backspace)
    assert window.marker_model.markers == []


def test_space_stop_returns_playhead_to_navigation_start(qtbot, test_wav_path):
    from unittest.mock import patch

    window = _load_window_with_tone(qtbot, test_wav_path)
    window.playhead_ms = 400

    with patch.object(window.player, "is_playing", return_value=False), \
         patch.object(window.player, "play_from") as mock_play_from:
        QTest.keyClick(window, Qt.Key_Space)

    mock_play_from.assert_called_once_with(400)
    assert window.nav_point_ms == 400

    # Playback advances the playhead (mirrors what position_changed does while playing).
    window.playhead_ms = 950

    with patch.object(window.player, "is_playing", return_value=True), \
         patch.object(window.player, "stop") as mock_stop:
        QTest.keyClick(window, Qt.Key_Space)

    mock_stop.assert_called_once()
    assert window.playhead_ms == 400
    # nav_point_ms is persistent (not cleared): pressing Space again resumes from here.
    assert window.nav_point_ms == 400


def test_s_key_stops_playback_and_pins_nav_point_at_current_playhead(qtbot, test_wav_path):
    from unittest.mock import patch

    window = _load_window_with_tone(qtbot, test_wav_path)
    window.nav_point_ms = 100  # started playing from here...
    window.playhead_ms = 650  # ...but playback has since moved on

    with patch.object(window.player, "is_playing", return_value=True), \
         patch.object(window.player, "stop") as mock_stop:
        QTest.keyClick(window, Qt.Key_S)

    mock_stop.assert_called_once()
    # "Stop here": nav point moves to wherever playback currently was, not back to
    # where it started, and the playhead itself is left where it is (not rewound).
    assert window.nav_point_ms == 650
    assert window.playhead_ms == 650


def test_s_key_pins_nav_point_even_when_not_playing(qtbot, test_wav_path):
    from unittest.mock import patch

    window = _load_window_with_tone(qtbot, test_wav_path)
    window.playhead_ms = 200

    with patch.object(window.player, "is_playing", return_value=False), \
         patch.object(window.player, "stop") as mock_stop:
        QTest.keyClick(window, Qt.Key_S)

    mock_stop.assert_not_called()
    assert window.nav_point_ms == 200


def test_ctrl_s_still_exports_instead_of_pinning_nav_point(qtbot, test_wav_path, tmp_path):
    from unittest.mock import patch

    window = _load_window_with_tone(qtbot, test_wav_path)
    window.marker_model.add_marker(300)
    window.marker_model.toggle_interval_at(100)
    window.output_dir = tmp_path
    window.nav_point_ms = 0
    window.playhead_ms = 500

    with patch("clipnotch.main_window.export_intervals", return_value=[]) as mock_export, \
         patch("clipnotch.main_window.QMessageBox.information"):
        QTest.keyClick(window, Qt.Key_S, Qt.ControlModifier)

    mock_export.assert_called_once()
    assert window.nav_point_ms == 0


def test_waveform_view_never_takes_keyboard_focus(qtbot, test_wav_path):
    # Regression test: WaveformView briefly had Qt.ClickFocus so it could take
    # keyboard focus on click. That broke every shortcut, because Qt's Tab/arrow-key
    # handling then applied to WaveformView (and its QScrollArea ancestor) instead of
    # reaching MainWindow.keyPressEvent/event() — the sole place shortcuts are wired.
    window = _load_window_with_tone(qtbot, test_wav_path)
    assert window.waveform_view.focusPolicy() == Qt.NoFocus


def test_clicking_waveform_returns_keyboard_focus_to_main_window(qtbot, test_wav_path):
    from unittest.mock import patch

    window = _load_window_with_tone(qtbot, test_wav_path)
    with patch.object(window, "setFocus") as mock_set_focus:
        window.waveform_view.position_clicked.emit(250)

    mock_set_focus.assert_called_once()
    assert window.playhead_ms == 250


def test_load_audio_file_returns_keyboard_focus_to_main_window(qtbot, test_wav_path):
    from unittest.mock import patch

    window = MainWindow()
    qtbot.addWidget(window)
    with patch.object(window, "setFocus") as mock_set_focus:
        window.load_audio_file(test_wav_path)

    mock_set_focus.assert_called_once()


def test_export_button_calls_export_intervals(qtbot, test_wav_path, tmp_path):
    from unittest.mock import patch

    window = _load_window_with_tone(qtbot, test_wav_path)
    window.marker_model.add_marker(300)
    window.marker_model.toggle_interval_at(100)
    window.output_dir = tmp_path

    with patch("clipnotch.main_window.export_intervals", return_value=[]) as mock_export, \
         patch("clipnotch.main_window.QMessageBox.information"):
        window.export_button.click()

    mock_export.assert_called_once()
