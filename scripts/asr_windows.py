"""Run one recognizer over every stream as if live; cache window hypotheses.

    uv run --group <group> python scripts/asr_windows.py --model <name> --condition clean|noisy|hard [--set blind]

Per stream writes <id>.windows.jsonl (t, text, compute_s) and <id>.clips.jsonl
(each truth ayah transcribed on its own, to measure the condition's CER).
Engine replay (scripts/replay_m3.py) then needs no ASR.
"""

import argparse
import json
import time
import wave
import zlib
from pathlib import Path

import numpy as np

from tilavet.asr import MODELS, load
from tilavet.audio import SAMPLE_RATE
from tilavet.corpus import AyahRef, load_tanzil
from tilavet.eval import degrade
from tilavet.stream import sliding_windows

ROOT = Path(__file__).resolve().parents[1]
SETS = {
    "main": (ROOT / "data" / "derived" / "streams", ROOT / "data" / "derived" / "m3" / "asr"),
    "blind": (ROOT / "data" / "derived" / "streams-blind", ROOT / "data" / "derived" / "m4" / "asr-blind"),
}
QURAN = ROOT / "data" / "raw" / "quran-simple-clean.txt"

HOP_S = 1.0
WINDOW_S = 12.0
SNR_DB = {"clean": None, "noisy": 10.0, "hard": 0.0}  # noisy/hard also get the phone/room filter
SILENCE_RMS = 1e-3  # about -60 dBFS; skip ASR on digital silence
INT16_SCALE = 32768.0


def _read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / INT16_SCALE


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=sorted(MODELS))
    parser.add_argument("--condition", required=True, choices=sorted(SNR_DB))
    parser.add_argument("--set", default="main", choices=sorted(SETS))
    args = parser.parse_args()

    streams, cache = SETS[args.set]

    quran = load_tanzil(QURAN)
    recognizer = load(args.model)
    out = cache / args.model / args.condition
    out.mkdir(parents=True, exist_ok=True)

    for meta_path in sorted(streams.glob("*.json")):
        meta = json.loads(meta_path.read_text())
        # Clips are written last, so their presence marks a finished stream (resume after interruption).
        if (out / f"{meta['id']}.clips.jsonl").exists():
            continue

        audio = _read_wav(streams / f"{meta['id']}.wav")
        if args.condition != "clean":
            audio = degrade(audio, SNR_DB[args.condition], seed=zlib.crc32(meta["id"].encode()))

        windows = []
        for t, span in sliding_windows(len(audio), SAMPLE_RATE, HOP_S, WINDOW_S):
            chunk = audio[span]
            started = time.perf_counter()
            text = recognizer.transcribe(chunk) if np.sqrt(np.mean(chunk**2)) >= SILENCE_RMS else ""
            windows.append({"t": t, "text": text, "compute_s": round(time.perf_counter() - started, 4)})

        clips = []
        for segment in meta["segments"]:
            if segment["ref"] is None:
                continue
            chunk = audio[round(segment["start"] * SAMPLE_RATE) : round(segment["end"] * SAMPLE_RATE)]
            clips.append({"ref": segment["ref"], "text": recognizer.transcribe(chunk),
                          "reference": quran[AyahRef(*segment["ref"])]})

        (out / f"{meta['id']}.windows.jsonl").write_text("".join(json.dumps(w, ensure_ascii=False) + "\n" for w in windows))
        (out / f"{meta['id']}.clips.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in clips))
        print(f"{meta['id']}: {len(windows)} windows, compute p50 {np.median([w['compute_s'] for w in windows]):.3f} s")


if __name__ == "__main__":
    main()
