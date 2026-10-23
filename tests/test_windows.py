from tilavet.stream import sliding_windows


def test_windows_end_on_hops_and_cap_length():
    # 3.5 s at 10 Hz sampling, hop 1 s, window 2 s.
    result = list(sliding_windows(35, sample_rate=10, hop_s=1.0, window_s=2.0))

    assert result == [(1.0, slice(0, 10)), (2.0, slice(0, 20)), (3.0, slice(10, 30))]


def test_short_input_has_no_window():
    assert list(sliding_windows(5, sample_rate=10, hop_s=1.0, window_s=2.0)) == []
