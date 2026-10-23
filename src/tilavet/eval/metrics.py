from collections.abc import Sequence
from dataclasses import dataclass

from rapidfuzz.distance import Levenshtein

from tilavet.corpus import normalize

__all__ = ["Score", "fold_alef", "prefix_match", "score"]


@dataclass(frozen=True)
class Score:
    cer: float
    wer: float
    ref_chars: int
    ref_words: int


def score(refs: Sequence[str], hyps: Sequence[str]) -> Score:
    """Corpus-level CER/WER on normalized text: total edits / total reference length."""
    char_edits = word_edits = ref_chars = ref_words = 0

    for ref, hyp in zip(refs, hyps, strict=True):
        ref, hyp = normalize(ref), normalize(hyp)
        char_edits += Levenshtein.distance(ref, hyp)
        word_edits += Levenshtein.distance(ref.split(), hyp.split())
        ref_chars += len(ref)
        ref_words += len(ref.split())

    return Score(cer=char_edits / ref_chars, wer=word_edits / ref_words, ref_chars=ref_chars, ref_words=ref_words)


def fold_alef(text: str) -> str:
    """Drop alef: Uthmani rasm and standard spelling differ mostly in long-a alefs."""
    return normalize(text).replace("ا", "")


def prefix_match(ref: str, hyp: str, words: int) -> bool:
    """Are the first `words` reference words recognized exactly? (Track needs 1–3 words.)"""
    expected = normalize(ref).split()[:words]
    return normalize(hyp).split()[: len(expected)] == expected
