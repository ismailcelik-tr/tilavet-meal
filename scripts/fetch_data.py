"""Download pinned M1 inputs into data/raw and write data/manifest.json."""

import hashlib
import json
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifest.json"

USER_AGENT = "tilavet-meal/0.1 (research prototype)"
SURA_COUNT = 114
REQUEST_DELAY_S = 0.1

TANZIL_TEXT_URL = "https://tanzil.net/pub/download/index.php?quranType=simple-clean&outType=txt-2&agree=true"
TANZIL_TRANS_URL = "https://tanzil.net/trans/?transID={id}&type=txt-2"
TIMINGS_URL = "https://api.qurancdn.com/api/qdc/audio/reciters/{id}/audio_files?chapter={sura}&segments=true"

TANZIL_TEXT_LICENSE = "Tanzil Quran Text, CC BY 3.0, verbatim only, attribution + link to tanzil.net"
TANZIL_TRANS_LICENSE = "Tanzil translation, non-commercial use only (tanzil.net/trans)"
TIMINGS_LICENSE = "quran.com / Quran Foundation API, terms unverified; evaluation use only"

TRANSLATIONS = ["tr.diyanet", "tr.vakfi"]

# quran.com reciter ids; style spread from mujawwad (slow) to taraweeh-like murattal.
RECITERS = {
    1: "abdulbaset-mujawwad",
    6: "husary-murattal",
    9: "minshawi-murattal",
    7: "alafasy-murattal",
    10: "shuraim-murattal",
    3: "sudais-murattal",
}


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fetch_file(path: Path, url: str) -> None:
    if path.exists():
        return

    print(f"GET {url}")
    path.write_bytes(_get(url))


def _fetch_timings(path: Path, reciter_id: int) -> None:
    if path.exists():
        return

    chapters = []
    for sura in range(1, SURA_COUNT + 1):
        url = TIMINGS_URL.format(id=reciter_id, sura=sura)
        chapters.extend(json.loads(_get(url))["audio_files"])
        time.sleep(REQUEST_DELAY_S)

    print(f"timings reciter={reciter_id}: {len(chapters)} chapters")
    path.write_text(json.dumps({"reciter_id": reciter_id, "audio_files": chapters}, ensure_ascii=False))


def _entry(path: Path, url: str, license_note: str) -> dict:
    retrieved = datetime.fromtimestamp(path.stat().st_mtime, UTC)
    return {
        "path": str(path.relative_to(ROOT)),
        "url": url,
        "sha256": _sha256(path),
        "retrieved_at": retrieved.isoformat(timespec="seconds"),
        "license": license_note,
    }


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    entries = []

    text_path = RAW / "quran-simple-clean.txt"
    _fetch_file(text_path, TANZIL_TEXT_URL)
    entries.append(_entry(text_path, TANZIL_TEXT_URL, TANZIL_TEXT_LICENSE))

    for trans_id in TRANSLATIONS:
        url = TANZIL_TRANS_URL.format(id=trans_id)
        path = RAW / f"{trans_id}.txt"
        _fetch_file(path, url)
        entries.append(_entry(path, url, TANZIL_TRANS_LICENSE))

    for reciter_id, name in RECITERS.items():
        path = RAW / f"timings-{reciter_id}-{name}.json"
        _fetch_timings(path, reciter_id)
        url = TIMINGS_URL.format(id=reciter_id, sura="1..114")
        entries.append(_entry(path, url, TIMINGS_LICENSE))

    MANIFEST.write_text(json.dumps({"files": entries}, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {MANIFEST.relative_to(ROOT)} ({len(entries)} files)")


if __name__ == "__main__":
    main()
