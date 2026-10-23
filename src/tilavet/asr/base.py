from typing import Protocol

import numpy as np

__all__ = ["Recognizer"]


class Recognizer(Protocol):
    def transcribe(self, audio: np.ndarray) -> str:
        """16 kHz mono float32 in, Arabic text out (unnormalized)."""
        ...
