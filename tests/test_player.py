from unittest.mock import patch
from clipnotch.player import AudioPlayer


def test_load_sets_source(qtbot, test_wav_path):
    player = AudioPlayer()
    qtbot.addWidget  # no-op reference to ensure qtbot fixture is wired; player is a QObject, not a widget
    player.load(test_wav_path)
    assert player._player.source().isLocalFile()


def test_play_once_range_sets_stop_position(qtbot, test_wav_path):
    player = AudioPlayer()
    player.load(test_wav_path)
    with patch.object(player._player, "setPosition") as mock_set_position, \
         patch.object(player._player, "play") as mock_play:
        player.play_once_range(200, 700)
        mock_set_position.assert_called_once_with(200)
        mock_play.assert_called_once()
    assert player._stop_at_ms == 700


def test_position_changed_stops_player_at_target():
    player = AudioPlayer()
    player._stop_at_ms = 700
    with patch.object(player._player, "stop") as mock_stop:
        player._on_position_changed(699)
        mock_stop.assert_not_called()
        player._on_position_changed(700)
        mock_stop.assert_called_once()
    assert player._stop_at_ms is None


def test_play_from_clears_stop_position(qtbot, test_wav_path):
    player = AudioPlayer()
    player.load(test_wav_path)
    player._stop_at_ms = 500
    with patch.object(player._player, "setPosition"), patch.object(player._player, "play"):
        player.play_from(100)
    assert player._stop_at_ms is None


def test_play_looping_range_sets_loop_range_not_stop_at(qtbot, test_wav_path):
    player = AudioPlayer()
    player.load(test_wav_path)
    with patch.object(player._player, "setPosition") as mock_set_position, \
         patch.object(player._player, "play") as mock_play:
        player.play_looping_range(200, 700)
        mock_set_position.assert_called_once_with(200)
        mock_play.assert_called_once()
    assert player._stop_at_ms is None
    assert player._loop_range == (200, 700)


def test_position_changed_seeks_back_to_loop_start_without_stopping():
    player = AudioPlayer()
    player._loop_range = (200, 700)
    with patch.object(player._player, "setPosition") as mock_set_position, \
         patch.object(player._player, "stop") as mock_stop:
        player._on_position_changed(699)
        mock_set_position.assert_not_called()
        player._on_position_changed(700)
        mock_set_position.assert_called_once_with(200)
        mock_stop.assert_not_called()
    # Looping keeps going: the loop range is not cleared after wrapping.
    assert player._loop_range == (200, 700)


def test_play_once_range_clears_loop_range(qtbot, test_wav_path):
    player = AudioPlayer()
    player.load(test_wav_path)
    player._loop_range = (0, 100)
    with patch.object(player._player, "setPosition"), patch.object(player._player, "play"):
        player.play_once_range(200, 700)
    assert player._loop_range is None


def test_stop_clears_loop_range(qtbot, test_wav_path):
    player = AudioPlayer()
    player.load(test_wav_path)
    player._loop_range = (0, 100)
    player.stop()
    assert player._loop_range is None


def test_stop_does_not_emit_position_changed(qtbot, test_wav_path):
    # QMediaPlayer.stop() resets position to 0 and would otherwise emit
    # positionChanged(0); callers (e.g. MainWindow) rely on stop() being
    # silent so their own notion of "current position" isn't clobbered.
    player = AudioPlayer()
    player.load(test_wav_path)
    received = []
    player.position_changed.connect(received.append)
    player.stop()
    assert received == []
