import pytest

from tilavet.corpus import AyahRef
from tilavet.eval import Emission, Segment, pause_emissions, score_stream

A1, A2, A3 = AyahRef(1, 1), AyahRef(1, 2), AyahRef(1, 3)
UNIT_OF = {A1: (1, 1), A2: (1, 2), A3: (1, 2)}  # ayahs 2-3 share one meal unit

TRUTH = [
    Segment(A1, 0.0, 5.0),
    Segment(A2, 5.0, 10.0),
    Segment(None, 10.0, 25.0),  # long pause
    Segment(A3, 25.0, 30.0),
    Segment(A1, 30.0, 35.0),  # repetition of A1
]


def test_perfect_run():
    emissions = [Emission(2.0, (1, 1)), Emission(6.5, (1, 2))]

    result = score_stream(TRUTH, emissions, UNIT_OF)

    assert (result.emissions, result.wrong, result.late, result.duplicates) == (2, 0, 0, 0)
    assert (result.occurrences, result.recalled) == (2, 2)
    assert result.latency_from_start == pytest.approx([2.0, 1.5])
    assert result.latency_from_end == pytest.approx([-3.0, -23.5])


def test_emission_shortly_after_ayah_end_is_correct():
    assert score_stream(TRUTH, [Emission(6.5, (1, 1))], UNIT_OF).wrong == 0


def test_emission_during_pause_is_wrong():
    assert score_stream(TRUTH, [Emission(22.0, (1, 2))], UNIT_OF).wrong == 1


def test_correct_unit_a_few_seconds_after_its_ayah_is_late_not_wrong():
    result = score_stream(TRUTH, [Emission(8.0, (1, 1))], UNIT_OF)

    assert (result.wrong, result.late) == (0, 1)


def test_wrong_unit_is_wrong():
    assert score_stream(TRUTH, [Emission(2.0, (1, 2))], UNIT_OF).wrong == 1


def test_replay_on_repetition_is_duplicate():
    emissions = [Emission(2.0, (1, 1)), Emission(31.0, (1, 1))]

    assert score_stream(TRUTH, emissions, UNIT_OF).duplicates == 1


def test_missed_unit_lowers_recall():
    result = score_stream(TRUTH, [Emission(2.0, (1, 1))], UNIT_OF)

    assert (result.occurrences, result.recalled) == (2, 1)


def test_emission_late_in_a_long_pause_counts():
    assert pause_emissions(TRUTH, [Emission(22.0, (1, 2))], min_pause_s=15.0) == 1


def test_last_ayahs_meal_early_in_a_pause_does_not_count():
    assert pause_emissions(TRUTH, [Emission(19.0, (1, 2))], min_pause_s=15.0) == 0


def test_short_pauses_are_ignored():
    assert pause_emissions(TRUTH, [Emission(22.0, (1, 2))], min_pause_s=20.0) == 0
