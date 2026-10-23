"""How many words must be heard before an ayah is unambiguous."""

from collections import Counter
from collections.abc import Sequence
from itertools import accumulate

__all__ = ["global_prefix_lengths", "track_prefix_lengths"]

Ayahs = Sequence[Sequence[str]]


def _stream(ayahs: Ayahs) -> tuple[list[str], list[int]]:
    stream = [word for ayah in ayahs for word in ayah]
    starts = [0, *accumulate(len(ayah) for ayah in ayahs)][:-1]
    return stream, starts


def global_prefix_lengths(ayahs: Ayahs, max_k: int) -> list[int | None]:
    """Acquire mode: position unknown.

    For each ayah, the smallest k such that the k words starting at the ayah
    occur exactly once anywhere in the recited stream. k may exceed the ayah's
    length (the reciter continues into the next ayah). None if k > max_k.
    """
    stream, starts = _stream(ayahs)
    result: list[int | None] = [None] * len(ayahs)
    unresolved = set(range(len(ayahs)))

    for k in range(1, max_k + 1):
        if not unresolved:
            break

        counts = Counter(tuple(stream[i : i + k]) for i in range(len(stream) - k + 1))
        for index in list(unresolved):
            start = starts[index]
            if start + k > len(stream) or counts[tuple(stream[start : start + k])] != 1:
                continue

            result[index] = k
            unresolved.discard(index)

    return result


def track_prefix_lengths(ayahs: Ayahs, window: int) -> list[int | None]:
    """Track mode within one sura: the previous ayah has just been recited.

    Competing hypotheses: any ayah within `window` of the expected one, or a
    restart from any word of the previous ayah. Returns the words needed to
    rule them all out; None for the first ayah (no context) or if never resolved.
    """
    stream, starts = _stream(ayahs)
    result: list[int | None] = [None]

    for index in range(1, len(ayahs)):
        start = starts[index]
        neighbours = range(max(0, index - window), min(len(ayahs), index + window + 1))
        rivals = {starts[i] for i in neighbours} | set(range(starts[index - 1], start))
        rivals.discard(start)
        result.append(_words_to_resolve(stream, start, rivals))

    return result


def _words_to_resolve(stream: list[str], start: int, rivals: set[int]) -> int | None:
    for offset in range(len(stream) - start):
        word = stream[start + offset]
        rivals = {r for r in rivals if r + offset < len(stream) and stream[r + offset] == word}
        if not rivals:
            return offset + 1

    return None
