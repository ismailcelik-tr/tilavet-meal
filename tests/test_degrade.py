import numpy as np
import pytest

from tilavet.audio import SAMPLE_RATE
from tilavet.eval import degrade


@pytest.fixture
def tone() -> np.ndarray:
    t = np.arange(2 * SAMPLE_RATE) / SAMPLE_RATE
    return (0.3 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)


def test_degrade_keeps_length_and_type(tone):
    result = degrade(tone, snr_db=10, seed=1)

    assert result.dtype == np.float32
    assert len(result) == len(tone)


def test_degrade_is_deterministic(tone):
    assert np.array_equal(degrade(tone, snr_db=10, seed=1), degrade(tone, snr_db=10, seed=1))


def test_degrade_adds_noise_at_requested_snr(tone):
    result = degrade(tone, snr_db=10, seed=1)
    clean = degrade(tone, snr_db=None, seed=1)

    noise = result - clean
    snr = 10 * np.log10(np.mean(clean**2) / np.mean(noise**2))
    assert snr == pytest.approx(10, abs=0.5)


def test_degrade_removes_low_frequencies():
    t = np.arange(2 * SAMPLE_RATE) / SAMPLE_RATE
    hum = (0.3 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)

    filtered = degrade(hum, snr_db=None, seed=1)

    assert np.sqrt(np.mean(filtered**2)) < 0.1 * np.sqrt(np.mean(hum**2))
