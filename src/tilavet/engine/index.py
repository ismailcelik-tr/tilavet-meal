from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from tilavet.corpus import AyahRef

__all__ = ["QuranIndex"]


@dataclass(frozen=True)
class QuranIndex:
    """The recited word stream in mushaf order, with word -> ayah lookups."""

    words: tuple[str, ...]
    _word_ayah: tuple[int, ...]  # ordinal of each word's ayah
    _refs: tuple[AyahRef, ...]  # ordinal -> ref
    _ordinals: Mapping[AyahRef, int]
    _starts: tuple[int, ...]  # ordinal -> first word position
    _postings: Mapping[str, tuple[int, ...]]

    @classmethod
    def build(cls, ayahs: Mapping[AyahRef, Sequence[str]]) -> "QuranIndex":
        refs = tuple(sorted(ayahs))
        words: list[str] = []
        word_ayah: list[int] = []
        starts: list[int] = []
        postings: dict[str, list[int]] = defaultdict(list)

        for ordinal, ref in enumerate(refs):
            starts.append(len(words))
            for word in ayahs[ref]:
                postings[word].append(len(words))
                words.append(word)
                word_ayah.append(ordinal)

        return cls(
            words=tuple(words),
            _word_ayah=tuple(word_ayah),
            _refs=refs,
            _ordinals={ref: i for i, ref in enumerate(refs)},
            _starts=tuple(starts),
            _postings={w: tuple(p) for w, p in postings.items()},
        )

    @property
    def refs(self) -> tuple[AyahRef, ...]:
        return self._refs

    def ayah_at(self, position: int) -> AyahRef:
        return self._refs[self._word_ayah[position]]

    def ordinal(self, ref: AyahRef) -> int:
        return self._ordinals[ref]

    def ordinal_at(self, position: int) -> int:
        return self._word_ayah[position]

    def ref(self, ordinal: int) -> AyahRef:
        return self._refs[ordinal]

    def span(self, ref: AyahRef) -> tuple[int, int]:
        """[start, end) word positions of an ayah."""
        ordinal = self._ordinals[ref]
        end = self._starts[ordinal + 1] if ordinal + 1 < len(self._starts) else len(self.words)
        return self._starts[ordinal], end

    def positions(self, word: str) -> tuple[int, ...]:
        return self._postings.get(word, ())
