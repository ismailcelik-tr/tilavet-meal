import numpy as np

from tilavet.audio import SAMPLE_RATE

__all__ = ["HfWhisper", "MlxWhisper"]

_LANGUAGE = "ar"
_WINDOW_S = 30  # Whisper input window


class MlxWhisper:
    """Whisper on Apple MLX (GPU). Greedy, no conditioning on previous text."""

    def __init__(self, repo: str) -> None:
        import mlx_whisper

        self._transcribe = mlx_whisper.transcribe
        self._repo = repo

    def transcribe(self, audio: np.ndarray) -> str:
        result = self._transcribe(
            audio,
            path_or_hf_repo=self._repo,
            language=_LANGUAGE,
            temperature=0.0,
            condition_on_previous_text=False,
        )
        return result["text"]


class HfWhisper:
    """Whisper checkpoint via transformers (for fine-tunes without an MLX conversion)."""

    def __init__(self, model_id: str, language: str | None) -> None:
        import torch
        from transformers import pipeline

        device = "mps" if torch.backends.mps.is_available() else "cpu"
        # Chunked mode: long-form generation needs timestamp tokens old fine-tunes lack.
        self._pipe = pipeline(
            "automatic-speech-recognition", model=model_id, device=device, chunk_length_s=_WINDOW_S
        )
        self._generate = {"language": language, "task": "transcribe"} if language else {}

    def transcribe(self, audio: np.ndarray) -> str:
        result = self._pipe({"raw": audio, "sampling_rate": SAMPLE_RATE}, generate_kwargs=self._generate)
        return result["text"]
