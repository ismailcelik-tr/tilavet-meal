import hashlib
from dataclasses import replace

import pytest

from tilavet.corpus import AyahRef
from tilavet.engine import AyahConfirmed, EngineConfig, Lost, Mode, PositionEngine, QuranIndex


def token(*parts: object) -> str:
    """Dissimilar words, so fuzzy matching only hits on purpose."""
    return hashlib.md5("-".join(map(str, parts)).encode()).hexdigest()[:8]


# Sura 1: six 3-word ayahs with unique words. Sura 2 repeats ayah 1:3 verbatim.
# Sura 3 has a refrain (ayahs 2, 4, 6), like Ar-Rahman.
SURA_1 = {AyahRef(1, a): [token(1, a, w) for w in range(3)] for a in range(1, 7)}
SURA_2 = {
    AyahRef(2, 1): ["x1", "x2", "x3"],
    AyahRef(2, 2): list(SURA_1[AyahRef(1, 3)]),
    AyahRef(2, 3): ["y1", "y2", "y3"],
    AyahRef(2, 4): ["z1"],
    AyahRef(2, 5): ["q1", "q2", "q3"],
}
REFRAIN = [token("r", w) for w in range(3)]
SURA_3 = {AyahRef(3, a): REFRAIN if a % 2 == 0 else [token(3, a, w) for w in range(3)] for a in range(1, 8)}
# Sura 4: ayah 3 ends with the same words as ayah 1.
A, B, C = token(4, "a"), token(4, "b"), token(4, "c")
SURA_4 = {
    AyahRef(4, 1): [A, B, C],
    AyahRef(4, 2): [token(4, "d"), token(4, "e"), token(4, "f")],
    AyahRef(4, 3): [token(4, "g"), token(4, "h"), B, C],
}
# Sura 5: ayahs 3 and 4 share their first two words (like 72:21-22, "qul inni").
P, Q = token(5, "p"), token(5, "q")
SURA_5 = {
    AyahRef(5, 1): [token(5, "k", w) for w in range(3)],
    AyahRef(5, 2): [P, token(5, "x"), token(5, "y")],
    AyahRef(5, 3): [P, Q, token(5, "z1")],
    AyahRef(5, 4): [P, Q, token(5, "z2")],
}
# Sura 6: ayahs 2 and 4 differ only by a letter in the first word (like 37:174 / 37:178).
F, W = "fatoolxx", "watoolxx"
TAIL = [token(6, "n"), token(6, "h"), token(6, "j")]
SURA_6 = {
    AyahRef(6, 1): [token(6, "u", w) for w in range(3)],
    AyahRef(6, 2): [F, *TAIL],
    AyahRef(6, 3): [token(6, "g", w) for w in range(3)],
    AyahRef(6, 4): [W, *TAIL],
    AyahRef(6, 5): [token(6, "v", w) for w in range(3)],
}
ALL = {**SURA_1, **SURA_2, **SURA_3, **SURA_4, **SURA_5, **SURA_6}
CONFIG = EngineConfig(acquire_min_matched=3, acquire_min_score=5, acquire_margin=3, acquire_min_votes=2)


def words(*refs: tuple[int, int], take: int | None = None) -> list[str]:
    result = [w for sura, aya in refs for w in ALL[AyahRef(sura, aya)]]
    return result if take is None else result[:take]


@pytest.fixture
def engine() -> PositionEngine:
    return PositionEngine(QuranIndex.build(ALL), CONFIG)


def confirmed(events) -> list[AyahRef]:
    return [e.ref for e in events if isinstance(e, AyahConfirmed)]


def test_acquire_commits_on_unique_passage(engine):
    events = engine.feed(1.0, words((1, 1), (1, 2)))

    assert confirmed(events) == [AyahRef(1, 1), AyahRef(1, 2)]
    assert engine.mode is Mode.TRACK


def test_acquire_backfill_is_capped():
    engine = PositionEngine(QuranIndex.build(ALL), replace(CONFIG, acquire_backfill=1))

    assert confirmed(engine.feed(1.0, words((1, 1), (1, 2), (1, 3)))) == [AyahRef(1, 2), AyahRef(1, 3)]


