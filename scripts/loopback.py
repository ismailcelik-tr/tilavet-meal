"""Play streams through the speaker, record the microphone, run the live pipeline on it.

    uv run --group onnx --group audio python scripts/loopback.py --streams shuraim-2 --volume 50

Per stream writes data/derived/m4/room/<id>.wav (microphone), <id>.live.jsonl
(windows, engine events, plays, player events) and <id>.json (summary).
Meal audio is not played: the speaker is the recitation source and the mic would hear it.
"""

import argparse
import csv
import dataclasses
import json
import os
import queue
import subprocess
import threading
import time
import wave
from enum import Enum
from pathlib import Path

import numpy as np

from tilavet.asr import Recognizer, load
from tilavet.audio import SAMPLE_RATE, load_audio
from tilavet.corpus import AyahRef, load_tanzil, meal_units, normalize, strip_basmala
from tilavet.engine import PositionEngine, QuranIndex
from tilavet.eval import Emission, Segment, estimate_offset, score, score_stream
from tilavet.live import LiveSession, MealPlayer, Record, Skipped, Started, Window
from tilavet.live.devices import Microphone, default_output, play
from tilavet.policy import EmissionPolicy, Play

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
STREAMS = DERIVED / "streams"
OUT = DERIVED / "m4" / "room"
DURATIONS = DERIVED / "meal-durations-tr.diyanet-yelda.csv"

SPEAKER = "MacBook Pro Hoparlörü"
MICROPHONE = "MacBook Pro Mikrofonu"
LEAD_S = 10.0  # room noise before playback: noise floor for SNR
TAIL_S = 5.0
HOP_S = 1.0
WINDOW_S = 12.0
COOLDOWN_S = 300.0
MAX_WAIT_S = 15.0
POLL_S = 0.1
INT16_MAX = 32767


class Bench:
    def __init__(self, model: str) -> None:
        self.quran = load_tanzil(RAW / "quran-simple-clean.txt")
        self.index = QuranIndex.build(
            {ref: normalize(strip_basmala(ref, text)).split() for ref, text in self.quran.items()}
        )
        self.units = meal_units(load_tanzil(RAW / "tr.diyanet.txt"))
        self.unit_of = {ref: (u.sura, u.first) for u in self.units for ref in u.refs}
        with DURATIONS.open() as f:
            self.duration_s = {(int(r["sura"]), int(r["first"])): float(r["seconds"]) for r in csv.DictReader(f)}
        self.recognizer: Recognizer = load(model)

    def session(self) -> tuple[LiveSession, MealPlayer]:
        player = MealPlayer(lambda unit: self.duration_s[(unit.sura, unit.first)], MAX_WAIT_S)
        session = LiveSession(
            self.recognizer,
            PositionEngine(self.index),
            EmissionPolicy(self.units, COOLDOWN_S),
            player,
            time.monotonic,
            HOP_S,
            WINDOW_S,
        )
        return session, player


def _pump(mic: Microphone, session: LiveSession, recorded: list[np.ndarray], records: list[Record],
          stop: threading.Event) -> None:
    """Drain all pending chunks, then feed them at once: a late ASR skips to the newest window."""
    while not (stop.is_set() and mic.chunks.empty()):
        try:
            batch = [mic.chunks.get(timeout=POLL_S)]
        except queue.Empty:
            continue

        while not mic.chunks.empty():
            batch.append(mic.chunks.get_nowait())

        samples = np.concatenate([chunk for chunk, _ in batch])
        recorded.append(samples)
        records.extend(session.feed(samples, arrived_at=batch[-1][1]))


def _record(bench: Bench, reference: np.ndarray) -> tuple[np.ndarray, list[Record], int, MealPlayer]:
    session, player = bench.session()
    recorded: list[np.ndarray] = []
    records: list[Record] = []
    stop = threading.Event()

    with Microphone(MICROPHONE) as mic:
        worker = threading.Thread(target=_pump, args=(mic, session, recorded, records, stop))
        worker.start()
        time.sleep(LEAD_S)
        play(reference, SPEAKER)
        time.sleep(TAIL_S)
        stop.set()
        worker.join()

    return np.concatenate(recorded), records, mic.overflows, player


def _jsonable(record: Record) -> dict:
    return {"type": type(record).__name__, **json.loads(json.dumps(dataclasses.asdict(record), default=str))}


