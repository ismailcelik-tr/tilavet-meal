"""Two-mode position tracker over ASR window hypotheses.

ACQUIRE: position unknown. Vote candidate regions from exact word hits, align
each, commit only if the best region beats every other region by a margin.
Identical passages tie, so the engine waits for disambiguating words. Every
place where the winner's corpus words line up is aligned as a rival: a stray
or misheard word must not hide a look-alike passage.

TRACK: align only around the current position. An ayah is confirmed once
enough of its *opening* words match (ayahs are identified by their prefix;
scattered mid-ayah matches are look-alike phrases). Confirmed ayahs are never
re-confirmed (repetitions). A non-sequential ayah (going back, or more than
`max_skip` ayahs ahead) needs extra words and must be where the reciter is now:
window edges distort words into look-alikes of nearby passages. Repeated
misses -> LOST -> ACQUIRE.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
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
    acquire_rival_votes: int = 2  # the winner's own rare words lining up elsewhere: a look-alike passage
    acquire_backfill: int = 2  # earlier heard ayahs of the winning match also confirmed; a short opening ayah (103:1)
    acquire_backfill_age_s: float = 7.0  # older ones are skipped: a meal > 10 s after its ayah misleads
    window_s: float = 12.0  # ASR window, to estimate how long ago a word was heard
    diagonal_tolerance: int = 8  # words; ASR insertions/deletions shift the diagonal
    common_word_limit: int = 500  # words with more occurrences don't vote
    track_back: int = 30
    track_ahead: int = 50
    track_min_score: int = 3
    track_tie_slack: int = 0
    track_margin: int = 2  # words a rival this close elsewhere also explains are contested (near-duplicates)
    past_margin: int = 3  # rivals over ayahs already recited: likely a repetition, contest more readily
    confirm_words: int = 2  # minimum; raised per ayah to what sets it apart from its neighbours
    distinct_window: int = 3  # neighbours considered: ayahs within this distance + restarts in the previous one
    prefix_slack: int = 1  # ASR may drop one of the opening words
    max_skip: int = 2  # ayahs a reciter may skip and still count as sequential
    jump_extra: int = 1
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
        voters = list(enumerate(words))
        alignments = self._candidate_alignments(words, voters, config.acquire_min_votes, config.acquire_max_candidates)
        if not alignments:
            return []

        best = max(alignments, key=lambda a: a.score)
        # Look-alikes share the winner's corpus words, not the (maybe misheard) hypothesis words.
        # All are aligned: a formula phrase can recur in hundreds of places.
        corpus = self._index.words
        lookalikes = self._candidate_alignments(words, [(h, corpus[p]) for h, p in best.pairs],
                                                config.acquire_rival_votes, None)
        rivals = [a for a in alignments + lookalikes if not _overlaps(a, best)]
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
        ordinals = [*self._backfill(len(words), best, current), current]
        self._last_confirmed = current
        self._confirmed = set(ordinals)
        return [AyahConfirmed(t, self._index.ref(o), Mode.ACQUIRE, best.score) for o in ordinals]

    def _backfill(self, hyp_len: int, best: Alignment, current: int) -> list[int]:
        """Earlier ayahs of the match with a heard word, recent enough for their meal to still make sense.

        Age is estimated from the words after an ayah's last matched word, assuming words spread evenly over the
        window; a window not yet full overestimates it, which only skips more."""
        config = self._config
        if config.acquire_backfill == 0:
            return []

        last_heard: dict[int, int] = {}
        for h, position in best.pairs:
            last_heard[self._index.ordinal_at(position)] = h
        earlier = sorted(o for o in last_heard if o < current)[-config.acquire_backfill:]
        seconds_per_word = config.window_s / hyp_len
        return [o for o in earlier if (hyp_len - 1 - last_heard[o]) * seconds_per_word <= config.acquire_backfill_age_s]

    def _candidate_alignments(self, words: Sequence[str], voters: Iterable[tuple[int, str]], min_votes: int,
                              limit: int | None) -> list[Alignment]:
        """Align regions where at least `min_votes` (hypothesis index, word) voters line up; at most `limit`."""
        config = self._config
        diagonals: Counter[int] = Counter()
        for i, word in voters:
            positions = self._index.positions(word)
            if len(positions) > config.common_word_limit:
                continue
            for position in positions:
                diagonals[position - i] += 1

        tolerance = config.diagonal_tolerance
        support = {d: sum(diagonals[d + k] for k in range(-tolerance, tolerance + 1)) for d in diagonals}

        chosen: list[int] = []
        for diagonal, votes in sorted(support.items(), key=lambda item: (-item[1], item[0])):
            if votes < min_votes or (limit is not None and len(chosen) >= limit):
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

        rivals = [a for a in alignments if not _overlaps(a, alignment) and a.score > alignment.score - self._margin(a)]
        contested = {h for rival in rivals for h, _ in rival.pairs}
        evidence = {position for h, position in alignment.pairs if h not in contested}

        matched = set(alignment.positions)
        current = self._index.ordinal_at(alignment.positions[-1])
        events: list[Event] = []
        for ordinal in sorted({self._index.ordinal_at(p) for p in matched}):
            sequential = self._last_confirmed < ordinal <= self._last_confirmed + 1 + config.max_skip
            if ordinal in self._confirmed or (not sequential and ordinal != current):
                continue

            start, end = self._index.span(self._index.ref(ordinal))
            extra = 0 if sequential else config.jump_extra
            distinct = self._distinct[ordinal] or 0
            needed = min(max(config.confirm_words, distinct) + extra, end - start)
            prefix = range(start, min(end, start + needed + config.prefix_slack))
            if sum(p in evidence for p in prefix) < needed:
                continue

            events.append(AyahConfirmed(t, self._index.ref(ordinal), Mode.TRACK, alignment.score))
            self._confirmed.add(ordinal)
            self._last_confirmed = max(self._last_confirmed, ordinal)

        return events

    def _margin(self, rival: Alignment) -> int:
        recited = all(self._index.ordinal_at(p) in self._confirmed for p in rival.positions)
        return self._config.past_margin if recited else self._config.track_margin


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