def test_acquire_without_backfill_confirms_last_ayah_only():
    engine = PositionEngine(QuranIndex.build(ALL), replace(CONFIG, acquire_backfill=0))

    assert confirmed(engine.feed(1.0, words((1, 1), (1, 2)))) == [AyahRef(1, 2)]


def test_backfill_skips_an_ayah_that_was_not_heard(engine):
    # The match bridges the skipped one-word ayah 2:4 (muhammad-ayyoub-8 skipped 74:5 this way).
    assert confirmed(engine.feed(1.0, words((2, 3), (2, 5)))) == [AyahRef(2, 3), AyahRef(2, 5)]


def test_backfill_skips_an_ayah_that_ended_too_long_ago():
    engine = PositionEngine(QuranIndex.build(ALL), replace(CONFIG, acquire_backfill_age_s=1.0))

    assert confirmed(engine.feed(1.0, words((1, 1), (1, 2)))) == [AyahRef(1, 2)]


def test_backfilled_ayahs_are_not_reconfirmed(engine):
    engine.feed(1.0, words((1, 1), (1, 2)))

    assert confirmed(engine.feed(2.0, words((1, 1), (1, 2), (1, 3)))) == [AyahRef(1, 3)]


def test_acquire_waits_while_passage_is_ambiguous(engine):
    assert engine.feed(1.0, words((1, 3))) == []
    assert engine.mode is Mode.ACQUIRE

    events = engine.feed(2.0, words((1, 3), (1, 4)))

    assert confirmed(events) == [AyahRef(1, 3), AyahRef(1, 4)]


def test_track_confirms_next_ayah_after_two_words(engine):
    engine.feed(1.0, words((1, 1), (1, 2)))

    assert confirmed(engine.feed(2.0, words((1, 2)) + words((1, 3), take=1))) == []
    assert confirmed(engine.feed(3.0, words((1, 2)) + words((1, 3), take=2))) == [AyahRef(1, 3)]


def test_track_confirms_one_word_ayah(engine):
    engine.feed(1.0, words((2, 1), (2, 2), (2, 3)))

    assert confirmed(engine.feed(2.0, words((2, 3), (2, 4)))) == [AyahRef(2, 4)]


def test_repetition_is_not_reconfirmed(engine):
    engine.feed(1.0, words((1, 1), (1, 2)))
    engine.feed(2.0, words((1, 2), (1, 3)))

    assert confirmed(engine.feed(3.0, words((1, 3), (1, 2)))) == []


def test_skipped_ayah_is_not_confirmed(engine):
    engine.feed(1.0, words((1, 1), (1, 2)))

    assert confirmed(engine.feed(2.0, words((1, 2), (1, 4)))) == [AyahRef(1, 4)]


def test_lost_then_reacquire(engine):
    engine.feed(1.0, words((1, 1), (1, 2)))

    events = []
    for t in range(2, 2 + CONFIG.lost_after):
        events += engine.feed(float(t), ["n1", "n2", "n3", "n4"])

    assert [type(e) for e in events] == [Lost]
    assert engine.mode is Mode.ACQUIRE
    assert confirmed(engine.feed(10.0, words((2, 3), (2, 4), (2, 5)))) == [AyahRef(2, 3), AyahRef(2, 4), AyahRef(2, 5)]


def test_short_noise_is_not_a_miss(engine):
    engine.feed(1.0, words((1, 1), (1, 2)))

    for t in range(2, 12):
        assert engine.feed(float(t), ["n1"]) == []

    assert engine.mode is Mode.TRACK


def test_acquire_waits_on_nearby_refrain(engine):
    assert engine.feed(1.0, words((3, 2))) == []


def test_track_refrain_confirms_nearest_occurrence(engine):
    engine.feed(1.0, words((2, 5), (3, 1)))

    assert confirmed(engine.feed(2.0, words((3, 1), (3, 2)))) == [AyahRef(3, 2)]


