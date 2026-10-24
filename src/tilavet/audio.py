import subprocess
from pathlib import Path

import numpy as np

__all__ = ["SAMPLE_RATE", "load_audio"]

SAMPLE_RATE = 16_000


def load_audio(
    path: Path, start_s: float | None = None, end_s: float | None = None, sample_rate: int = SAMPLE_RATE
) -> np.ndarray:
    """Decode any ffmpeg-readable file to mono float32 in [-1, 1] (16 kHz unless asked)."""
    if not Path(path).exists():
        raise FileNotFoundError(path)

    command = ["ffmpeg", "-nostdin", "-loglevel", "error"]
    if start_s is not None:
        command += ["-ss", f"{start_s:.3f}"]
    if end_s is not None:
        command += ["-to", f"{end_s:.3f}"]
    command += ["-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sample_rate), "-"]

    raw = subprocess.run(command, check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()
