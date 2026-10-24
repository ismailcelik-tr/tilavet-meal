"""The iPhone listens while the MacBook speaker plays the M4 live-session streams; score the device run.

    uv run --group audio python scripts/device_loopback.py --volume 50
    uv run --group audio python scripts/device_loopback.py --volume 50 --repeat 2   # battery: longer run

The app runs muted (meals logged, not played) so nothing feeds back into its microphone; headphone
latency is measured separately. One engine session spans all streams: a passage switch is a reciter change.
"""

import argparse
import json
import statistics
import subprocess
import time
from pathlib import Path

import numpy as np

from device import launch, pull
from loopback import SPEAKER, _set_volume, _volume
from tilavet.audio import SAMPLE_RATE, load_audio
from tilavet.corpus import AyahRef, load_tanzil, meal_units
from tilavet.eval import Emission, Segment, estimate_offset, score_stream
from tilavet.live.devices import default_output, play

ROOT = Path(__file__).resolve().parents[1]
STREAMS = ROOT / "data" / "derived" / "streams"
OUT = ROOT / "data" / "derived" / "m6"
REPORT = ROOT / "reports" / "m6-device.md"
STREAM_IDS = ("abdulbaset-mujawwad-1", "abdulbaset-mujawwad-4", "hani-rifai-3", "hani-rifai-4", "minshawi-0",
              "minshawi-1", "sudais-0", "sudais-4")
LEAD_S = 10.0
GAP_S = 5.0
START_DELAY_S = 8.0  # app load (index, model) before the Mac starts playing
TAIL_S = 20.0
MAX_LAG_S = 60.0
ALIGN_S = 300.0
THREADS = 2
HOP_S = 1.0


def _session(repeat: int) -> tuple[np.ndarray, list[Segment]]:
    chunks = [np.zeros(round(LEAD_S * SAMPLE_RATE), dtype=np.float32)]
    truth: list[Segment] = []
    cursor = LEAD_S
    for stream_id in STREAM_IDS * repeat:
        audio = load_audio(STREAMS / f"{stream_id}.wav")
        meta = json.loads((STREAMS / f"{stream_id}.json").read_text())
        truth += [Segment(AyahRef(*s["ref"]) if s["ref"] else None, cursor + s["start"], cursor + s["end"])
                  for s in meta["segments"]]
        chunks += [audio, np.zeros(round(GAP_S * SAMPLE_RATE), dtype=np.float32)]
        cursor += (len(audio) + round(GAP_S * SAMPLE_RATE)) / SAMPLE_RATE
    return np.concatenate(chunks), truth


def _pct(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q / 100 * len(ordered)))]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, required=True)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--label", default="loopback")
    args = parser.parse_args()

    if default_output() != SPEAKER:
        raise SystemExit(f"default output must be {SPEAKER!r} (volume is set on it)")

    audio, truth = _session(args.repeat)
    duration = len(audio) / SAMPLE_RATE
    print(f"session {duration / 60:.1f} min")

    previous = _volume()
    _set_volume(args.volume)
    try:
        launch(["--autostart", "--mute", "--threads", str(THREADS), "--duration",
                str(round(START_DELAY_S + duration + TAIL_S))])
        time.sleep(START_DELAY_S)
        caffeinate = subprocess.Popen(["caffeinate", "-i", "-t", str(round(duration + TAIL_S))])
        play(audio, SPEAKER)
        caffeinate.wait()
    finally:
        _set_volume(previous)

    run = pull("latest.txt", OUT).read_text().strip()
    folder = OUT / args.label
    pull(f"{run}/done", folder, wait=True)
    for name in ("mic.f32", "live.jsonl", "metrics.jsonl"):
        pull(f"{run}/{name}", folder)

    recording = np.fromfile(folder / "mic.f32", dtype="<f4")
    # The first minutes are enough: the offset is constant and a full-length FFT needs gigabytes.
    head = round(ALIGN_S * SAMPLE_RATE)
    offset = estimate_offset(audio[:head], recording[: head + round(MAX_LAG_S * SAMPLE_RATE)], SAMPLE_RATE, MAX_LAG_S)
    shifted = [Segment(s.ref, s.start + offset, s.end + offset) for s in truth]
    records = [json.loads(line) for line in (folder / "live.jsonl").read_text().splitlines()]
    metrics = [json.loads(line) for line in (folder / "metrics.jsonl").read_text().splitlines()]

    units = meal_units(load_tanzil(ROOT / "data" / "raw" / "tr.diyanet.txt"))
    unit_of = {ref: (u.sura, u.first) for u in units for ref in u.refs}
    plays = [Emission(r["t"], (r["unit"][0], r["unit"][1])) for r in records if r["type"] == "Play"]
    result = score_stream(shifted, plays, unit_of)
    windows = [r for r in records if r["type"] == "Window"]
    compute = [w["compute_s"] for w in windows]
    battery = [m["battery"] for m in metrics if m["battery"] >= 0]
    hours = (metrics[-1]["t"] - metrics[0]["t"]) / 3600

    summary = {
        "label": args.label, "minutes": round(duration / 60, 1), "offset_s": round(offset, 3),
        "plays": result.emissions, "wrong": result.wrong, "late": result.late,
        "recall": f"{result.recalled}/{result.occurrences}",
        "from_start_p50_p90": [round(_pct(result.latency_from_start, q), 2) for q in (50, 90)],
        "from_end_p50_p90": [round(_pct(result.latency_from_end, q), 2) for q in (50, 90)],
        "asr_s_p50_p90": [round(_pct(compute, q), 3) for q in (50, 90)],
        "rtf_p90": round(_pct(compute, 90) / HOP_S, 3),
        "skipped_hops": sum(w["skipped"] for w in windows),
        "memory_mb_max": round(max(m["memory_mb"] for m in metrics)),
        "cpu_percent_median": round(statistics.median(m["cpu_percent"] for m in metrics)),
        "thermal": sorted({m["thermal"] for m in metrics}),
        "battery_start_end": [battery[0], battery[-1]] if battery else None,
        "battery_percent_per_hour": round(100 * (battery[0] - battery[-1]) / hours, 1) if battery and hours else None,
    }
    (folder / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
