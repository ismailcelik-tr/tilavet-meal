"""Where a played signal starts inside its recording (speaker -> microphone latency)."""

import numpy as np

__all__ = ["estimate_offset"]


def estimate_offset(reference: np.ndarray, recording: np.ndarray, sample_rate: int, max_lag_s: float) -> float:
    """Lag in [0, max_lag_s] seconds that best aligns `reference` with `recording` (FFT cross-correlation)."""
    size = 1 << (len(reference) + len(recording) - 1).bit_length()
    spectrum = np.fft.rfft(recording, size) * np.conj(np.fft.rfft(reference, size))
    correlation = np.fft.irfft(spectrum, size)[: round(max_lag_s * sample_rate) + 1]
    return int(np.argmax(correlation)) / sample_rate
