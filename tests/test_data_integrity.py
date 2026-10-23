"""Checks on pinned raw data. Skipped until scripts/fetch_data.py has run."""

import hashlib
import json
from pathlib import Path

import pytest

from tilavet.corpus import AyahRef, load_tanzil

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "manifest.json"
RAW = ROOT / "data" / "raw"

AYAH_COUNT = 6236
SURA_COUNT = 114

pytestmark = pytest.mark.skipif(not MANIFEST.exists(), reason="run scripts/fetch_data.py first")


def _manifest_files() -> list[dict]:
    return json.loads(MANIFEST.read_text())["files"]


@pytest.fixture(scope="module")
def quran() -> dict[AyahRef, str]:
    return load_tanzil(RAW / "quran-simple-clean.txt")


def test_files_match_manifest_sha256():
    for entry in _manifest_files():
        digest = hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest()
        assert digest == entry["sha256"], entry["path"]


def test_quran_has_all_ayahs(quran):
    assert len(quran) == AYAH_COUNT
    assert {ref.sura for ref in quran} == set(range(1, SURA_COUNT + 1))


@pytest.mark.parametrize("trans_id", ["tr.diyanet", "tr.vakfi"])
def test_translation_covers_every_ayah(quran, trans_id):
    meal = load_tanzil(RAW / f"{trans_id}.txt")

    assert meal.keys() == quran.keys()
    assert all(text.strip() for text in meal.values())


def test_timings_cover_every_ayah():
    for path in sorted(RAW.glob("timings-*.json")):
        files = json.loads(path.read_text())["audio_files"]
        keys = {t["verse_key"] for f in files for t in f["verse_timings"]}
        assert len(keys) == AYAH_COUNT, path.name
