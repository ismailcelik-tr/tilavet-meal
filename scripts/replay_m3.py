"""Replay cached ASR windows through PositionEngine + EmissionPolicy; score vs truth.

    uv run python scripts/replay_m3.py               # report with default EngineConfig
    uv run python scripts/replay_m3.py --sweep       # tune on dev streams only
    uv run python scripts/replay_m3.py --debug quran-asr-tiny/clean   # wrong + missed per stream
"""

import argparse
import itertools
import json
from collections import defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path

from tilavet.corpus import AyahRef, load_tanzil, meal_units, normalize, strip_basmala
from tilavet.engine import EngineConfig, Lost, PositionEngine, QuranIndex
from tilavet.eval import Emission, Segment, StreamScore, score, score_stream
from tilavet.eval.streams import LATE_LIMIT_S
from tilavet.policy import EmissionPolicy

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
STREAMS = ROOT / "data" / "derived" / "streams"
ASR = ROOT / "data" / "derived" / "m3" / "asr"
OUT = ROOT / "reports" / "m3-results.md"

COOLDOWN_S = 300.0
SPLITS = ("dev", "test")
SWEEP = {
    "acquire_margin": (2, 3, 4),
    "confirm_words": (1, 2, 3),
    "track_min_score": (3, 4),
    "lost_after": (3, 5),
}


@dataclass
class Totals:
    streams: int = 0
    emissions: int = 0
    wrong: int = 0
    late: int = 0
    duplicates: int = 0
    occurrences: int = 0
    recalled: int = 0
    lost: int = 0
    from_start: list[float] = field(default_factory=list)
    from_end: list[float] = field(default_factory=list)

    def add(self, result: StreamScore, lost: int) -> None:
        self.streams += 1
        self.emissions += result.emissions
        self.wrong += result.wrong
        self.late += result.late
        self.duplicates += result.duplicates
        self.occurrences += result.occurrences
        self.recalled += result.recalled
        self.lost += lost
        self.from_start += result.latency_from_start
        self.from_end += result.latency_from_end


def pct(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q / 100 * len(ordered)))] if ordered else float("nan")


