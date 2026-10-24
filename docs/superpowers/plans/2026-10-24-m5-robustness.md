# M5 Robustness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the engine mechanisms behind M4's wrong meals, test them on a new blind set with 30 s pauses, measure non-Quran speech and resources, and report GO/NO-GO.

**Architecture:** Two engine rules in `PositionEngine` (look-alike search by corpus words, wider margin for already-recited rivals), each TDD'd from real M4 cases. Evaluation reuses the cached-ASR replay (`scripts/replay_m3.py`) with a new `blind2` stream set and a pause metric in `tilavet.eval`.

**Tech Stack:** Python 3.12, uv, pytest, sherpa-onnx (tiny), existing `tilavet` package.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-10-24-m5-robustness-design.md`.
- Primary model `quran-asr-tiny`; blind2 ASR runs tiny only.
- Rule acceptance without asking: no condition loses > 1 recall point, p50 latency grows ≤ 0.5 s. Otherwise İsmail decides.
- No look at blind2 ASR text or results before İsmail approves the freeze and the opening.
- Code, comments, commits in English; commit subject ≤ 50 chars, imperative; trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Commit and push after each task.
- No new dependencies.

---

### Task 1: Blind2 stream set and ASR pass

**Files:**
- Modify: `scripts/build_streams.py`
- Modify: `scripts/asr_windows.py:26-29`

Script-only change (TDD exception for one-off scripts).

- [ ] **Step 1: Add the set to `build_streams.py`**

After `BLIND_RECITERS`:

```python
# Held out until the M5 rules are frozen; two mujawwad reciters, the weak spot in M4.
BLIND2_RECITERS = {
    "husary-mujawwad": ("Husary_128kbps_Mujawwad", "blind"),
    "tablawi": ("Mohammad_al_Tablaway_128kbps", "blind"),
    "ghamdi": ("Ghamadi_40kbps", "blind"),
    "hudhaify": ("Hudhaify_128kbps", "blind"),
}
```

Constants next to the others:

```python
BLIND2_OUT = ROOT / "data" / "derived" / "streams-blind2"
BLIND2_SEED = 47
LONG_PAUSE_S = 30.0
LONG_PAUSE_AFTER = 4  # among the first ayahs, so the MAX_SECONDS cut keeps the pause
```

After `_script`:

```python
def _with_long_pause(rng: random.Random, plan: list[tuple[str, AyahRef | float]]) -> list[tuple[str, AyahRef | float]]:
    ayahs = [i for i, (kind, _) in enumerate(plan) if kind == "ayah"][:LONG_PAUSE_AFTER]
    at = rng.choice(ayahs[1:] or ayahs) + 1
    return [*plan[:at], ("pause", LONG_PAUSE_S), *plan[at:]]
```

`SETS` gains a long-pause flag:

```python
SETS = {
    "main": (RECITERS, STREAMS_PER_RECITER, SEED, OUT, False),
    "blind": (BLIND_RECITERS, BLIND_STREAMS_PER_RECITER, BLIND_SEED, BLIND_OUT, False),
    "blind2": (BLIND2_RECITERS, BLIND_STREAMS_PER_RECITER, BLIND2_SEED, BLIND2_OUT, True),
}
```

In `main`:

```python
    reciters, per_reciter, seed, out, long_pause = SETS[args.set]
    ...
            plan = _script(rng, _passage(rng, refs))
            if long_pause:
                plan = _with_long_pause(rng, plan)
```

- [ ] **Step 2: Add the set to `asr_windows.py`**

```python
    "blind2": (ROOT / "data" / "derived" / "streams-blind2", ROOT / "data" / "derived" / "m5" / "asr-blind2"),
```

- [ ] **Step 3: Build and check, without reading ASR text**

Run: `uv run python scripts/build_streams.py --set blind2`
Expected: 40 lines `<id>: <n> s, <k> ayah segments`. Then confirm each stream has a 30 s segment:

```bash
uv run python -c "
import json, glob
for f in sorted(glob.glob('data/derived/streams-blind2/*.json')):
    m = json.load(open(f)); assert any(s['ref'] is None and s['end'] - s['start'] >= 29.9 for s in m['segments']), f
print('ok')"
```

- [ ] **Step 4: Start ASR in the background**

```bash
for c in clean noisy hard; do uv run --group onnx python scripts/asr_windows.py --set blind2 --model quran-asr-tiny --condition $c > <scratchpad>/blind2-$c.log 2>&1 || break; done
```

Expected later: `data/derived/m5/asr-blind2/quran-asr-tiny/{clean,noisy,hard}` each with 40 `.windows.jsonl` and 40 `.clips.jsonl`.

- [ ] **Step 5: Commit** `Add blind2 stream set with 30 s pauses`

---

### Task 2: Pause metric

**Files:**
- Modify: `src/tilavet/eval/streams.py`, `src/tilavet/eval/__init__.py`
- Test: `tests/test_stream_metrics.py`

**Interfaces:**
- Produces: `pause_emissions(truth: Sequence[Segment], emissions: Sequence[Emission], min_pause_s: float) -> int`

- [ ] **Step 1: Write the failing tests** (append to `tests/test_stream_metrics.py`; `TRUTH` has a 15 s pause at 10–25 s)

```python
def test_emission_late_in_a_long_pause_counts():
    assert pause_emissions(TRUTH, [Emission(22.0, (1, 2))], min_pause_s=15.0) == 1


