import pytest

from tilavet.eval import Score, fold_alef, prefix_match, score


def test_perfect_hypothesis():
    result = score(["بسم الله"], ["بسم الله"])

    assert result == Score(cer=0.0, wer=0.0, ref_chars=8, ref_words=2)


def test_rates_are_corpus_level():
    # 1 substituted char of 8, then 0 of 3.
    result = score(["بسم الله", "الم"], ["بسم اللا", "الم"])

    assert result.cer == pytest.approx(1 / 11)
    assert result.wer == pytest.approx(1 / 3)


def test_hypothesis_is_normalized_before_scoring():
    assert score(["الرحمن"], ["الرَّحْمَٰنِ"]).cer == 0.0


def test_fold_alef_ignores_rasm_spelling_differences():
    assert fold_alef("الرحمان") == fold_alef("الرحمن")


@pytest.mark.parametrize(
    ("hyp", "expected"),
    [
        ("قل اعوذ برب الناس", True),
        ("قل اعوذ برب", True),
        ("قل اعوذ", False),
        ("قل اعوز برب الناس", False),
    ],
)
def test_prefix_match(hyp, expected):
    assert prefix_match("قل أعوذ برب الناس", hyp, words=3) is expected


def test_prefix_match_uses_whole_reference_when_shorter():
    assert prefix_match("الم", "الم", words=3) is True
