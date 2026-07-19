from dataclasses import dataclass


@dataclass(frozen=True)
class Interval:
    start_ms: int
    end_ms: int
    included: bool = False


class MarkerModel:
    def __init__(self, duration_ms: int):
        self.duration_ms = duration_ms
        self._markers: list[int] = []
        self._included_starts: set[int] = set()

    def add_marker(self, position_ms: int) -> None:
        if position_ms <= 0 or position_ms >= self.duration_ms:
            return
        if position_ms in self._markers:
            return
        self._markers.append(position_ms)
        self._markers.sort()

    def remove_nearest_marker(self, position_ms: int) -> None:
        if not self._markers:
            return
        nearest = min(self._markers, key=lambda m: abs(m - position_ms))
        self._markers.remove(nearest)

    @property
    def markers(self) -> list[int]:
        return list(self._markers)

    def intervals(self) -> list[Interval]:
        bounds = [0, *self._markers, self.duration_ms]
        return [
            Interval(start, end, start in self._included_starts)
            for start, end in zip(bounds, bounds[1:])
        ]

    def toggle_interval_at(self, position_ms: int) -> None:
        interval = self.interval_containing(position_ms)
        if interval is None:
            return
        if interval.start_ms in self._included_starts:
            self._included_starts.discard(interval.start_ms)
        else:
            self._included_starts.add(interval.start_ms)

    def interval_containing(self, position_ms: int) -> Interval | None:
        for interval in self.intervals():
            if interval.start_ms <= position_ms < interval.end_ms:
                return interval
        if position_ms == self.duration_ms:
            return self.intervals()[-1]
        return None

    def next_marker(self, position_ms: int) -> int | None:
        candidates = [m for m in self._markers if m > position_ms]
        return min(candidates) if candidates else None

    def prev_marker(self, position_ms: int) -> int | None:
        candidates = [m for m in self._markers if m < position_ms]
        return max(candidates) if candidates else None

    def _interval_index_containing(self, position_ms: int) -> int | None:
        intervals = self.intervals()
        for i, interval in enumerate(intervals):
            if interval.start_ms <= position_ms < interval.end_ms:
                return i
        if position_ms == self.duration_ms and intervals:
            return len(intervals) - 1
        return None

    def next_interval_start(self, position_ms: int) -> int | None:
        intervals = self.intervals()
        idx = self._interval_index_containing(position_ms)
        if idx is None or idx + 1 >= len(intervals):
            return None
        return intervals[idx + 1].start_ms

    def prev_interval_start(self, position_ms: int) -> int | None:
        intervals = self.intervals()
        idx = self._interval_index_containing(position_ms)
        if idx is None or idx <= 0:
            return None
        return intervals[idx - 1].start_ms
