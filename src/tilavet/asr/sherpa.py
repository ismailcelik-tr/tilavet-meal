import json

import numpy as np
import sherpa_onnx
from huggingface_hub import hf_hub_download

from tilavet.audio import SAMPLE_RATE

__all__ = ["QuranAsrTiny"]

_REPO = "Abdou/quran-asr-tiny"
_WORD_BOUNDARY = "▁"
_THREADS = 4


class QuranAsrTiny:
    """Zipformer CTC, 16M params, int8 ONNX. Writes Uthmani rasm; spelling.json maps to standard spelling."""

    def __init__(self) -> None:
        self._recognizer = sherpa_onnx.OfflineRecognizer.from_zipformer_ctc(
            model=hf_hub_download(_REPO, "model.int8.onnx"),
            tokens=hf_hub_download(_REPO, "tokens.txt"),
            num_threads=_THREADS,
        )
        with open(hf_hub_download(_REPO, "spelling.json"), encoding="utf-8") as f:
            self._spelling = json.load(f)

    def transcribe(self, audio: np.ndarray) -> str:
        stream = self._recognizer.create_stream()
        stream.accept_waveform(SAMPLE_RATE, audio)
        self._recognizer.decode_stream(stream)

        words = stream.result.text.replace(_WORD_BOUNDARY, " ").split()
        return " ".join(self._spelling.get(w, w) for w in words)
