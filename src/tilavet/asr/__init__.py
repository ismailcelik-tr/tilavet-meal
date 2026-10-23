"""Speech recognizers behind one interface.

Each model family lives in its own uv dependency group; imports are lazy so a
run only needs the group of the model it loads.
"""

from collections.abc import Callable
from dataclasses import dataclass

from tilavet.asr.base import Recognizer

__all__ = ["MODELS", "ModelSpec", "Recognizer", "load"]


@dataclass(frozen=True)
class ModelSpec:
    group: str  # uv dependency group
    license: str
    factory: Callable[[], Recognizer]


def _tiny() -> Recognizer:
    from tilavet.asr.sherpa import QuranAsrTiny

    return QuranAsrTiny()


def _nemo(decoder: str) -> Callable[[], Recognizer]:
    def factory() -> Recognizer:
        from tilavet.asr.nemo import NemoHybrid

        return NemoHybrid(decoder)

    return factory


def _mlx(repo: str) -> Callable[[], Recognizer]:
    def factory() -> Recognizer:
        from tilavet.asr.whisper import MlxWhisper

        return MlxWhisper(repo)

    return factory


def _hf(model_id: str, language: str | None) -> Callable[[], Recognizer]:
    def factory() -> Recognizer:
        from tilavet.asr.whisper import HfWhisper

        return HfWhisper(model_id, language)

    return factory


MODELS: dict[str, ModelSpec] = {
    "quran-asr-tiny": ModelSpec("onnx", "MIT", _tiny),
    "nvidia-fc-ctc": ModelSpec("nemo", "CC-BY-4.0", _nemo("ctc")),
    "nvidia-fc-rnnt": ModelSpec("nemo", "CC-BY-4.0", _nemo("rnnt")),
    "tarteel-whisper-base": ModelSpec("hf", "Apache-2.0", _hf("tarteel-ai/whisper-base-ar-quran", language=None)),  # Arabic-only fine-tune; its generation config predates `language`
    "whisper-large-v3-turbo": ModelSpec("mlx", "MIT", _mlx("mlx-community/whisper-large-v3-turbo")),
}


def load(name: str) -> Recognizer:
    return MODELS[name].factory()
