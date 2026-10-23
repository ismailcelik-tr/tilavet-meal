from collections.abc import Iterator

__all__ = ["sliding_windows"]


def sliding_windows(n_samples: int, sample_rate: int, hop_s: float, window_s: float) -> Iterator[tuple[float, slice]]:
    """Simulate live input: every hop, the last `window_s` seconds heard so far."""
    hop = round(hop_s * sample_rate)
    window = round(window_s * sample_rate)

    for end in range(hop, n_samples + 1, hop):
        yield end / sample_rate, slice(max(0, end - window), end)
