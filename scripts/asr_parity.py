"""Same clips through Python and the iPhone app: is the ASR output identical?

    uv run --group onnx python scripts/asr_parity.py prepare   # clips -> app resources, Python reference
    uv run python scripts/asr_parity.py run                    # launch on device, pull, compare
"""

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np

from device import APP_DIR, launch, pull
from tilavet.audio import SAMPLE_RATE, load_audio
from tilavet.eval import score

ROOT = Path(__file__).resolve().parents[1]
STREAMS = ROOT / "data" / "derived" / "streams-blind2"
CLIPS = APP_DIR / "Data" / "parity"
OUT = ROOT / "data" / "derived" / "m6"
REFERENCE = OUT / "parity-python.json"
CLIP_COUNT = 50
SEED = 7
THREADS = "1,2,4"
FLOAT32 = 3  # WAVE_FORMAT_IEEE_FLOAT


def _write_float_wav(path: Path, audio: np.ndarray) -> None:
    """32-bit float, so both sides decode exactly the same samples."""
    data = audio.astype("<f4").tobytes()
    header = (b"RIFF" + (36 + len(data)).to_bytes(4, "little") + b"WAVEfmt " + (16).to_bytes(4, "little")
              + FLOAT32.to_bytes(2, "little") + (1).to_bytes(2, "little") + SAMPLE_RATE.to_bytes(4, "little")
              + (SAMPLE_RATE * 4).to_bytes(4, "little") + (4).to_bytes(2, "little") + (32).to_bytes(2, "little")
              + b"data" + len(data).to_bytes(4, "little"))
    path.write_bytes(header + data)


def prepare() -> None:
    from tilavet.asr.sherpa import QuranAsrTiny

    rng = random.Random(SEED)
    segments = [(meta_path, s) for meta_path in sorted(STREAMS.glob("*.json"))
                for s in json.loads(meta_path.read_text())["segments"] if s["ref"]]
    CLIPS.mkdir(parents=True, exist_ok=True)
    recognizer = QuranAsrTiny()
    reference = {}
    for n, (meta_path, s) in enumerate(rng.sample(segments, CLIP_COUNT)):
        audio = load_audio(meta_path.with_suffix(".wav"), s["start"], s["end"]).astype(np.float32)
        name = f"{n:02d}.wav"
        _write_float_wav(CLIPS / name, audio)
        start = time.perf_counter()
        text = recognizer.transcribe(audio)
        reference[name] = {"text": text, "seconds": time.perf_counter() - start, "audio_s": len(audio) / SAMPLE_RATE}

    OUT.mkdir(parents=True, exist_ok=True)
    REFERENCE.write_text(json.dumps(reference, ensure_ascii=False))
    print(f"{CLIP_COUNT} clips, {sum(r['audio_s'] for r in reference.values()):.0f} s audio")


def run() -> None:
    reference = json.loads(REFERENCE.read_text())
    launch(["--asr-parity", "--threads", THREADS])
    device = json.loads(pull("parity.json", OUT, wait=True).read_text())

    for threads in sorted({r["threads"] for r in device}):
        rows = [r for r in device if r["threads"] == threads]
        same = sum(r["text"] == reference[r["clip"]]["text"] for r in rows)
        cer = score([reference[r["clip"]]["text"] for r in rows], [r["text"] for r in rows]).cer
        rtf = sum(r["seconds"] for r in rows) / sum(r["audio_s"] for r in rows)
        print(f"threads {threads}: identical {same}/{len(rows)}, CER vs Python {100 * cer:.2f}%, RTF {rtf:.4f}")

    python_rtf = sum(r["seconds"] for r in reference.values()) / sum(r["audio_s"] for r in reference.values())
    print(f"Mac Python RTF (4 threads): {python_rtf:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "run"])
    args = parser.parse_args()
    prepare() if args.command == "prepare" else run()


if __name__ == "__main__":
    main()