def test_last_ayahs_meal_early_in_a_pause_does_not_count():
    assert pause_emissions(TRUTH, [Emission(19.0, (1, 2))], min_pause_s=15.0) == 0


def test_short_pauses_are_ignored():
    assert pause_emissions(TRUTH, [Emission(22.0, (1, 2))], min_pause_s=20.0) == 0
```

Import: `from tilavet.eval import Emission, Segment, pause_emissions, score_stream`.

- [ ] **Step 2: Run, expect ImportError**

Run: `uv run pytest tests/test_stream_metrics.py -q`

- [ ] **Step 3: Implement** in `streams.py`, add to `__all__` of both modules:

```python
def pause_emissions(truth: Sequence[Segment], emissions: Sequence[Emission], min_pause_s: float) -> int:
    """Meals played inside silences of at least `min_pause_s`, after the last ayah's meal had its LATE_LIMIT_S."""
    pauses = [s for s in truth if s.ref is None and s.end - s.start >= min_pause_s]
    return sum(1 for p in pauses for e in emissions if p.start + LATE_LIMIT_S < e.t <= p.end)
```

- [ ] **Step 4: Run, expect pass**; full suite `uv run pytest -q`.

- [ ] **Step 5: Commit** `Add long pause emission metric`

---

### Task 3: Replay sets, tuning table, blind2 report

**Files:**
- Modify: `scripts/replay_m3.py`

**Interfaces:**
- Consumes: `pause_emissions` (Task 2).
- Produces: CLI `--set main|blind|blind2`, `--tune [KEY=VALUE ...]`.

- [ ] **Step 1: Sets instead of `--blind`**

```python
SETS = {
    "main": (STREAMS, ASR, OUT),
    "blind": (BLIND_STREAMS, BLIND_ASR, BLIND_OUT),
    "blind2": (ROOT / "data" / "derived" / "streams-blind2", ROOT / "data" / "derived" / "m5" / "asr-blind2",
               ROOT / "reports" / "m5-blind.md"),
}
LONG_PAUSE_S = 30.0
```

`main`: `--set` (default `main`) replaces `--blind`; `bench = Bench(*SETS[args.set][:2])`; non-main sets call `blind_report(bench, SETS[args.set][2])`. `blind_report` takes `out: Path` instead of `BLIND_OUT`, and its title names the set. Update the module docstring commands.

- [ ] **Step 2: Pause and compute columns in `blind_report`**

`Totals` gains `pause: int = 0`; `Bench.run` adds `pause_emissions(truth, emissions, LONG_PAUSE_S)` per stream. Below the main table:

```python
    lines += ["", "## 30 s duraklama ve ASR süresi", "", "| Koşu | Duraklamada meal | ASR p50 / p90 (adım 1 s) |", "|---|---|---|"]
    for model, condition in available(bench):
        t = bench.run(model, condition, config, "blind")
        compute = [w["compute_s"] for m in bench.streams for w in bench.windows(model, condition, m)]
        lines.append(f"| {model} / {condition} | {t.pause} | {pct(compute, 50):.3f} / {pct(compute, 90):.3f} s |")
```

with `Bench.windows(model, condition, meta) -> list[dict]` extracted from `replay` (reads the `.windows.jsonl`).

- [ ] **Step 3: Tuning table**

```python
TUNE_SETS = (("dev", "main", "dev"), ("test", "main", "test"), ("m4-blind", "blind", "blind"))


def tune(overrides: list[str]) -> None:
    """Rule comparison on every opened set; blind2 stays closed."""
    config = replace(EngineConfig(), **{k: int(v) for k, v in (o.split("=") for o in overrides)})
    benches = {name: Bench(*SETS[name][:2]) for name in ("main", "blind")}
    totals = Totals()
    for label, name, split in TUNE_SETS:
        bench = benches[name]
        for model, condition in available(bench):
            t = bench.run(model, condition, config, split)
            print(f"{label:8} {model:15} {condition:5} wrong {t.wrong:2}/{t.emissions:3} "
                  f"recall {rate(t.recalled, t.occurrences):>6} p50 {pct(t.from_start, 50):.1f} s")
            if model == "quran-asr-tiny":
                totals.wrong += t.wrong
    print(f"tiny wrong total: {totals.wrong}")
