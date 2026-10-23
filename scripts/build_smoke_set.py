"""Build a small ayah-level eval set from EveryAyah per-ayah recordings.

Not leakage-free for every model (see reports/m2-*.md); used to validate the
pipeline and measure speed. Per-ayah files avoid cutting chapter audio: quran.com
timings for some reciters are shifted by about a word.
"""

import json
import random
import urllib.request
from pathlib import Path

from tilavet.corpus import AyahRef, load_tanzil

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
AUDIO = RAW / "everyayah"
OUT = ROOT / "data" / "derived" / "sets" / "smoke.jsonl"

USER_AGENT = "tilavet-meal/0.1 (research prototype)"
AYAH_URL = "https://everyayah.com/data/{folder}/{sura:03d}{aya:03d}.mp3"

RECITERS = {"hani-rifai": "Hani_Rifai_192kbps", "minshawi-murattal": "Minshawy_Murattal_128kbps"}
SURAS = {1, 36, 67, *range(78, 115)}
CLIPS_PER_RECITER = 100
SEED = 7


def _download(url: str, path: Path) -> None:
    if path.exists():
        return

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        path.write_bytes(response.read())


def main() -> None:
    quran = load_tanzil(RAW / "quran-simple-clean.txt")
    # Aya 1 is skipped: basmala handling differs between recordings.
    eligible = sorted(ref for ref in quran if ref.sura in SURAS and ref.aya > 1)
    rows = []

    for name, folder in RECITERS.items():
        target = AUDIO / folder
        target.mkdir(parents=True, exist_ok=True)

        for ref in random.Random(SEED).sample(eligible, CLIPS_PER_RECITER):
            path = target / f"{ref.sura:03d}{ref.aya:03d}.mp3"
            _download(AYAH_URL.format(folder=folder, sura=ref.sura, aya=ref.aya), path)
            rows.append(
                {
                    "id": f"{name}-{ref.sura}-{ref.aya}",
                    "source": name,
                    "audio": str(path.relative_to(ROOT)),
                    "text": quran[AyahRef(ref.sura, ref.aya)],
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"wrote {OUT.relative_to(ROOT)} ({len(rows)} clips)")


if __name__ == "__main__":
    main()
