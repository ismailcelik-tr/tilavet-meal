from tilavet.corpus import AyahRef, MealUnit
from tilavet.live import MealPlayer, Skipped, Started
from tilavet.policy import Play

UNITS = [MealUnit(114, a, a, str(a)) for a in range(1, 7)]


def play(t: float, i: int) -> Play:
    return Play(t, UNITS[i], AyahRef(114, i + 1))


def player(duration_s: float) -> MealPlayer:
    return MealPlayer(lambda unit: duration_s, max_wait_s=15)


def test_idle_player_starts_at_once():
    assert player(5).submit(play(1.0, 0)) == [Started(1.0, play(1.0, 0))]


def test_meals_never_overlap():
    p = player(5)
    p.submit(play(1.0, 0))

    assert p.submit(play(2.0, 1)) == []
    assert p.advance(5.9) == []
    assert p.advance(6.0) == [Started(6.0, play(2.0, 1))]


def test_stale_meal_gives_way_to_newer():
    p = player(20)
    p.submit(play(0.0, 0))
    p.submit(play(1.0, 1))
    p.submit(play(2.0, 2))

    assert p.advance(20.0) == [Skipped(20.0, play(1.0, 1)), Started(20.0, play(2.0, 2))]


def test_last_meal_always_plays():
    p = player(20)
    p.submit(play(0.0, 0))
    p.submit(play(1.0, 1))

    assert p.advance(20.0) == [Started(20.0, play(1.0, 1))]
