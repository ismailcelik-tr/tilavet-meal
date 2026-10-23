"""Local (Smith-Waterman) alignment of ASR words against a corpus region.

Local, because a sliding ASR window has garbage at both edges (cut words,
basmala, isti'adha) and covers only part of the region.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from rapidfuzz.distance import Indel

__all__ = ["Alignment", "align_all", "local_align"]

STRONG_SIM = 0.9
WEAK_SIM = 0.7
STRONG_SCORE = 2
WEAK_SCORE = 1
MISMATCH = -1
GAP = -1

_DIAG, _UP, _LEFT = 1, 2, 3


@dataclass(frozen=True)
class Alignment:
    score: int
    corpus_start: int  # [start, end) of the aligned corpus span
    corpus_end: int
    pairs: tuple[tuple[int, int], ...]  # (hypothesis index, corpus position) of matched words
    hyp_end: int  # hypothesis words [.., hyp_end) take part; larger = covers more recent audio

    @property
    def positions(self) -> tuple[int, ...]:
        return tuple(position for _, position in self.pairs)

    @property
    def matched(self) -> int:
        return len(self.pairs)


def _substitution(a: str, b: str) -> int:
    similarity = Indel.normalized_similarity(a, b)
    if similarity >= STRONG_SIM:
        return STRONG_SCORE
    if similarity >= WEAK_SIM:
        return WEAK_SCORE
    return MISMATCH


def local_align(hyp: Sequence[str], corpus: Sequence[str], lo: int, hi: int) -> Alignment | None:
    """Best local alignment of `hyp` inside corpus[lo:hi]; None if nothing scores above 0."""
    region = corpus[lo:hi]
    rows, cols = len(hyp) + 1, len(region) + 1
    score = [[0] * cols for _ in range(rows)]
    move = [[0] * cols for _ in range(rows)]
    best, best_at = 0, (0, 0)

    for i in range(1, rows):
        for j in range(1, cols):
            candidates = (
                (score[i - 1][j - 1] + _substitution(hyp[i - 1], region[j - 1]), _DIAG),
                (score[i - 1][j] + GAP, _UP),
                (score[i][j - 1] + GAP, _LEFT),
            )
            value, direction = max(candidates)
            if value <= 0:
                continue

            score[i][j], move[i][j] = value, direction
            if value > best:
                best, best_at = value, (i, j)

    if best <= 0:
        return None

    i, j = best_at
    hyp_end, end = i, j
    pairs = []
    while i > 0 and j > 0 and score[i][j] > 0:
        direction = move[i][j]
        if direction == _DIAG:
            if _substitution(hyp[i - 1], region[j - 1]) > 0:
                pairs.append((i - 1, lo + j - 1))
            i, j = i - 1, j - 1
        elif direction == _UP:
            i -= 1
        else:
            j -= 1

    return Alignment(
        score=best,
        corpus_start=lo + j,
        corpus_end=lo + end,
        pairs=tuple(reversed(pairs)),
        hyp_end=hyp_end,
    )


def align_all(hyp: Sequence[str], corpus: Sequence[str], lo: int, hi: int, min_score: int) -> list[Alignment]:
    """Non-overlapping alignments scoring >= min_score: best one, then recurse left and right of it.

    Finds every occurrence of a repeated passage (refrains) inside one region.
    """
    best = local_align(hyp, corpus, lo, hi)
    if best is None or best.score < min_score:
        return []

    return [
        *align_all(hyp, corpus, lo, best.corpus_start, min_score),
        best,
        *align_all(hyp, corpus, best.corpus_end, hi, min_score),
    ]