def test_track_repeated_refrain_does_not_jump_ahead(engine):
    engine.feed(1.0, words((2, 5), (3, 1)))
    engine.feed(2.0, words((3, 1), (3, 2)))

    assert confirmed(engine.feed(3.0, words((3, 2)))) == []
    assert confirmed(engine.feed(4.0, words((3, 2), (3, 3)))) == [AyahRef(3, 3)]


def test_matches_outside_ayah_prefix_do_not_confirm(engine):
    engine.feed(1.0, words((3, 7), (4, 1)))

    window = words((4, 2), take=2) + [B, C]

    assert confirmed(engine.feed(2.0, window)) == [AyahRef(4, 2)]


def test_going_back_to_a_skipped_ayah_confirms_it(engine):
    engine.feed(1.0, words((1, 3), (1, 4)))
    engine.feed(2.0, words((1, 4), (1, 6)))

    assert confirmed(engine.feed(3.0, words((1, 6), (1, 5)))) == [AyahRef(1, 5)]
    assert confirmed(engine.feed(4.0, words((1, 5), (1, 6)))) == []


def test_stale_backward_ayah_is_not_confirmed(engine):
    engine.feed(1.0, words((1, 3), (1, 4)))
    engine.feed(2.0, words((1, 4), (1, 6)))

    assert confirmed(engine.feed(3.0, words((1, 5), (1, 6)))) == []


def test_ayah_needs_words_that_set_it_apart_from_neighbours(engine):
    engine.feed(1.0, words((5, 1)))

    assert confirmed(engine.feed(2.0, [P, Q])) == []
    assert confirmed(engine.feed(3.0, words((5, 3)))) == [AyahRef(5, 3)]


def test_far_forward_jump_needs_more_words(engine):
    engine.feed(1.0, words((1, 1), (1, 2)))

    assert confirmed(engine.feed(2.0, words((1, 6), take=2))) == []
    assert confirmed(engine.feed(3.0, words((1, 6)))) == [AyahRef(1, 6)]


def test_far_forward_ayah_that_is_not_current_is_not_confirmed(engine):
    engine.feed(1.0, words((1, 1), (1, 2)))

    assert confirmed(engine.feed(2.0, words((1, 6), (2, 1), take=4))) == []


def test_near_duplicate_ayah_is_not_confirmed_while_ambiguous(engine):
    engine.feed(1.0, words((6, 1), (6, 2)))
    engine.feed(2.0, words((6, 2), (6, 3)))

    assert confirmed(engine.feed(3.0, [W, *TAIL])) == []
    # Followed by 6:5, the tail can only be 6:4: confirmed late, not wrong.
    assert confirmed(engine.feed(4.0, [*TAIL, *words((6, 5))])) == [AyahRef(6, 4), AyahRef(6, 5)]


# One phrase three times, two of its words common (like 37:40/74/128 "illa ibad allah al-mukhlasin").
# A stray word next to the first occurrence must not hide the other two from Acquire.
PHRASE = [token(7, "c1"), token(7, "r1"), token(7, "c2"), token(7, "r2")]
STRAY = token(7, "z")
LOOKALIKE = {AyahRef(7, a): [token(7, a, w) for w in range(10)] for a in range(1, 9)}
LOOKALIKE |= {AyahRef(7, a): PHRASE for a in (2, 5, 7)}
LOOKALIKE[AyahRef(7, 3)] = [STRAY, *LOOKALIKE[AyahRef(7, 3)][1:]]
LOOKALIKE[AyahRef(7, 8)] = [PHRASE[0], PHRASE[2], *LOOKALIKE[AyahRef(7, 8)][2:]]


def test_acquire_sees_lookalikes_that_got_fewer_votes():
    engine = PositionEngine(QuranIndex.build(LOOKALIKE), EngineConfig(common_word_limit=3))

    assert engine.feed(1.0, [STRAY, *PHRASE]) == []
    assert engine.mode is Mode.ACQUIRE

