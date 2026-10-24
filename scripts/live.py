"""Listen with the MacBook microphone; play the meal of what is recited to headphones.

    uv run --group onnx --group audio python scripts/live.py --output "CMF Buds 2a"

Ctrl+C stops. Writes data/derived/m4/live/<start time>.wav (microphone) and
.live.jsonl (windows, engine events, plays, player events, playback starts) for review.
Meals start on window hops, so a queued meal may wait up to one hop after the previous ends.
"""

import argparse
import json
import queue
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from loopback import MICROPHONE, OUT as ROOM, POLL_S, Bench, jsonable, write_wav
from tilavet.audio import load_audio
from tilavet.engine import Lost
from tilavet.live import LiveSession, Record, Started
from tilavet.live.devices import Microphone, outputs, start_playback

OUT = ROOM.parent / "live"
MEALS = ROOM.parents[1] / "meals" / "tr.diyanet-yelda"
MEAL_RATE = 22_050  # `say` renders Yelda at this rate


def _show(record: Record, started_at: float) -> None:
    clock = time.strftime("%M:%S", time.gmtime(time.monotonic() - started_at))
    if isinstance(record, Lost):
        print(f"{clock}  (takip kaybedildi)")
        return

    unit = record.play.unit
    span = f"{unit.sura}:{unit.first}" if unit.first == unit.last else f"{unit.sura}:{unit.first}-{unit.last}"
    print(f"{clock}  [{span}] {unit.text}")
    if unit.first != unit.last:
        print(f"       ({span} birbirine bağlı olduğu için birlikte çevrilmiştir.)")


def _pump(mic: Microphone, session: LiveSession, device: str, recorded: list[np.ndarray], log: list[dict],
          stop: threading.Event, started_at: float) -> None:
    while not (stop.is_set() and mic.chunks.empty()):
        try:
            batch = [mic.chunks.get(timeout=POLL_S)]
        except queue.Empty:
            continue

        while not mic.chunks.empty():
            batch.append(mic.chunks.get_nowait())

        samples = np.concatenate([chunk for chunk, _ in batch])
        recorded.append(samples)
        for record in session.feed(samples, arrived_at=batch[-1][1]):
            log.append(jsonable(record))
            if isinstance(record, Lost):
                _show(record, started_at)
            if not isinstance(record, Started):
                continue

            unit = record.play.unit
            start_playback(load_audio(MEALS / f"{unit.sura}-{unit.first}.m4a", sample_rate=MEAL_RATE), MEAL_RATE, device)
            log.append({"type": "Playback", "unit": [unit.sura, unit.first], "wall_s": time.monotonic() - started_at})
            _show(record, started_at)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="headphone device name")
    parser.add_argument("--model", default="quran-asr-tiny")
    args = parser.parse_args()

    if args.output not in outputs():
        raise SystemExit(f"no output named {args.output!r}; available: {outputs()}")

    bench = Bench(args.model)
    session, _ = bench.session()
    OUT.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime("%Y%m%d-%H%M%S")
    recorded: list[np.ndarray] = []
    log: list[dict] = []
    stop = threading.Event()

    print("Dinliyorum. Durdurmak için Ctrl+C.")
    with Microphone(MICROPHONE) as mic:
        started_at = time.monotonic()
        worker = threading.Thread(target=_pump, args=(mic, session, args.output, recorded, log, stop, started_at))
        worker.start()
        try:
            while worker.is_alive():
                worker.join(timeout=POLL_S)
        except KeyboardInterrupt:
            stop.set()
            worker.join()

        # Save before closing the stream: CoreAudio once hung in stop for minutes, holding the data in memory.
        write_wav(OUT / f"{name}.wav", np.concatenate(recorded) if recorded else np.zeros(0, dtype=np.float32))
        (OUT / f"{name}.live.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in log))
        print(f"kaydedildi: {OUT / name}.{{wav,live.jsonl}}, overflows {mic.overflows}")


if __name__ == "__main__":
    main()