```

CLI: `parser.add_argument("--tune", nargs="*", metavar="KEY=VALUE")`; `if args.tune is not None: tune(args.tune); return`.

- [ ] **Step 4: Verify unchanged outputs**

Run: `uv run python scripts/replay_m3.py && uv run python scripts/replay_m3.py --set blind && git diff --stat reports/`
Expected: `m3-results.md` unchanged; `m4-blind.md` differs only by the new pause/compute section (pause column 0: blind has no 30 s pauses).
Run: `uv run python scripts/replay_m3.py --tune` → baseline; save it to the scratchpad as `tune-baseline.txt`. Tiny wrong total must equal M4: dev 0 + test 0 + blind 3 (hard).

- [ ] **Step 5: Commit** `Add replay sets, tuning table and pause column`

---

### Task 4: Rule L — look-alikes by the winner's corpus words

**Files:**
- Modify: `src/tilavet/engine/tracker.py:100-159`
- Create: `tests/test_engine_regressions.py`

**Interfaces:**
- Changes private `_candidate_alignments(words, voters: Iterable[tuple[int, str]], min_votes: int, limit: int | None)`.

- [ ] **Step 1: Write the failing tests** (real corpus; skipped without data)

```python
"""M4 blind set failures, replayed on the real corpus."""

from pathlib import Path

import pytest

from tilavet.corpus import AyahRef, load_tanzil, normalize, strip_basmala
from tilavet.engine import AyahConfirmed, PositionEngine, QuranIndex

QURAN = Path(__file__).resolve().parents[1] / "data" / "raw" / "quran-simple-clean.txt"
pytestmark = pytest.mark.skipif(not QURAN.exists(), reason="run scripts/fetch_data.py first")


@pytest.fixture(scope="module")
def index() -> QuranIndex:
    quran = load_tanzil(QURAN)
    return QuranIndex.build({ref: normalize(strip_basmala(ref, text)).split() for ref, text in quran.items()})


def feed(engine: PositionEngine, *texts: str) -> list[AyahRef]:
    return [e.ref for t, text in enumerate(texts) for e in engine.feed(float(t), normalize(text).split())
            if isinstance(e, AyahConfirmed)]


def test_formula_phrase_does_not_commit(index):
    # minshawi-mujawwad-8: 21:19 opens "وله من في السماوات والأرض"; the window edge dropped "و".
    assert feed(PositionEngine(index), "له من في السماوات والارض") == []


def test_misheard_words_still_find_the_lookalike(index):
    # minshawi-mujawwad-1: 45:33 and 39:48 differ by one later word.
    assert feed(PositionEngine(index), "فوبدا لهم سييات موا") == []
```

- [ ] **Step 2: Run, expect 2 failures** (`[AyahRef(24, 41)]`, `[AyahRef(39, 48)]`)

Run: `uv run pytest tests/test_engine_regressions.py -q`

- [ ] **Step 3: Implement**

```python
    def _acquire(self, t: float, words: Sequence[str]) -> list[Event]:
        config = self._config
        voters = [(i, word) for i, word in enumerate(words)]
        alignments = self._candidate_alignments(words, voters, config.acquire_min_votes, config.acquire_max_candidates)
        if not alignments:
            return []

        best = max(alignments, key=lambda a: a.score)
        # Look-alikes share the winner's corpus words, not the (maybe misheard) hypothesis words.
        # Every one is aligned: a formula phrase can recur in hundreds of places.
        corpus = self._index.words
        lookalikes = self._candidate_alignments(words, [(h, corpus[p]) for h, p in best.pairs],
                                                config.acquire_rival_votes, None)
```

`_candidate_alignments`:

```python
    def _candidate_alignments(self, words: Sequence[str], voters: Iterable[tuple[int, str]], min_votes: int,
                              limit: int | None) -> list[Alignment]:
        """Align regions where at least `min_votes` (hypothesis index, word) voters line up; at most `limit`."""
        ...
        for i, word in voters:
            positions = self._index.positions(word)
        ...
            if votes < min_votes or (limit is not None and len(chosen) >= limit):
                break
```

Update the module docstring sentence on look-alikes to match.

- [ ] **Step 4: Run tests** — regressions pass, `tests/test_engine_tracker.py` passes, full suite passes.

- [ ] **Step 5: Measure**: `uv run python scripts/replay_m3.py --tune`; compare with baseline against the acceptance rule; check Acquire cost stays small (`time` of the replay vs baseline). Record the comparison for the report.

- [ ] **Step 6: Commit** `Search look-alikes by the winner's corpus words`

---

### Task 5: Rule P — wider margin for already-recited rivals

**Files:**
- Modify: `src/tilavet/engine/tracker.py` (`EngineConfig`, `_track`)
- Test: `tests/test_engine_regressions.py`

