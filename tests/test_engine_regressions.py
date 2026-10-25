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


def test_going_back_is_not_progress(index):
    # muhammad-ayyoub-1: after 22:56 the reciter repeats 22:55; its "الذين كفروا" matches 22:57's opening.
    engine = PositionEngine(index)
    texts = [
        "وليعلم الذين اوتوا العلم انه الحق من ربك فيومنوا به فتخبت له قلوبهم وان الله لهاد الذين امنوا الى صراط مستقيم "
        "ولا يزال الذين كفروا في مريه منه حتي تاتيهم الساعه بغته او ياتيهم عذاب يوم عقيم",
        "الملك يوميذ لله يحكم بينهم فالذين امنوا وعملوا الصالحات في جنات النعيم",
        "في جنات النعيولا يزال الذين كفر",
    ]

    assert AyahRef(22, 57) not in feed(engine, *texts)


def test_short_first_ayah_is_backfilled(index):
    # Field test: Al-Asr 103:1 is one word; the passage is only placed once 103:3 begins.
    words = normalize("بسم الله الرحمن الرحيم والعصر إن الإنسان لفي خسر إلا الذين آمنوا").split()
    engine = PositionEngine(index)
    refs = [e.ref for n in range(1, len(words) + 1) for e in engine.feed(float(n), words[:n])
            if isinstance(e, AyahConfirmed)]

    assert refs[:3] == [AyahRef(103, 1), AyahRef(103, 2), AyahRef(103, 3)]
