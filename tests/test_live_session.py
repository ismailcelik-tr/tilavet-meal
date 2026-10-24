import numpy as np

from tilavet.audio import SAMPLE_RATE
from tilavet.corpus import AyahRef, MealUnit, normalize
from tilavet.engine import AyahConfirmed, Mode
from tilavet.live import LiveSession, MealPlayer, Started, Window
from tilavet.policy import EmissionPolicy, Play

TEXT = "قل أعوذ برب الناس"
UNIT = MealUnit(114, 1, 1, "a")


class FakeRecognizer:
    def __init__(self) -> None:
        self.lengths: list[int] = []

    def transcribe(self, audio: np.ndarray) -> str:
        self.lengths.append(len(audio))
        return TEXT


class FakeEngine:
    def __init__(self, events=()) -> None:
        self.fed: list[tuple[float, list[str]]] = []
        self._events = list(events)

    def feed(self, t, words):
        self.fed.append((t, list(words)))
        return self._events


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


def seconds(s: float) -> np.ndarray:
    return np.zeros(round(s * SAMPLE_RATE), dtype=np.float32)


def session(engine=None, clock=None, recognizer=None):
    return LiveSession(
        recognizer or FakeRecognizer(),
        engine or FakeEngine(),
        EmissionPolicy([UNIT], cooldown_s=300),
        MealPlayer(lambda unit: 5.0, max_wait_s=15),
        clock or Clock(),
        hop_s=1.0,
        window_s=12.0,
    )


def test_window_closes_every_hop_with_compute_in_time():
    clock, engine = Clock(), FakeEngine()
    s = session(engine, clock)

    assert s.feed(seconds(0.5), arrived_at=10.0) == []
    clock.now = 10.75
    assert s.feed(seconds(0.5), arrived_at=10.5) == [Window(1.0, 1.25, TEXT, skipped=0)]
    assert engine.fed == [(1.25, normalize(TEXT).split())]


def test_backlog_transcribes_latest_window_only():
    recognizer = FakeRecognizer()
    s = session(recognizer=recognizer)

    [window] = s.feed(seconds(3.0), arrived_at=0.0)

    assert window.skipped == 2
    assert recognizer.lengths == [3 * SAMPLE_RATE]


def test_window_keeps_last_12_seconds():
    recognizer = FakeRecognizer()
    s = session(recognizer=recognizer)

    for _ in range(13):
        s.feed(seconds(1.0), arrived_at=0.0)

    assert recognizer.lengths[-1] == 12 * SAMPLE_RATE


def test_confirmed_ayah_reaches_player():
    clock = Clock()
    clock.now = 0.25
    confirmed = AyahConfirmed(1.25, AyahRef(114, 1), Mode.TRACK, score=6)
    s = session(FakeEngine([confirmed]), clock)

    records = s.feed(seconds(1.0), arrived_at=0.0)

    play = Play(1.25, UNIT, AyahRef(114, 1))
    assert records == [Window(1.0, 1.25, TEXT, skipped=0), confirmed, play, Started(1.25, play)]
