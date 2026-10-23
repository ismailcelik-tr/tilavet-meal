"""Phone/room proxy for test audio: telephone band, short echoes, white noise."""

import subprocess

import numpy as np

from tilavet.audio import SAMPLE_RATE

__all__ = ["degrade"]

# 300-3400 Hz: narrowband telephone channel. Echo taps approximate a small hall.
_FILTERS = "highpass=f=300:poles=2,highpass=f=300:poles=2,lowpass=f=3400,aecho=0.8:0.7:40|90:0.3|0.2"


def degrade(audio: np.ndarray, snr_db: float | None, seed: int) -> np.ndarray:
    """Filter, then add white noise at `snr_db` relative to the filtered signal (None = no noise)."""
    filtered = subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "1",
         "-i", "-", "-af", _FILTERS, "-f", "f32le", "-"],
        input=audio.astype(np.float32).tobytes(),
        check=True,
        capture_output=True,
    ).stdout
    result = np.frombuffer(filtered, dtype=np.float32)[: len(audio)].copy()
    result = np.pad(result, (0, len(audio) - len(result)))

    if snr_db is None:
        return result

    signal_power = float(np.mean(result**2))
    noise = np.random.default_rng(seed).standard_normal(len(result)).astype(np.float32)
    noise *= np.sqrt(signal_power / 10 ** (snr_db / 10))
    return (result + noise).astype(np.float32)