def _db(power: float) -> float:
    return 10 * np.log10(max(power, 1e-12))


def _summary(bench: Bench, meta: dict, recording: np.ndarray, records: list[Record], overflows: int,
             player: MealPlayer, offset: float) -> dict:
    truth = [Segment(AyahRef(*s["ref"]) if s["ref"] else None, s["start"] + offset, s["end"] + offset)
             for s in meta["segments"]]
    speech = [recording[round(s.start * SAMPLE_RATE) : round(s.end * SAMPLE_RATE)] for s in truth if s.ref]

    noise_power = float(np.mean(recording[: round((LEAD_S - 1) * SAMPLE_RATE)] ** 2))
    speech_power = float(np.mean(np.concatenate(speech) ** 2))

    end = recording.size / SAMPLE_RATE
    player_events = records + player.advance(end + max(bench.duration_s.values()))
    plays = [r for r in records if isinstance(r, Play)]
    started = [r for r in player_events if isinstance(r, Started)]
    result = score_stream(truth, [Emission(p.t, (p.unit.sura, p.unit.first)) for p in plays], bench.unit_of)

    hyps = [bench.recognizer.transcribe(chunk) for chunk in speech]
    refs = [bench.quran[s.ref] for s in truth if s.ref]

    return {
        "id": meta["id"],
        "offset_s": offset,
        "peak_dbfs": 20 * np.log10(max(float(np.max(np.abs(recording))), 1e-12)),
        "noise_dbfs": _db(noise_power),
        "snr_db": _db(speech_power - noise_power) - _db(noise_power),
        "overflows": overflows,
        "skipped_hops": sum(r.skipped for r in records if isinstance(r, Window)),
        "plays": result.emissions,
        "wrong": result.wrong,
        "late": result.late,
        "recalled": f"{result.recalled}/{result.occurrences}",
        "from_start_p50_s": float(np.median(result.latency_from_start)) if result.latency_from_start else None,
        "player_wait_max_s": max((s.t - s.play.t for s in started), default=0.0),
        "player_skips": sum(isinstance(r, Skipped) for r in player_events),
        "room_cer": score(refs, hyps).cer,
    }


def _write_wav(path: Path, audio: np.ndarray) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes((np.clip(audio, -1, 1) * INT16_MAX).astype(np.int16).tobytes())


def _volume() -> int:
    return int(subprocess.run(["osascript", "-e", "output volume of (get volume settings)"],
                              check=True, capture_output=True, text=True).stdout)


def _set_volume(level: int) -> None:
    subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)


class Outcome(Enum):
    DONE = "done"
    SKIPPED = "skipped"


def run_stream(bench: Bench, meta: dict) -> Outcome:
    summary_path = OUT / f"{meta['id']}.json"
    if summary_path.exists():
        return Outcome.SKIPPED

    reference = load_audio(STREAMS / f"{meta['id']}.wav")
    recording, records, overflows, player = _record(bench, reference)
    if not np.any(recording):
        raise SystemExit("microphone returned only zeros: grant microphone access to the terminal app")

    offset = estimate_offset(reference, recording, SAMPLE_RATE, LEAD_S + 1)
    summary = _summary(bench, meta, recording, records, overflows, player, offset)

    _write_wav(OUT / f"{meta['id']}.wav", recording)
    (OUT / f"{meta['id']}.live.jsonl").write_text("".join(json.dumps(_jsonable(r), ensure_ascii=False) + "\n"
                                                          for r in records))
    summary_path.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return Outcome.DONE


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--streams", nargs="+", required=True, help="stream ids, e.g. shuraim-2")
    parser.add_argument("--volume", type=int, required=True, help="system output volume 0-100 during playback")
    parser.add_argument("--model", default="quran-asr-tiny")
    args = parser.parse_args()

    # osascript sets the default device's volume; it must be the speaker we play through.
    if default_output() != SPEAKER:
        raise SystemExit(f"set system output to {SPEAKER!r} (now {default_output()!r})")

    bench = Bench(args.model)
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])

    previous = _volume()
    _set_volume(args.volume)
    try:
        for stream_id in args.streams:
            meta = json.loads((STREAMS / f"{stream_id}.json").read_text())
            print(f"{stream_id}: {run_stream(bench, meta).value}")
    finally:
        _set_volume(previous)


if __name__ == "__main__":
    main()
