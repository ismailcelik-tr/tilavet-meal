"""Measure spoken duration of every meal unit with macOS `say`.

Audio is discarded; only durations are kept (the PoC voice is not final).
"""

import argparse
import csv
import subprocess
import tempfile
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tilavet.corpus import MealUnit, load_tanzil, meal_units

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"

AUDIO_FORMAT = "LEI16@22050"
WORKERS = 8


def _duration_s(unit: MealUnit, voice: str, workdir: Path) -> float:
    name = f"{unit.sura}-{unit.first}"
    text_path = workdir / f"{name}.txt"
    audio_path = workdir / f"{name}.wav"

    # -f avoids `say` parsing text that starts with "-" as an option.
    text_path.write_text(unit.text, encoding="utf-8")
    subprocess.run(
        ["say", "-v", voice, f"--data-format={AUDIO_FORMAT}", "-o", str(audio_path), "-f", str(text_path)],
        check=True,
    )

    with wave.open(str(audio_path)) as w:
        seconds = w.getnframes() / w.getframerate()

    text_path.unlink()
    audio_path.unlink()
    return seconds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--translation", default="tr.diyanet")
    parser.add_argument("--voice", default="Yelda")
    args = parser.parse_args()

    units = meal_units(load_tanzil(RAW / f"{args.translation}.txt"))
    DERIVED.mkdir(parents=True, exist_ok=True)
    out = DERIVED / f"meal-durations-{args.translation}-{args.voice.lower()}.csv"

    with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(WORKERS) as pool:
        durations = list(pool.map(lambda u: _duration_s(u, args.voice, Path(tmp)), units))

    with out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sura", "first", "last", "chars", "seconds"])
        for unit, seconds in zip(units, durations, strict=True):
            writer.writerow([unit.sura, unit.first, unit.last, len(unit.text), f"{seconds:.3f}"])

    print(f"wrote {out.relative_to(ROOT)} ({len(units)} units, {sum(durations) / 3600:.2f} h)")


if __name__ == "__main__":
    main()
