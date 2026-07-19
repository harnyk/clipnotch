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
