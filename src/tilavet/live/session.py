"""Live pipeline over microphone chunks: window -> ASR -> engine -> policy -> player. Pure; time is passed in."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from tilavet.asr import Recognizer
from tilavet.audio import SAMPLE_RATE
from tilavet.corpus import normalize
from tilavet.engine import Event
from tilavet.live.player import MealPlayer, PlayerEvent
from tilavet.policy import EmissionPolicy, Play

__all__ = ["LiveSession", "Record", "Window"]


class Engine(Protocol):
    def feed(self, t: float, words: Sequence[str]) -> list[Event]: ...


@dataclass(frozen=True)
class Window:
    heard_s: float  # audio heard when the window closed
    t: float  # decision time: heard_s + queueing + compute
    text: str
    skipped: int  # hops dropped because ASR fell behind


Record = Window | Event | Play | PlayerEvent


class LiveSession:
    def __init__(
        self,
        recognizer: Recognizer,
        engine: Engine,
        policy: EmissionPolicy,
        player: MealPlayer,
        clock: Callable[[], float],
        hop_s: float,
        window_s: float,
    ) -> None:
        self._recognizer = recognizer
        self._engine = engine
        self._policy = policy
        self._player = player
        self._clock = clock
        self._hop = round(hop_s * SAMPLE_RATE)
        self._window = round(window_s * SAMPLE_RATE)
        self._buffer = np.zeros(0, dtype=np.float32)
        self._heard = 0
        self._next_hop = self._hop

    def feed(self, samples: np.ndarray, arrived_at: float) -> list[Record]:
        """`arrived_at`: clock time when the last of `samples` was captured."""
        self._buffer = np.concatenate([self._buffer, samples])[-self._window :]
        self._heard += len(samples)
        if self._heard < self._next_hop:
            return []

        hops = (self._heard - self._next_hop) // self._hop + 1
        self._next_hop += hops * self._hop
        heard_s = self._heard / SAMPLE_RATE

        text = self._recognizer.transcribe(self._buffer)
        t = heard_s + self._clock() - arrived_at
        records: list[Record] = [Window(heard_s, t, text, hops - 1)]

        for event in self._engine.feed(t, normalize(text).split()):
            records.append(event)
            play = self._policy.on(event)
            if play:
                records.append(play)
                records.extend(self._player.submit(play))

        records.extend(self._player.advance(t))
        return records
