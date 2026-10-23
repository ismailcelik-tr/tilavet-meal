"""Transcribe an eval set with one model; record hypotheses, speed and memory.

    uv run --group <group> python scripts/bench_asr.py --model <name> --set <name>

One model per process so peak RSS is attributable. GPU (MLX/MPS) memory is not
included in RSS.
"""

import argparse
import json
import resource
import time
from pathlib import Path

from tilavet.asr import MODELS, load
from tilavet.audio import SAMPLE_RATE, load_audio

ROOT = Path(__file__).resolve().parents[1]
SETS = ROOT / "data" / "derived" / "sets"
RESULTS = ROOT / "data" / "derived" / "bench"

BYTES_PER_MB = 1024 * 1024


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(MODELS))
    parser.add_argument("--set", required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    rows = [json.loads(line) for line in (SETS / f"{args.set}.jsonl").read_text().splitlines()]
    rows = rows[: args.limit] if args.limit else rows
    clips = [load_audio(ROOT / r["audio"], r.get("start_s"), r.get("end_s")) for r in rows]

    started = time.perf_counter()
    recognizer = load(args.model)
    load_s = time.perf_counter() - started

    # Warm-up: first call pays lazy init (graph compile, kernel caches).
    recognizer.transcribe(clips[0])

    hyps = []
    for row, audio in zip(rows, clips, strict=True):
        started = time.perf_counter()
        text = recognizer.transcribe(audio)
        hyps.append({"id": row["id"], "text": text, "proc_s": time.perf_counter() - started,
                     "audio_s": len(audio) / SAMPLE_RATE})

    out = RESULTS / args.set
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{args.model}.jsonl").write_text("".join(json.dumps(h, ensure_ascii=False) + "\n" for h in hyps))

    audio_s = sum(h["audio_s"] for h in hyps)
    proc_s = sum(h["proc_s"] for h in hyps)
    summary = {
        "model": args.model,
        "set": args.set,
        "clips": len(hyps),
        "load_s": round(load_s, 2),
        "audio_s": round(audio_s, 1),
        "proc_s": round(proc_s, 1),
        "rtf": round(proc_s / audio_s, 4),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / BYTES_PER_MB),
    }
    (out / f"{args.model}.summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
