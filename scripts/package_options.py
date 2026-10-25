"""Meal audio size per codec and bit rate, plus listening samples (M6 package options).

    uv run python scripts/package_options.py      # ~5 min; resumes

Sizes come from transcoding every shipped unit. Samples are rendered from text (`say` → PCM → `afconvert`),
so they carry no second-generation loss. Writes data/derived/m6/package/{<variant>/, samples/, summary.json}.
"""

import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tilavet.corpus import load_tanzil, meal_units

ROOT = Path(__file__).resolve().parents[1]
MEALS = ROOT / "data" / "derived" / "meals" / "tr.diyanet-yelda"
OUT = ROOT / "data" / "derived" / "m6" / "package"
VOICE = "Yelda"
# (afconvert data format, bit rate). aac 32k: the shipped quality without `say`'s 32 KB header padding.
VARIANTS = (("aach", 16000), ("aach", 24000), ("aac", 32000))
# Fatiha, short, multi-ayah, Ayat al-Kursi, longest.
SAMPLES = ((1, 2), (112, 1), (12, 11), (2, 255), (2, 282))
WORKERS = 8


def _name(variant: tuple[str, int]) -> str:
    codec, bit_rate = variant
    return f"{codec}-{bit_rate // 1000}k"


def _encode(source: Path, target: Path, variant: tuple[str, int]) -> None:
    codec, bit_rate = variant
    partial = target.with_suffix(".part.m4a")
    subprocess.run(["afconvert", "-f", "m4af", "-d", codec, "-b", str(bit_rate), str(source), str(partial)], check=True)
    partial.rename(target)


def _transcode(variant: tuple[str, int]) -> int:
    out = OUT / _name(variant)
    out.mkdir(parents=True, exist_ok=True)
    sources = sorted(MEALS.glob("*.m4a"))

    def one(source: Path) -> int:
        target = out / source.name
        if not target.exists():
            _encode(source, target, variant)
        return target.stat().st_size

    with ThreadPoolExecutor(WORKERS) as pool:
        return sum(pool.map(one, sources))


def _samples() -> None:
    out = OUT / "samples"
    out.mkdir(parents=True, exist_ok=True)
    units = {(u.sura, u.first): u for u in meal_units(load_tanzil(ROOT / "data" / "raw" / "tr.diyanet.txt"))}

    with tempfile.TemporaryDirectory() as tmp:
        for sura, first in SAMPLES:
            stem = f"{sura}-{first}"
            shutil.copy(MEALS / f"{stem}.m4a", out / f"{stem}-shipped.m4a")

            # -f avoids `say` parsing text that starts with "-" as an option.
            text = Path(tmp) / f"{stem}.txt"
            text.write_text(units[(sura, first)].text, encoding="utf-8")
            pcm = Path(tmp) / f"{stem}.wav"
            subprocess.run(["say", "-v", VOICE, "--file-format=WAVE", "--data-format=LEI16@22050", "-o", str(pcm),
                            "-f", str(text)], check=True)
            for variant in VARIANTS:
                _encode(pcm, out / f"{stem}-{_name(variant)}.m4a", variant)


def main() -> None:
    shipped = sorted(MEALS.glob("*.m4a"))
    summary = {"units": len(shipped), "shipped_mb": round(sum(p.stat().st_size for p in shipped) / 1e6, 1)}
    for variant in VARIANTS:
        summary[f"{_name(variant)}_mb"] = round(_transcode(variant) / 1e6, 1)
    _samples()

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
