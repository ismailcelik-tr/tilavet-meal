"""Pre-render every meal unit with a Piper voice as HE-AAC, plus the durations the player needs.

    uv run --group piper python scripts/render_meals_piper.py      # ~15 min; resumes

Writes data/derived/meals/<translation>-<voice>/<sura>-<first>.m4a and
data/derived/meal-durations-<translation>-<voice>.csv. The voice license is unstated (U7).
"""

import argparse
import csv
import io
import subprocess
import tempfile
import wave
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from huggingface_hub import hf_hub_download
from piper import PiperVoice

from tilavet.corpus import MealUnit, load_tanzil, meal_units

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
REPO = "99eren99/piper-turkish-tts"
REVISION = "885d69c91c4a83f49467f152690460e26b818d0b"
VOICE = "eren"
BIT_RATE = 16000  # HE-AAC; no audible difference from the shipped set (M6)
WORKERS = 6

_voice: PiperVoice | None = None


def _load() -> None:
    global _voice
    model = hf_hub_download(REPO, "model.onnx", revision=REVISION)
    config = hf_hub_download(REPO, "config.json", revision=REVISION)
    _voice = PiperVoice.load(model, config_path=config)


def _render(unit: MealUnit, out: Path) -> float:
    """Encode one unit unless present; return its spoken seconds."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as w:
        _voice.synthesize_wav(unit.text, w)
    buffer.seek(0)
    with wave.open(buffer) as w:
        seconds = w.getnframes() / w.getframerate()

    path = out / f"{unit.sura}-{unit.first}.m4a"
    if path.exists():
        return seconds

    with tempfile.NamedTemporaryFile(suffix=".wav") as pcm:
        pcm.write(buffer.getvalue())
        pcm.flush()
        partial = path.with_suffix(".part.m4a")
        subprocess.run(["afconvert", "-f", "m4af", "-d", "aach", "-b", str(BIT_RATE), pcm.name, str(partial)],
                       check=True)
        partial.rename(path)
    return seconds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--translation", default="tr.diyanet")
    args = parser.parse_args()

    units = meal_units(load_tanzil(RAW / f"{args.translation}.txt"))
    out = DERIVED / "meals" / f"{args.translation}-{VOICE}"
    out.mkdir(parents=True, exist_ok=True)

    with ProcessPoolExecutor(WORKERS, initializer=_load) as pool:
        durations = list(pool.map(_render, units, [out] * len(units), chunksize=16))

    csv_path = DERIVED / f"meal-durations-{args.translation}-{VOICE}.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sura", "first", "last", "chars", "seconds"])
        for unit, seconds in zip(units, durations, strict=True):
            writer.writerow([unit.sura, unit.first, unit.last, len(unit.text), f"{seconds:.3f}"])

    size = sum(p.stat().st_size for p in out.glob("*.m4a"))
    print(f"wrote {csv_path.relative_to(ROOT)} ({len(units)} units, {sum(durations) / 3600:.2f} h, {size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
