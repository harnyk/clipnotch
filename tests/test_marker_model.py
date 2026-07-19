import pytest
from clipnotch.marker_model import MarkerModel, Interval


def test_new_model_has_no_markers():
    model = MarkerModel(duration_ms=10_000)
    assert model.markers == []


def test_add_marker_adds_sorted():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(5000)
    model.add_marker(2000)
    assert model.markers == [2000, 5000]


def test_add_marker_ignores_duplicate():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(3000)
    model.add_marker(3000)
    assert model.markers == [3000]


def test_add_marker_ignores_out_of_range():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(-1)
    model.add_marker(0)
    model.add_marker(10_000)
    model.add_marker(20_000)
    assert model.markers == []


def test_remove_nearest_marker():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(2000)
    model.add_marker(8000)
    model.remove_nearest_marker(7000)
    assert model.markers == [2000]


def test_remove_nearest_marker_when_empty_is_noop():
    model = MarkerModel(duration_ms=10_000)
    model.remove_nearest_marker(5000)
    assert model.markers == []


def test_intervals_with_no_markers_returns_full_range():
    model = MarkerModel(duration_ms=10_000)
    assert model.intervals() == [Interval(0, 10_000, False)]


def test_intervals_with_markers():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(3000)
    model.add_marker(7000)
    assert model.intervals() == [
        Interval(0, 3000, False),
        Interval(3000, 7000, False),
        Interval(7000, 10_000, False),
    ]


def test_toggle_interval_at_toggles_included():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(5000)
    model.toggle_interval_at(2000)
    intervals = model.intervals()
    assert intervals[0].included is True
    assert intervals[1].included is False
    model.toggle_interval_at(2000)
    assert model.intervals()[0].included is False


def test_interval_containing_boundary_at_duration():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(5000)
    interval = model.interval_containing(10_000)
    assert interval == Interval(5000, 10_000, False)


def test_interval_containing_returns_none_out_of_range():
    model = MarkerModel(duration_ms=10_000)
    assert model.interval_containing(20_000) is None


def test_next_and_prev_marker():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(3000)
    model.add_marker(7000)
    assert model.next_marker(1000) == 3000
    assert model.next_marker(3000) == 7000
    assert model.next_marker(8000) is None
    assert model.prev_marker(8000) == 7000
    assert model.prev_marker(3000) is None


def test_next_and_prev_interval_start_covers_boundary_intervals():
    # Intervals: [0, 3000) [3000, 7000) [7000, 10000) -- three intervals, two markers.
    # Unlike next_marker/prev_marker, this must also reach the very first (start 0)
    # and very last interval, which have no marker exactly at their boundary.
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(3000)
    model.add_marker(7000)

    assert model.next_interval_start(0) == 3000
    assert model.next_interval_start(3000) == 7000
    assert model.next_interval_start(7000) is None
    assert model.next_interval_start(9999) is None

    assert model.prev_interval_start(7000) == 3000
    assert model.prev_interval_start(3000) == 0
    assert model.prev_interval_start(0) is None
    assert model.prev_interval_start(9999) == 3000


def test_next_and_prev_interval_start_with_no_markers():
    model = MarkerModel(duration_ms=10_000)
    assert model.next_interval_start(0) is None
    assert model.prev_interval_start(0) is None


def test_move_marker_shifts_position():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(3000)
    model.move_marker(3000, 10)
    assert model.markers == [3010]
    model.move_marker(3010, -20)
    assert model.markers == [2990]


def test_move_marker_clamps_at_neighboring_markers():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(3000)
    model.add_marker(3005)
    # Moving 3000 rightward can't reach or pass 3005.
    model.move_marker(3000, 100)
    assert model.markers == [3004, 3005]
    # Moving 3005 leftward can't reach or pass 3004.
    model.move_marker(3005, -100)
    assert model.markers == [3004, 3005]


def test_move_marker_clamps_at_track_boundaries():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(5)
    model.move_marker(5, -100)
    assert model.markers == [1]

    model.add_marker(9995)
    model.move_marker(9995, 100)
    assert model.markers == [1, 9999]


def test_move_marker_does_nothing_for_unknown_position():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(3000)
    model.move_marker(4000, 10)
    assert model.markers == [3000]


def test_move_marker_preserves_included_flag_of_the_interval_it_starts():
    model = MarkerModel(duration_ms=10_000)
    model.add_marker(3000)
    model.add_marker(7000)
    model.toggle_interval_at(4000)  # includes the [3000, 7000) interval
    assert model.interval_containing(4000).included is True

    model.move_marker(3000, 10)

    assert model.markers == [3010, 7000]
    assert model.interval_containing(4000).included is True
