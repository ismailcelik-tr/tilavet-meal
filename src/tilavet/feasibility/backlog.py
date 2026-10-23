"""Does sequential meal playback fall behind the live recitation?"""

from collections.abc import Sequence
from dataclasses import dataclass

__all__ = ["Unit", "simulate_backlog"]


@dataclass(frozen=True)
class Unit:
    available_s: float  # when the meal may start (unit identified)
    meal_s: float  # meal audio duration at 1.0x


def simulate_backlog(units: Sequence[Unit], speed: float) -> list[float]:
    """Play meals back to back in order; return each unit's start lag in seconds."""
    if speed <= 0:
        raise ValueError("speed must be positive")

    lags: list[float] = []
    player_free_at = float("-inf")

    for unit in units:
        start = max(unit.available_s, player_free_at)
        lags.append(start - unit.available_s)
        player_free_at = start + unit.meal_s / speed

    return lags
