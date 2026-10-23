"""Two-mode position tracker over ASR window hypotheses.

ACQUIRE: position unknown. Vote candidate regions from exact word hits, align
each, commit only if the best region beats every other region by a margin.
Identical passages tie, so the engine waits for disambiguating words.

TRACK: align only around the current position. An ayah is confirmed once
enough of its *opening* words match (ayahs are identified by their prefix;
scattered mid-ayah matches are look-alike phrases). Confirmed ayahs are never
re-confirmed (repetitions); going back to a never-confirmed ayah needs one more
word and must be where the reciter is now, else it is stale. Repeated misses
-> LOST -> ACQUIRE.
"""

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from tilavet.corpus import AyahRef
from tilavet.engine.align import Alignment, align_all
from tilavet.engine.index import QuranIndex
from tilavet.feasibility import track_prefix_lengths

__all__ = ["AyahConfirmed", "EngineConfig", "Event", "Lost", "Mode", "PositionEngine"]


class Mode(Enum):
    ACQUIRE = "acquire"
    TRACK = "track"


@dataclass(frozen=True)
class AyahConfirmed:
    t: float
    ref: AyahRef
    mode: Mode
    score: int


@dataclass(frozen=True)
class Lost:
    t: float


Event = AyahConfirmed | Lost


@dataclass(frozen=True)
class EngineConfig:
    acquire_min_matched: int = 4
    acquire_min_score: int = 6
    acquire_margin: int = 3
    acquire_min_votes: int = 3
    acquire_max_candidates: int = 8
    diagonal_tolerance: int = 8  # words; ASR insertions/deletions shift the diagonal
    common_word_limit: int = 500  # words with more occurrences don't vote
    track_back: int = 30
    track_ahead: int = 50
    track_min_score: int = 3
    track_tie_slack: int = 0
    confirm_words: int = 2  # minimum; raised per ayah to what sets it apart from its neighbours
    distinct_window: int = 3  # neighbours considered: ayahs within this distance + restarts in the previous one
    prefix_slack: int = 1  # ASR may drop one of the opening words
    backtrack_extra: int = 1
    lost_after: int = 4  # consecutive non-matching hops
    min_words_for_miss: int = 3


class PositionEngine:
    def __init__(self, index: QuranIndex, config: EngineConfig = EngineConfig()) -> None:
        self._index = index
        self._config = config
        self._mode = Mode.ACQUIRE
        self._pointer = 0
        self._last_confirmed = -1
        self._confirmed: set[int] = set()
        self._misses = 0
        self._distinct = _distinct_prefixes(index, config.distinct_window)

    @property
    def mode(self) -> Mode:
        return self._mode

    def feed(self, t: float, words: Sequence[str]) -> list[Event]:
        if not words:
            return []

        if self._mode is Mode.ACQUIRE:
            return self._acquire(t, words)

        return self._track(t, words)

    def _acquire(self, t: float, words: Sequence[str]) -> list[Event]:
        config = self._config
        alignments = self._candidate_alignments(words)
        if not alignments:
            return []

        best = max(alignments, key=lambda a: a.score)
        rivals = [a for a in alignments if not _overlaps(a, best)]
        runner_up = max((a.score for a in rivals), default=0)

        if (
            best.score < config.acquire_min_score
            or best.matched < config.acquire_min_matched
            or best.score - runner_up < config.acquire_margin
        ):
            return []

        self._mode = Mode.TRACK
        self._pointer = best.corpus_end
        self._misses = 0
        current = self._index.ordinal_at(best.positions[-1])
        self._last_confirmed = current
        self._confirmed = {current}
        return [AyahConfirmed(t, self._index.ref(current), Mode.ACQUIRE, best.score)]

    def _candidate_alignments(self, words: Sequence[str]) -> list[Alignment]:
        config = self._config
        diagonals: Counter[int] = Counter()
        for i, word in enumerate(words):
            positions = self._index.positions(word)
            if len(positions) > config.common_word_limit:
                continue
            for position in positions:
                diagonals[position - i] += 1

        tolerance = config.diagonal_tolerance
        support = {d: sum(diagonals[d + k] for k in range(-tolerance, tolerance + 1)) for d in diagonals}

        chosen: list[int] = []
        for diagonal, votes in sorted(support.items(), key=lambda item: (-item[1], item[0])):
            if votes < config.acquire_min_votes or len(chosen) >= config.acquire_max_candidates:
                break
            if all(abs(diagonal - c) > tolerance for c in chosen):
                chosen.append(diagonal)

        # Rivals below this cannot block a commit, so they need not be found.
        min_score = max(1, config.acquire_min_score - config.acquire_margin)
        alignments: list[Alignment] = []
        corpus = self._index.words
        for diagonal in chosen:
            lo = max(0, diagonal - tolerance)
            hi = min(len(corpus), diagonal + len(words) + tolerance)
            for alignment in align_all(words, corpus, lo, hi, min_score):
                if not any(_overlaps(alignment, a) for a in alignments):
                    alignments.append(alignment)

        return alignments

    def _track(self, t: float, words: Sequence[str]) -> list[Event]:
        config = self._config
        corpus = self._index.words
        lo = max(0, self._pointer - config.track_back)
        hi = min(len(corpus), self._pointer + config.track_ahead)
        alignments = align_all(words, corpus, lo, hi, config.track_min_score)

        if not alignments:
            if len(words) < config.min_words_for_miss:
                return []

            self._misses += 1
            if self._misses < config.lost_after:
                return []

            self._mode = Mode.ACQUIRE
            return [Lost(t)]

        # Ties (refrains, back-jumps): the most recent words decide, then closeness to the pointer.
        best_score = max(a.score for a in alignments)
        alignment = min(
            (a for a in alignments if a.score >= best_score - config.track_tie_slack),
            key=lambda a: (-a.hyp_end, abs(a.corpus_end - self._pointer)),
        )
        self._misses = 0
        self._pointer = alignment.corpus_end

        matched = set(alignment.positions)
        current = self._index.ordinal_at(alignment.positions[-1])
        events: list[Event] = []
        for ordinal in sorted({self._index.ordinal_at(p) for p in matched}):
            backward = ordinal < self._last_confirmed
            if ordinal in self._confirmed or (backward and ordinal != current):
                continue

            start, end = self._index.span(self._index.ref(ordinal))
            extra = config.backtrack_extra if backward else 0
            distinct = self._distinct[ordinal] or 0
            needed = min(max(config.confirm_words, distinct) + extra, end - start)
            prefix = range(start, min(end, start + needed + config.prefix_slack))
            if sum(p in matched for p in prefix) < needed:
                continue

            events.append(AyahConfirmed(t, self._index.ref(ordinal), Mode.TRACK, alignment.score))
            self._confirmed.add(ordinal)
            self._last_confirmed = max(self._last_confirmed, ordinal)

        return events


def _distinct_prefixes(index: QuranIndex, window: int) -> list[int | None]:
    """Per ayah ordinal: opening words needed to tell it from nearby ayahs (None: never resolved / first)."""
    by_sura: dict[int, list[int]] = defaultdict(list)
    for ordinal, ref in enumerate(index.refs):
        by_sura[ref.sura].append(ordinal)

    result: list[int | None] = [None] * len(index.refs)
    for ordinals in by_sura.values():
        ayahs = [index.words[slice(*index.span(index.ref(o)))] for o in ordinals]
        for o, k in zip(ordinals, track_prefix_lengths(ayahs, window), strict=True):
            result[o] = k
    return result


def _overlaps(a: Alignment, b: Alignment) -> bool:
    return a.corpus_start < b.corpus_end and b.corpus_start < a.corpus_end
