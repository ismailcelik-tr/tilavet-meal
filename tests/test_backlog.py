import pytest

from tilavet.feasibility import Unit, simulate_backlog


def test_no_lag_when_meal_fits_recitation():
    units = [Unit(available_s=5, meal_s=3), Unit(available_s=10, meal_s=4)]

    assert simulate_backlog(units, speed=1.0) == [0, 0]


def test_lag_accumulates_when_meal_is_longer():
    units = [Unit(available_s=0, meal_s=6), Unit(available_s=4, meal_s=6), Unit(available_s=8, meal_s=1)]

    assert simulate_backlog(units, speed=1.0) == [0, 2, 4]


def test_speed_shortens_playback():
    units = [Unit(available_s=0, meal_s=6), Unit(available_s=4, meal_s=6)]

    assert simulate_backlog(units, speed=1.5) == [0, 0]


def test_rejects_non_positive_speed():
    with pytest.raises(ValueError):
        simulate_backlog([], speed=0)
