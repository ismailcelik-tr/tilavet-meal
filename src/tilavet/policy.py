"""Which meal unit to play, and when. Early policy: on first confirmed ayah of a unit."""

from collections.abc import Sequence
from dataclasses import dataclass

from tilavet.corpus import AyahRef, MealUnit
from tilavet.engine import AyahConfirmed, Event

__all__ = ["EmissionPolicy", "Play"]


@dataclass(frozen=True)
class Play:
    t: float
    unit: MealUnit
    trigger: AyahRef


class EmissionPolicy:
    def __init__(self, units: Sequence[MealUnit], cooldown_s: float) -> None:
        self._unit_of = {ref: unit for unit in units for ref in unit.refs}
        self._cooldown_s = cooldown_s
        self._played_at: dict[MealUnit, float] = {}

    def on(self, event: Event) -> Play | None:
        if not isinstance(event, AyahConfirmed):
            return None

        unit = self._unit_of[event.ref]
        played_at = self._played_at.get(unit)
        # Reciters repeat passages; replaying the same meal right away only adds backlog.
        if played_at is not None and event.t - played_at < self._cooldown_s:
            return None

        self._played_at[unit] = event.t
        return Play(event.t, unit, event.ref)
