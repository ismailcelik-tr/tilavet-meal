from tilavet.engine import align_all, local_align

CORPUS = "w0 w1 alpha beta gamma delta w6 w7".split()


def test_exact_match_inside_region():
    result = local_align(["beta", "gamma", "delta"], CORPUS, 0, len(CORPUS))

    assert (result.corpus_start, result.corpus_end) == (3, 6)
    assert result.matched == 3
    assert result.score == 6


def test_noise_words_at_edges_are_ignored():
    result = local_align(["xx", "alpha", "beta", "gamma", "yy"], CORPUS, 0, len(CORPUS))

    assert (result.corpus_start, result.corpus_end) == (2, 5)
    assert result.matched == 3


def test_near_miss_word_counts_as_weak_match():
    result = local_align(["alpha", "betta", "gamma"], CORPUS, 0, len(CORPUS))

    assert result.matched == 3
    assert result.score == 5


def test_skipped_corpus_word_is_a_gap():
    result = local_align(["alpha", "beta", "delta"], CORPUS, 0, len(CORPUS))

    assert (result.corpus_start, result.corpus_end) == (2, 6)
    assert result.score == 5


def test_region_limits_search():
    assert local_align(["alpha", "beta"], CORPUS, 4, len(CORPUS)) is None


def test_matched_positions_are_reported():
    result = local_align(["beta", "gamma"], CORPUS, 0, len(CORPUS))

    assert result.positions == (3, 4)


def test_align_all_finds_every_occurrence():
    corpus = "r1 r2 u1 r1 r2 u2 r1 r2".split()

    results = align_all(["r1", "r2"], corpus, 0, len(corpus), min_score=3)

    assert sorted((a.corpus_start, a.corpus_end) for a in results) == [(0, 2), (3, 5), (6, 8)]


def test_align_all_respects_min_score():
    corpus = "r1 r2 u1 r1 x u2".split()

    results = align_all(["r1", "r2"], corpus, 0, len(corpus), min_score=3)

    assert [(a.corpus_start, a.corpus_end) for a in results] == [(0, 2)]


def test_hypothesis_end_is_reported():
    result = local_align(["alpha", "beta", "xx", "yy"], CORPUS, 0, len(CORPUS))

    assert result.hyp_end == 2


def test_matched_pairs_link_hypothesis_to_corpus():
    result = local_align(["xx", "beta", "gamma"], CORPUS, 0, len(CORPUS))

    assert result.pairs == ((1, 3), (2, 4))
