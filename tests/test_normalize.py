import pytest

from tilavet.corpus import normalize


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("بِسْمِ اللَّهِ", "بسم الله"),
        ("الرَّحْمَٰنِ", "الرحمن"),
        ("الـرحمـن", "الرحمن"),
        ("أإآٱا", "ااااا"),
        ("على", "علي"),
        ("رحمة", "رحمه"),
        ("مؤمن", "مومن"),
        ("سئل", "سيل"),
        ("ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى", "ذلك الكتاب لا ريب فيه هدي"),
        ("  الحمد   لله\tرب\n", "الحمد لله رب"),
        ("قال، نعم. أتعلم؟", "قال نعم اتعلم"),
        ("الم 1 ok", "الم"),
        ("یوم کتاب", "يوم كتاب"),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


def test_normalize_is_idempotent():
    text = "ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ"
    assert normalize(normalize(text)) == normalize(text)


def test_normalize_keeps_standalone_hamza():
    assert normalize("السماء") == "السماء"
