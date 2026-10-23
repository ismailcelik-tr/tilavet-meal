from tilavet.corpus import AyahRef
from tilavet.engine import QuranIndex

AYAHS = {
    AyahRef(1, 1): ["a", "b"],
    AyahRef(1, 2): ["c"],
    AyahRef(2, 1): ["a", "d", "e"],
}


def test_words_follow_mushaf_order():
    index = QuranIndex.build(AYAHS)

    assert index.words == ("a", "b", "c", "a", "d", "e")


def test_word_to_ayah_and_spans():
    index = QuranIndex.build(AYAHS)

    assert index.ayah_at(3) == AyahRef(2, 1)
    assert index.span(AyahRef(1, 2)) == (2, 3)
    assert index.ordinal(AyahRef(2, 1)) == 2


def test_postings():
    index = QuranIndex.build(AYAHS)

    assert index.positions("a") == (0, 3)
    assert index.positions("zzz") == ()
