from tilavet.feasibility import global_prefix_lengths, track_prefix_lengths


def test_global_prefix_counts_occurrences_anywhere_in_stream():
    # "a b" appears at start of ayah 0 and inside ayah 2.
    ayahs = [["a", "b", "c"], ["d", "e"], ["x", "a", "b", "z"]]

    assert global_prefix_lengths(ayahs, max_k=5) == [3, 1, 1]


def test_global_prefix_may_spill_into_next_ayah():
    ayahs = [["a"], ["b"], ["a"], ["c"]]

    assert global_prefix_lengths(ayahs, max_k=5) == [2, 1, 2, 1]


def test_global_prefix_is_none_beyond_max_k():
    ayahs = [["a", "b"], ["a", "b"]]

    assert global_prefix_lengths(ayahs, max_k=2) == [None, None]


def test_track_first_ayah_has_no_context():
    assert track_prefix_lengths([["a"], ["b"]], window=1)[0] is None


def test_track_distinguishes_from_neighbours_and_previous_ayah_positions():
    # Ayah 2 starts like a mid-ayah-1 restart ("q r ..."), so 3 words are needed.
    ayahs = [["k"], ["p", "q", "r", "s"], ["q", "r", "t"], ["u"]]

    assert track_prefix_lengths(ayahs, window=1) == [None, 1, 3, 1]


def test_track_ignores_ayahs_outside_window():
    ayahs = [["a", "b"], ["c"], ["d"], ["a", "x"]]

    assert track_prefix_lengths(ayahs, window=1)[3] == 1
