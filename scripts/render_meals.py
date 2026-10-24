"""Pre-render every meal unit with macOS `say` (AAC), so playback has no TTS latency.

    uv run python scripts/render_meals.py      # ~20 min, ~210 MB; resumes

Writes data/derived/meals/<translation>-<voice>/<sura>-<first>.m4a. Durations
for the player come from scripts/render_meal_durations.py (same voice and text).
"""

import argparse
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tilavet.corpus import MealUnit, load_tanzil, meal_units

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MEALS = ROOT / "data" / "derived" / "meals"
WORKERS = 8


def _render(unit: MealUnit, voice: str, out: Path, workdir: Path) -> None:
    path = out / f"{unit.sura}-{unit.first}.m4a"
    if path.exists():
        return

    # -f avoids `say` parsing text that starts with "-" as an option.
    text_path = workdir / f"{unit.sura}-{unit.first}.txt"
    text_path.write_text(unit.text, encoding="utf-8")
    partial = path.with_suffix(".part.m4a")
    subprocess.run(
        ["say", "-v", voice, "--file-format=m4af", "--data-format=aac", "-o", str(partial), "-f", str(text_path)],
        check=True,
    )
    partial.rename(path)
    text_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--translation", default="tr.diyanet")
    parser.add_argument("--voice", default="Yelda")
    args = parser.parse_args()

    units = meal_units(load_tanzil(RAW / f"{args.translation}.txt"))
    out = MEALS / f"{args.translation}-{args.voice.lower()}"
    out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(lambda u: _render(u, args.voice, out, Path(tmp)), units))

    print(f"{len(units)} units in {out}")


if __name__ == "__main__":
    main()
