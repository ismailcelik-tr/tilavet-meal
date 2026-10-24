"""sounddevice adapters. Devices are picked by name, never by system default."""

import queue
import time
import unicodedata
from enum import Enum

import numpy as np
import sounddevice as sd

from tilavet.audio import SAMPLE_RATE

__all__ = ["Kind", "Microphone", "default_output", "find_device", "outputs", "play"]


class Kind(Enum):
    INPUT = "input"
    OUTPUT = "output"


def _nfc(name: str) -> str:
    # CoreAudio may report "Hoparlörü" decomposed (o + combining diaeresis).
    return unicodedata.normalize("NFC", name)


def find_device(name: str, kind: Kind) -> int:
    for index, device in enumerate(sd.query_devices()):
        if _nfc(device["name"]) == _nfc(name) and device[f"max_{kind.value}_channels"] > 0:
            return index
    raise LookupError(f"no {kind.value} device named {name!r}")


def default_output() -> str:
    return _nfc(sd.query_devices(kind="output")["name"])


def outputs() -> list[str]:
    return [_nfc(d["name"]) for d in sd.query_devices() if d["max_output_channels"] > 0]


class Microphone:
    """16 kHz mono chunks stamped with arrival time; counts overflows (lost samples)."""

    def __init__(self, name: str) -> None:
        self.chunks: queue.Queue[tuple[np.ndarray, float]] = queue.Queue()
        self.overflows = 0
        self._stream = sd.InputStream(
            device=find_device(name, Kind.INPUT),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )

    def _callback(self, data: np.ndarray, frames: int, time_info: object, status: sd.CallbackFlags) -> None:
        if status.input_overflow:
            self.overflows += 1
        self.chunks.put((data[:, 0].copy(), time.monotonic()))

    def __enter__(self) -> "Microphone":
        self._stream.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stream.stop()
        self._stream.close()


def play(audio: np.ndarray, device: str) -> None:
    sd.play(audio, SAMPLE_RATE, device=find_device(device, Kind.OUTPUT), blocking=True)