def rate(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%" if b else "–"


class Bench:
    def __init__(self) -> None:
        quran = load_tanzil(RAW / "quran-simple-clean.txt")
        self.index = QuranIndex.build({ref: normalize(strip_basmala(ref, text)).split() for ref, text in quran.items()})
        self.units = meal_units(load_tanzil(RAW / "tr.diyanet.txt"))
        self.unit_of = {ref: (u.sura, u.first) for u in self.units for ref in u.refs}
        self.streams = [json.loads(p.read_text()) for p in sorted(STREAMS.glob("*.json"))]

    def replay(self, model: str, condition: str, config: EngineConfig, meta: dict):
        windows = (ASR / model / condition / f"{meta['id']}.windows.jsonl").read_text().splitlines()
        engine = PositionEngine(self.index, config)
        policy = EmissionPolicy(self.units, COOLDOWN_S)
        emissions, events = [], []

        for window in map(json.loads, windows):
            # Emission time includes this hop's ASR compute, as it would live.
            t = window["t"] + window["compute_s"]
            for event in engine.feed(t, normalize(window["text"]).split()):
                events.append(event)
                play = policy.on(event)
                if play:
                    emissions.append(Emission(play.t, (play.unit.sura, play.unit.first)))

        truth = [Segment(AyahRef(*s["ref"]) if s["ref"] else None, s["start"], s["end"]) for s in meta["segments"]]
        return truth, emissions, events

    def run(self, model: str, condition: str, config: EngineConfig, split: str) -> Totals:
        totals = Totals()
        for meta in self.streams:
            if meta["split"] != split:
                continue

            truth, emissions, events = self.replay(model, condition, config, meta)
            totals.add(score_stream(truth, emissions, self.unit_of), sum(isinstance(e, Lost) for e in events))

        return totals

    def clip_cer(self, model: str, condition: str) -> float:
        refs, hyps = [], []
        for meta in self.streams:
            for clip in map(json.loads, (ASR / model / condition / f"{meta['id']}.clips.jsonl").read_text().splitlines()):
                refs.append(clip["reference"])
                hyps.append(clip["text"])
        return score(refs, hyps).cer


def available() -> list[tuple[str, str]]:
    """(model, condition) runs whose ASR pass has finished every stream."""
    expected = len(list(STREAMS.glob("*.json")))
    return sorted(
        (p.parent.name, p.name) for p in ASR.glob("*/*") if len(list(p.glob("*.clips.jsonl"))) == expected
    )


def row(label: str, t: Totals) -> str:
    return (
        f"| {label} | {t.streams} | {t.emissions} | **{rate(t.wrong, t.emissions)}** | {rate(t.late, t.emissions)} | "
        f"{rate(t.recalled, t.occurrences)} | "
        f"{rate(t.duplicates, t.emissions)} | {t.lost} | {pct(t.from_start, 50):.1f} s | {pct(t.from_start, 90):.1f} s | "
        f"{pct(t.from_end, 50):.1f} s | {pct(t.from_end, 90):.1f} s |"
    )


HEADER = [
    "| Koşu | Akış | Meal | Yanlış | Geç | Recall | Mükerrer | Lost | Başlangıçtan p50 | p90 | Birim sonundan p50 | p90 |",
    "|---|---|---|---|---|---|---|---|---|---|---|---|",
]


def sweep(bench: Bench) -> None:
    keys = list(SWEEP)
    print(" ".join(keys), "| model/condition: wrong recall")
    for values in itertools.product(*SWEEP.values()):
        config = replace(EngineConfig(), **dict(zip(keys, values, strict=True)))
        cells = []
        for model, condition in available():
            t = bench.run(model, condition, config, "dev")
            cells.append(f"{model}/{condition}: {rate(t.wrong, t.emissions)} {rate(t.recalled, t.occurrences)}")
        print(values, " | ".join(cells))


def report(bench: Bench) -> None:
    config = EngineConfig()
    lines = [
        "# M3 sonuçları (otomatik: scripts/replay_m3.py)",
        "",
        f"EngineConfig: `{config}`",
        "",
        "Yanlış = son 10 s içinde okunmamış bir ayetin meali (yanıltıcı) / tüm çalınan. Geç = doğru meal, ayet "
        "bittikten 2–10 s sonra. Recall = ilk kez okunan meal birimlerinden "
        "zamanında çalınanlar. Mükerrer = aynı birimin tekrar çalınması. Gecikmeler: meal başlangıcı − "
        "birimin okunmaya başlaması / bitmesi (negatif = okuyucu bitirmeden).",
        "",
    ]
    for split in SPLITS:
        lines += [f"## {split}", "", *HEADER]
        for model, condition in available():
            lines.append(row(f"{model} / {condition}", bench.run(model, condition, config, split)))
        lines.append("")

    lines += ["## Koşulların ses tanıma hatası (ayet klipleri, tüm akışlar)", "", "| Koşu | CER |", "|---|---|"]
    for model, condition in available():
        lines.append(f"| {model} / {condition} | {100 * bench.clip_cer(model, condition):.2f}% |")

    lines += ["", "## Okuyucu bazında (test, varsayılan config)", "", *HEADER]
    for model, condition in available():
        for reciter in sorted({m["reciter"] for m in bench.streams if m["split"] == "test"}):
            subset = Bench.__new__(Bench)
            subset.__dict__ = {**bench.__dict__, "streams": [m for m in bench.streams if m["reciter"] == reciter]}
            lines.append(row(f"{model} / {condition} / {reciter}", subset.run(model, condition, config, "test")))

    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


def debug(bench: Bench, run: str) -> None:
    model, condition = run.split("/")
    for meta in bench.streams:
        truth, emissions, events = bench.replay(model, condition, EngineConfig(), meta)

        def correct(e: Emission) -> bool:
            return any(s.ref and bench.unit_of[s.ref] == e.unit and s.start <= e.t <= s.end + LATE_LIMIT_S
                       for s in truth)

        wrong = [e for e in emissions if not correct(e)]
        result = score_stream(truth, emissions, bench.unit_of)
        if not wrong and result.recalled == result.occurrences:
            continue

        print(f"== {meta['id']} ({meta['split']}) recalled {result.recalled}/{result.occurrences}")
        print("  truth :", " ".join(f"{s.ref.sura}:{s.ref.aya}@{s.start:.0f}" if s.ref else f"-@{s.start:.0f}"
                                  for s in truth))
        print("  events:", " ".join(f"{e.ref.sura}:{e.ref.aya}@{e.t:.0f}{e.mode.value[0]}" if hasattr(e, "ref")
                                  else f"LOST@{e.t:.0f}" for e in events))
        print("  wrong :", [(round(e.t), e.unit) for e in wrong])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", action="store_true")
    parser.add_argument("--debug", metavar="MODEL/CONDITION")
    args = parser.parse_args()

    bench = Bench()
    if args.sweep:
        sweep(bench)
        return
    if args.debug:
        debug(bench, args.debug)
        return

    report(bench)


if __name__ == "__main__":
    main()
