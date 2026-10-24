"""Meal playback queue: one meal at a time, never cut mid-sentence. Pure; time is passed in."""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

from tilavet.corpus import MealUnit
from tilavet.policy import Play

__all__ = ["MealPlayer", "PlayerEvent", "Skipped", "Started"]


@dataclass(frozen=True)
class Started:
    t: float
    play: Play


@dataclass(frozen=True)
class Skipped:
    t: float
    play: Play


PlayerEvent = Started | Skipped


class MealPlayer:
    def __init__(self, duration_s: Callable[[MealUnit], float], max_wait_s: float) -> None:
        self._duration_s = duration_s
        self._max_wait_s = max_wait_s
        self._queue: deque[Play] = deque()
        self._free_at = float("-inf")

    def submit(self, play: Play) -> list[PlayerEvent]:
        # Settle earlier meals first: whether a newer one exists is judged at their start time.
        events = self.advance(play.t)
        self._queue.append(play)
        return events + self.advance(play.t)

    def advance(self, now: float) -> list[PlayerEvent]:
        events: list[PlayerEvent] = []
        while self._queue:
            play = self._queue[0]
            start = max(self._free_at, play.t)
            if start > now:
                break

            self._queue.popleft()
            if self._queue and start - play.t > self._max_wait_s:
                events.append(Skipped(start, play))
                continue

            events.append(Started(start, play))
            self._free_at = start + self._duration_s(play.unit)
        return events