- [ ] **Step 1: Write the failing test**

```python
def test_going_back_is_not_progress(index):
    # muhammad-ayyoub-1: after 22:56 the reciter repeats 22:55; its "الذين كفروا" matches 22:57's opening.
    engine = PositionEngine(index)
    texts = [
        "وليعلم الذين اوتوا العلم انه الحق من ربك فيومنوا به فتخبت له قلوبهم وان الله لهاد الذين امنوا الى صراط مستقيم "
        "ولا يزال الذين كفروا في مريه منه حتي تاتيهم الساعه بغته او ياتيهم عذاب يوم عقيم",
        "الملك يوميذ لله يحكم بينهم فالذين امنوا وعملوا الصالحات في جنات النعيم",
        "في جنات النعيولا يزال الذين كفر",
    ]

    assert AyahRef(22, 57) not in feed(engine, *texts)
```

- [ ] **Step 2: Run, expect failure** (22:57 confirmed). If 22:56 is not confirmed by the second text, use the exact cached tiny-hard window texts of `muhammad-ayyoub-1` (t = 44–68) instead.

- [ ] **Step 3: Implement**

```python
    past_margin: int = 3  # rivals over ayahs already recited: likely a repetition, contest more readily
```

In `_track`:

```python
        rivals = [a for a in alignments if not _overlaps(a, alignment) and a.score > alignment.score - self._margin(a)]
```

```python
    def _margin(self, rival: Alignment) -> int:
        recited = all(self._index.ordinal_at(p) in self._confirmed for p in rival.positions)
        return self._config.past_margin if recited else self._config.track_margin
```

- [ ] **Step 4: Run tests** — new test passes, full suite passes.

- [ ] **Step 5: Measure** `--tune` (with L) and the alternative `--tune past_margin=2 track_margin=3`; pick by the acceptance rule; record both.

- [ ] **Step 6: Commit** `Contest words that repeat recited ayahs`

---

### Task 6: Freeze checkpoint (İsmail)

- [ ] Summarise per rule: tiny/NVIDIA wrong, recall and p50 deltas per set and condition vs baseline. If a rule breaks the acceptance rule, ask İsmail; if remaining wrong meals in the tuning sets show a new mechanism, report it (no new rule without approval).
- [ ] On approval: record the freeze commit in the spec (`Kurallar <sha>'de donduruldu`), commit `Record M5 rule freeze`.

### Task 7: Open blind2 (İsmail approval)

- [ ] Verify 3 × 40 clips in `data/derived/m5/asr-blind2/quran-asr-tiny/`.
- [ ] `uv run python scripts/replay_m3.py --set blind2` → `reports/m5-blind.md`; commit `Open blind2 set`.
- [ ] Report gates to İsmail; then `--debug` per wrong meal for mechanisms (`--set blind2 --debug quran-asr-tiny/<condition>`).

### Task 8: Non-Quran speech and resources (İsmail, ~1 h)

**Files:**
- Create: `scripts/sample_process.py`

- [ ] **Step 1: Sampler**

```python
"""Sample CPU % and RSS of a running process until it exits.

    uv run python scripts/sample_process.py <pid>
"""

import argparse
import statistics
import subprocess
import time

INTERVAL_S = 5.0
KB_PER_MB = 1024


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    args = parser.parse_args()

    cpu, rss = [], []
    while True:
        result = subprocess.run(["ps", "-o", "%cpu=,rss=", "-p", str(args.pid)], capture_output=True, text=True)
        if result.returncode != 0:
            break
        c, r = result.stdout.split()
        cpu.append(float(c.replace(",", ".")))
        rss.append(int(r) / KB_PER_MB)
        time.sleep(INTERVAL_S)

    print(f"samples {len(cpu)}, CPU median {statistics.median(cpu):.1f}% max {max(cpu):.1f}%, "
          f"RSS max {max(rss):.0f} MB")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Session** — İsmail plays ~30 min Turkish sohbet + ~30 min Arabic hutbe from the phone; headphone connected, not worn. Run `live.py --output "CMF Buds 2a"` in the background and the sampler on its Python PID.
- [ ] **Step 3: Review** every played meal: listen to the recording around it (`ffmpeg`/`afplay` excerpt) and check whether that ayah was actually recited. Count wrong meals per hour.
- [ ] **Step 4: Commit** `Add process sampler`

### Task 9: M5 report and GO/NO-GO

- [ ] `reports/m5-feasibility.md` (Turkish, M4 report format): rules and their tuning cost, blind2 gates (incl. rule-of-three, 30 s pause), non-Quran speech, resources, model choice, limitations (Husary voice in dev, leakage, small sample, short live tests), GO/NO-GO recommendation.
- [ ] README: M5 row and commands. Commit `Add M5 feasibility report`. İsmail decides.
