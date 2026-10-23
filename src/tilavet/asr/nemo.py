import numpy as np

__all__ = ["NemoHybrid"]

_MODEL_ID = "nvidia/stt_ar_fastconformer_hybrid_large_pcd_v1.0"


class NemoHybrid:
    """NVIDIA Arabic FastConformer (transducer + CTC heads). Output has diacritics and punctuation."""

    def __init__(self, decoder: str) -> None:
        import nemo.collections.asr as nemo_asr

        self._model = nemo_asr.models.ASRModel.from_pretrained(_MODEL_ID, map_location="cpu")
        self._model.change_decoding_strategy(decoder_type=decoder)
        self._model.eval()

    def transcribe(self, audio: np.ndarray) -> str:
        hypotheses = self._model.transcribe([audio], batch_size=1, verbose=False)
        return hypotheses[0].text
