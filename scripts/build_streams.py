"""Synthesize continuous recitation streams with known ground truth.

Ayah recordings (EveryAyah) are concatenated in mushaf order with injected
repetitions, skips and long pauses. Writes 16 kHz wav + truth json per stream.
"""

import argparse
import json
import random
import urllib.request
import wave
from pathlib import Path

import numpy as np

from tilavet.audio import SAMPLE_RATE, load_audio
from tilavet.corpus import AyahRef, load_tanzil

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
AUDIO = RAW / "everyayah"
OUT = ROOT / "data" / "derived" / "streams"
BLIND_OUT = ROOT / "data" / "derived" / "streams-blind"
BLIND2_OUT = ROOT / "data" / "derived" / "streams-blind2"

USER_AGENT = "tilavet-meal/0.1 (research prototype)"
AYAH_URL = "https://everyayah.com/data/{folder}/{sura:03d}{aya:03d}.mp3"

# Thresholds are tuned on dev reciters only; results are reported on test reciters.
RECITERS = {
    "husary": ("Husary_128kbps", "dev"),
    "shuraim": ("Saood_ash-Shuraym_128kbps", "dev"),
    "hani-rifai": ("Hani_Rifai_192kbps", "test"),
    "minshawi": ("Minshawy_Murattal_128kbps", "test"),
    "abdulbaset-mujawwad": ("Abdul_Basit_Mujawwad_128kbps", "test"),
    "sudais": ("Abdurrahmaan_As-Sudais_192kbps", "test"),
}
# Held out until the engine rules are frozen (M4); kept apart so routine replays never see it.
BLIND_RECITERS = {
    "alafasy": ("Alafasy_128kbps", "blind"),
    "maher-muaiqly": ("MaherAlMuaiqly128kbps", "blind"),
    "muhammad-ayyoub": ("Muhammad_Ayyoub_128kbps", "blind"),
    "minshawi-mujawwad": ("Minshawy_Mujawwad_192kbps", "blind"),
}
# Held out until the M5 rules are frozen; two mujawwad reciters, the weak spot in M4.
BLIND2_RECITERS = {
    "husary-mujawwad": ("Husary_128kbps_Mujawwad", "blind"),
    "tablawi": ("Mohammad_al_Tablaway_128kbps", "blind"),
    "ghamdi": ("Ghamadi_40kbps", "blind"),
    "hudhaify": ("Hudhaify_128kbps", "blind"),
}
STREAMS_PER_RECITER = 5
BLIND_STREAMS_PER_RECITER = 10
MAX_AYAHS = 12
MAX_SECONDS = 240.0
SEED = 11
BLIND_SEED = 29
BLIND2_SEED = 47

P_REPEAT = 0.12
P_SKIP = 0.06
P_PAUSE = 0.08
GAP_S = (0.3, 0.8)
PAUSE_S = (8.0, 20.0)
LONG_PAUSE_S = 30.0
LONG_PAUSE_AFTER = 4  # among the first ayahs, so the MAX_SECONDS cut keeps the pause

BASMALA = AyahRef(1, 1)
NO_BASMALA_SURAS = {1, 9}
INT16_MAX = 32767


def _ayah_audio(folder: str, ref: AyahRef) -> np.ndarray:
    path = AUDIO / folder / f"{ref.sura:03d}{ref.aya:03d}.mp3"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(AYAH_URL.format(folder=folder, sura=ref.sura, aya=ref.aya),
                                         headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())

    return load_audio(path)


def _passage(rng: random.Random, refs: list[AyahRef]) -> list[AyahRef]:
    start = rng.randrange(len(refs))
    passage = []
    for ref in refs[start:]:
        if ref.sura != refs[start].sura or len(passage) == MAX_AYAHS:
            break
        passage.append(ref)
    return passage


def _script(rng: random.Random, passage: list[AyahRef]) -> list[tuple[str, AyahRef | float]]:
    """Recitation plan: ('ayah', ref) / ('basmala', ref) / ('pause', seconds)."""
    plan: list[tuple[str, AyahRef | float]] = []
    if passage[0].aya == 1 and passage[0].sura not in NO_BASMALA_SURAS:
        plan.append(("basmala", BASMALA))

    i = 0
    while i < len(passage):
        plan.append(("ayah", passage[i]))
        if i > 0 and rng.random() < P_REPEAT:
            plan.append(("ayah", passage[i - 1]))
            plan.append(("ayah", passage[i]))
        if rng.random() < P_PAUSE:
            plan.append(("pause", rng.uniform(*PAUSE_S)))
        i += 2 if rng.random() < P_SKIP else 1

    return plan


def _with_long_pause(rng: random.Random, plan: list[tuple[str, AyahRef | float]]) -> list[tuple[str, AyahRef | float]]:
    ayahs = [i for i, (kind, _) in enumerate(plan) if kind == "ayah"][:LONG_PAUSE_AFTER]
    at = rng.choice(ayahs[1:] or ayahs) + 1
    return [*plan[:at], ("pause", LONG_PAUSE_S), *plan[at:]]


def _render(folder: str, plan, rng: random.Random) -> tuple[np.ndarray, list[dict]]:
    chunks, truth, cursor = [], [], 0.0

    for kind, value in plan:
        if kind == "pause":
            audio = np.zeros(round(value * SAMPLE_RATE), dtype=np.float32)
            ref = None
        else:
            audio = _ayah_audio(folder, value)
            ref = value if kind == "ayah" else None

        duration = len(audio) / SAMPLE_RATE
        truth.append({"ref": list(ref) if ref else None, "start": round(cursor, 3), "end": round(cursor + duration, 3)})
        chunks.append(audio)
        cursor += duration

        gap = np.zeros(round(rng.uniform(*GAP_S) * SAMPLE_RATE), dtype=np.float32)
        chunks.append(gap)
        cursor += len(gap) / SAMPLE_RATE

        if cursor > MAX_SECONDS:
            break

    return np.concatenate(chunks), truth


def _write_wav(path: Path, audio: np.ndarray) -> None:
    pcm = (np.clip(audio, -1, 1) * INT16_MAX).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())


SETS = {
    "main": (RECITERS, STREAMS_PER_RECITER, SEED, OUT, False),
    "blind": (BLIND_RECITERS, BLIND_STREAMS_PER_RECITER, BLIND_SEED, BLIND_OUT, False),
    "blind2": (BLIND2_RECITERS, BLIND_STREAMS_PER_RECITER, BLIND2_SEED, BLIND2_OUT, True),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", default="main", choices=sorted(SETS))
    args = parser.parse_args()

    reciters, per_reciter, seed, out, long_pause = SETS[args.set]
    refs = sorted(load_tanzil(RAW / "quran-simple-clean.txt"))
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    for name, (folder, split) in reciters.items():
        for n in range(per_reciter):
            stream_id = f"{name}-{n}"
            plan = _script(rng, _passage(rng, refs))
            if long_pause:
                plan = _with_long_pause(rng, plan)
            audio, truth = _render(folder, plan, rng)

            _write_wav(out / f"{stream_id}.wav", audio)
            meta = {"id": stream_id, "reciter": name, "split": split, "duration": len(audio) / SAMPLE_RATE,
                    "segments": truth}
            (out / f"{stream_id}.json").write_text(json.dumps(meta) + "\n")
            print(f"{stream_id}: {meta['duration']:.0f} s, {sum(s['ref'] is not None for s in truth)} ayah segments")


if __name__ == "__main__":
    main()
