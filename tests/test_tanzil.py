import pytest

from tilavet.corpus import AyahRef, MealUnit, meal_units, parse_tanzil, strip_basmala

BASMALA = "بسم الله الرحمن الرحيم"


def test_strip_basmala_from_first_ayah_prefix():
    assert strip_basmala(AyahRef(2, 1), f"{BASMALA} الم") == "الم"


def test_strip_basmala_keeps_fatiha_and_inner_occurrences():
    assert strip_basmala(AyahRef(1, 1), BASMALA) == BASMALA
    assert strip_basmala(AyahRef(27, 30), f"وإنه {BASMALA}") == f"وإنه {BASMALA}"
    assert strip_basmala(AyahRef(9, 1), "براءة من الله") == "براءة من الله"


def test_parse_skips_comments_and_blank_lines():
    lines = [
        "1|1|بسم الله الرحمن الرحيم",
        "",
        "#  Tanzil license notice",
        "1|2|الحمد لله رب العالمين",
    ]

    assert parse_tanzil(lines) == {
        AyahRef(1, 1): "بسم الله الرحمن الرحيم",
        AyahRef(1, 2): "الحمد لله رب العالمين",
    }


def test_parse_keeps_pipe_inside_text():
    assert parse_tanzil(["2|3|a|b"]) == {AyahRef(2, 3): "a|b"}


def test_parse_rejects_malformed_line():
    with pytest.raises(ValueError):
        parse_tanzil(["1|x|text"])


def test_parse_rejects_duplicate_ref():
    with pytest.raises(ValueError):
        parse_tanzil(["1|1|a", "1|1|b"])


def test_meal_units_merge_consecutive_identical_text():
    meal = {
        AyahRef(114, 3): "c",
        AyahRef(114, 4): "x",
        AyahRef(114, 5): "x",
        AyahRef(114, 6): "x",
    }

    assert meal_units(meal) == [
        MealUnit(sura=114, first=3, last=3, text="c"),
        MealUnit(sura=114, first=4, last=6, text="x"),
    ]


def test_meal_units_do_not_merge_non_consecutive_or_cross_sura():
    meal = {
        AyahRef(1, 7): "x",
        AyahRef(2, 1): "x",
        AyahRef(2, 2): "y",
        AyahRef(2, 3): "x",
    }

    units = meal_units(meal)

    assert [(u.sura, u.first, u.last) for u in units] == [(1, 7, 7), (2, 1, 1), (2, 2, 2), (2, 3, 3)]


def test_meal_unit_refs():
    unit = MealUnit(sura=114, first=4, last=6, text="x")
    assert unit.refs == (AyahRef(114, 4), AyahRef(114, 5), AyahRef(114, 6))
