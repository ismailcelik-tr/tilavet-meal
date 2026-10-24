import numpy as np

from tilavet.eval import estimate_offset

RATE = 16_000


def test_finds_delay_of_attenuated_noisy_copy():
    rng = np.random.default_rng(0)
    reference = rng.standard_normal(3 * RATE).astype(np.float32)
    delay = round(0.25 * RATE)
    recording = np.concatenate([np.zeros(delay), 0.3 * reference, np.zeros(RATE)]).astype(np.float32)
    recording += 0.1 * rng.standard_normal(len(recording)).astype(np.float32)

    assert estimate_offset(reference, recording, RATE, max_lag_s=1.0) == delay / RATE


def test_ignores_lags_beyond_limit():
    rng = np.random.default_rng(1)
    reference = rng.standard_normal(RATE).astype(np.float32)
    recording = np.concatenate([np.zeros(2 * RATE), reference]).astype(np.float32)

    assert estimate_offset(reference, recording, RATE, max_lag_s=1.0) <= 1.0
