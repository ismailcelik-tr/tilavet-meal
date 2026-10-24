"""Golden vectors for the Swift port: the same inputs must give the same outputs.

    uv run python scripts/export_golden.py

Writes data/derived/m6/golden/{normalize,align,engine}.json from the blind2 tiny cache.
"""

import json
import random

from replay_m3 import COOLDOWN_S, RAW, ROOT, SETS, Bench
from tilavet.corpus import load_tanzil, normalize, strip_basmala
from tilavet.engine import AyahConfirmed, EngineConfig, Lost, PositionEngine
from tilavet.engine.align import align_all
from tilavet.policy import EmissionPolicy

OUT = ROOT / "data" / "derived" / "m6" / "golden"
MODEL = "quran-asr-tiny"
CONDITIONS = ("clean", "hard")
SEED = 5
ASR_TEXTS = 5000
ALIGN_CASES = 500
ALIGN_REGION = 60
ALIGN_MIN_SCORE = 3


def _write(name: str, data: object) -> None:
    (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False))
    print(f"{name}: {len(data)}")


def _engine_records(bench: Bench, condition: str, meta: dict) -> dict:
    engine = PositionEngine(bench.index, EngineConfig())
    policy = EmissionPolicy(bench.units, COOLDOWN_S)
    windows, records = [], []
    for window in bench.windows(MODEL, condition, meta):
        t = window["t"] + window["compute_s"]
        windows.append([t, window["text"]])
        for event in engine.feed(t, normalize(window["text"]).split()):
            if isinstance(event, AyahConfirmed):
                records.append({"type": "AyahConfirmed", "t": t, "ref": list(event.ref), "mode": event.mode.value,
                                "score": event.score})
            if isinstance(event, Lost):
                records.append({"type": "Lost", "t": t})
            play = policy.on(event)
            if play:
                records.append({"type": "Play", "t": play.t, "unit": [play.unit.sura, play.unit.first, play.unit.last]})

    return {"id": f"{condition}/{meta['id']}", "windows": windows, "records": records}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    bench = Bench(*SETS["blind2"][:2])
    texts = [w["text"] for c in CONDITIONS for m in bench.streams for w in bench.windows(MODEL, c, m) if w["text"]]

    quran = [strip_basmala(ref, text) for ref, text in sorted(load_tanzil(RAW / "quran-simple-clean.txt").items())]
    _write("normalize", [[raw, normalize(raw)] for raw in quran + rng.sample(texts, ASR_TEXTS)])

    corpus = bench.index.words
    cases = []
    while len(cases) < ALIGN_CASES:
        hyp = normalize(rng.choice(texts)).split()
        # Centre most regions on the rarest hypothesis word, so they align something; the rest are random.
        known = [bench.index.positions(w) for w in hyp if bench.index.positions(w)]
        hits = min(known, key=len) if known and len(cases) % 4 else ()
        centre = rng.choice(hits) if hits else rng.randrange(len(corpus))
        lo = min(max(0, centre - ALIGN_REGION // 2), len(corpus) - ALIGN_REGION)
        found = align_all(hyp, corpus, lo, lo + ALIGN_REGION, ALIGN_MIN_SCORE)
        cases.append({"hyp": hyp, "lo": lo, "hi": lo + ALIGN_REGION, "min_score": ALIGN_MIN_SCORE, "expected": [
            {"score": a.score, "corpus_start": a.corpus_start, "corpus_end": a.corpus_end,
             "pairs": [list(p) for p in a.pairs], "hyp_end": a.hyp_end} for a in found]})
    _write("align", cases)

    _write("engine", [_engine_records(bench, c, m) for c in CONDITIONS for m in bench.streams])


if __name__ == "__main__":
    main()
