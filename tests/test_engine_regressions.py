"""M4 blind set failures, replayed on the real corpus."""

from pathlib import Path

import pytest

from tilavet.corpus import AyahRef, load_tanzil, normalize, strip_basmala
from tilavet.engine import AyahConfirmed, PositionEngine, QuranIndex

QURAN = Path(__file__).resolve().parents[1] / "data" / "raw" / "quran-simple-clean.txt"
pytestmark = pytest.mark.skipif(not QURAN.exists(), reason="run scripts/fetch_data.py first")


@pytest.fixture(scope="module")
def index() -> QuranIndex:
    quran = load_tanzil(QURAN)
    return QuranIndex.build({ref: normalize(strip_basmala(ref, text)).split() for ref, text in quran.items()})


def feed(engine: PositionEngine, *texts: str) -> list[AyahRef]:
    return [e.ref for t, text in enumerate(texts) for e in engine.feed(float(t), normalize(text).split())
            if isinstance(e, AyahConfirmed)]


def test_formula_phrase_does_not_commit(index):
    # minshawi-mujawwad-8: 21:19 opens "وله من في السماوات والأرض"; the window edge dropped "و".
    assert feed(PositionEngine(index), "له من في السماوات والارض") == []


def test_misheard_words_still_find_the_lookalike(index):
    # minshawi-mujawwad-1: 45:33 and 39:48 differ by one later word.
    assert feed(PositionEngine(index), "فوبدا لهم سييات موا") == []
