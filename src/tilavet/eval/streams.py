"""Score meal emissions against a ground-truth recitation timeline."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from tilavet.corpus import AyahRef

__all__ = ["Emission", "Segment", "StreamScore", "pause_emissions", "score_stream"]

UnitKey = tuple[int, int]  # (sura, first ayah) of a meal unit

# A meal confirmed just after its ayah ends (hop + compute) is still on time.
END_TOLERANCE_S = 2.0
# Later than that but within this window: right meaning, delivered late (not misleading).
LATE_LIMIT_S = 10.0


@dataclass(frozen=True)
class Segment:
    ref: AyahRef | None  # None = silence
    start: float
    end: float


@dataclass(frozen=True)
class Emission:
    t: float
    unit: UnitKey


@dataclass
class StreamScore:
    emissions: int = 0
    wrong: int = 0  # meaning of an ayah not recited recently: misleading
    late: int = 0
    duplicates: int = 0
    occurrences: int = 0  # first occurrence of each unit in the stream
    recalled: int = 0
    latency_from_start: list[float] = field(default_factory=list)
    latency_from_end: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class _Occurrence:
    unit: UnitKey
    start: float
    end: float


def _first_occurrences(truth: Sequence[Segment], unit_of: Mapping[AyahRef, UnitKey]) -> list[_Occurrence]:
    """Group consecutive segments of one unit (pauses are transparent); keep each unit's first run."""
    runs: list[_Occurrence] = []
    for segment in truth:
        if segment.ref is None:
            continue

        unit = unit_of[segment.ref]
        if runs and runs[-1].unit == unit:
            runs[-1] = _Occurrence(unit, runs[-1].start, segment.end)
            continue

        runs.append(_Occurrence(unit, segment.start, segment.end))

    seen: set[UnitKey] = set()
    first = []
    for run in runs:
        if run.unit not in seen:
            seen.add(run.unit)
            first.append(run)
    return first


def score_stream(
    truth: Sequence[Segment], emissions: Sequence[Emission], unit_of: Mapping[AyahRef, UnitKey]
) -> StreamScore:
    result = StreamScore(emissions=len(emissions))
    correct_units: set[UnitKey] = set()
    correct: list[Emission] = []

    for emission in emissions:
        spans = [(s.start, s.end) for s in truth if s.ref is not None and unit_of[s.ref] == emission.unit]
        if not any(start <= emission.t <= end + LATE_LIMIT_S for start, end in spans):
            result.wrong += 1
            continue
        if not any(start <= emission.t <= end + END_TOLERANCE_S for start, end in spans):
            result.late += 1

        if emission.unit in correct_units:
            result.duplicates += 1
        correct_units.add(emission.unit)
        correct.append(emission)

    for occurrence in _first_occurrences(truth, unit_of):
        result.occurrences += 1
        hit = next(
            (
                e
                for e in correct
                if e.unit == occurrence.unit and occurrence.start <= e.t <= occurrence.end + LATE_LIMIT_S
            ),
            None,
        )
        if hit is None:
            continue

        result.recalled += 1
        result.latency_from_start.append(hit.t - occurrence.start)
        result.latency_from_end.append(hit.t - occurrence.end)

    return result


def pause_emissions(truth: Sequence[Segment], emissions: Sequence[Emission], min_pause_s: float) -> int:
    """Meals played inside silences of at least `min_pause_s`, after the last ayah's meal had its LATE_LIMIT_S."""
    pauses = [s for s in truth if s.ref is None and s.end - s.start >= min_pause_s]
    return sum(1 for p in pauses for e in emissions if p.start + LATE_LIMIT_S < e.t <= p.end)
