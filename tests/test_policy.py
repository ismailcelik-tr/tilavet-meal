from tilavet.corpus import AyahRef, MealUnit
from tilavet.engine import AyahConfirmed, Lost, Mode
from tilavet.policy import EmissionPolicy, Play

UNITS = [MealUnit(114, 1, 1, "a"), MealUnit(114, 4, 6, "b")]


def confirm(t: float, aya: int) -> AyahConfirmed:
    return AyahConfirmed(t, AyahRef(114, aya), Mode.TRACK, score=6)


def test_plays_unit_of_confirmed_ayah():
    policy = EmissionPolicy(UNITS, cooldown_s=300)

    assert policy.on(confirm(1.0, 1)) == Play(1.0, UNITS[0], AyahRef(114, 1))


def test_mid_unit_entry_plays_whole_unit_once():
    policy = EmissionPolicy(UNITS, cooldown_s=300)

    assert policy.on(confirm(1.0, 5)) == Play(1.0, UNITS[1], AyahRef(114, 5))
    assert policy.on(confirm(4.0, 6)) is None


def test_cooldown_suppresses_replay():
    policy = EmissionPolicy(UNITS, cooldown_s=300)
    policy.on(confirm(1.0, 1))

    assert policy.on(confirm(200.0, 1)) is None
    assert policy.on(confirm(302.0, 1)) == Play(302.0, UNITS[0], AyahRef(114, 1))


def test_lost_plays_nothing():
    assert EmissionPolicy(UNITS, cooldown_s=300).on(Lost(1.0)) is None
