from unittest.mock import patch
from audioshit.player import AudioPlayer


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
