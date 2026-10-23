"""M1 paper-feasibility analyses (U1 duration/backlog, U2 uniqueness, U3 duplicates).

Writes reports/m1-results.md. Deterministic for fixed inputs.
"""

import csv
import json
import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from tilavet.corpus import AyahRef, MealUnit, load_tanzil, meal_units, normalize, strip_basmala
from tilavet.feasibility import Unit, global_prefix_lengths, simulate_backlog, track_prefix_lengths

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
OUT = ROOT / "reports" / "m1-results.md"

TRANSLATION = "tr.diyanet"
ALT_TRANSLATION = "tr.vakfi"
VOICE = "yelda"

GLOBAL_MAX_K = 40
TRACK_WINDOW = 3
SPEEDS = (1.0, 1.25)
LAG_LIMIT_S = 15.0
MS = 1000.0


@dataclass(frozen=True)
class AyahTiming:
    from_s: float
    to_s: float
    word_ends_s: tuple[float, ...]  # end of word i (0-based); empty if unusable
    first_word_s: float | None


def pct(values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile, q in [0, 100]."""
    ordered = sorted(values)
    rank = max(1, math.ceil(q / 100 * len(ordered)))
    return ordered[rank - 1]


def share(values: Sequence[bool]) -> str:
    return f"{100 * sum(values) / len(values):.1f}%"


def load_words() -> dict[AyahRef, list[str]]:
    quran = load_tanzil(RAW / "quran-simple-clean.txt")
    return {ref: normalize(strip_basmala(ref, text)).split() for ref, text in sorted(quran.items())}


def load_timings(words: dict[AyahRef, list[str]]) -> dict[str, dict[AyahRef, AyahTiming]]:
    result = {}

    for path in sorted(RAW.glob("timings-*.json")):
        name = path.stem.split("-", 2)[2]
        per_ayah = {}
        for audio in json.loads(path.read_text())["audio_files"]:
            for verse in audio["verse_timings"]:
                sura, aya = map(int, verse["verse_key"].split(":"))
                ref = AyahRef(sura, aya)
                segments = sorted((s for s in verse["segments"] if len(s) == 3), key=lambda s: s[0])
                indexes = [s[0] for s in segments]

                # Word-level times are only trusted when segment indexes map 1:1 to our tokens.
                usable = indexes == list(range(1, len(words[ref]) + 1))
                per_ayah[ref] = AyahTiming(
                    from_s=verse["timestamp_from"] / MS,
                    to_s=verse["timestamp_to"] / MS,
                    word_ends_s=tuple(s[2] / MS for s in segments) if usable else (),
                    first_word_s=segments[0][1] / MS if usable else None,
                )
        result[name] = per_ayah

    return result


def load_meal_seconds() -> dict[tuple[int, int], float]:
    path = DERIVED / f"meal-durations-{TRANSLATION}-{VOICE}.csv"
    with path.open() as f:
        return {(int(r["sura"]), int(r["first"])): float(r["seconds"]) for r in csv.DictReader(f)}


def seconds_to_hear(timing: AyahTiming, k: int | None) -> float | None:
    if k is None or not timing.word_ends_s or k > len(timing.word_ends_s):
        return None

    return timing.word_ends_s[k - 1] - timing.first_word_s


# --- U3 -------------------------------------------------------------------


def section_duplicates(words, meals) -> list[str]:
    groups = defaultdict(list)
    for ref, tokens in words.items():
        groups[" ".join(tokens)].append(ref)
    groups = [refs for refs in groups.values() if len(refs) > 1]

    lines = [
        "## U3 — Metni birebir aynı ayetler",
        "",
        f"Normalize Arapça metni aynı olan **{len(groups)} grup**, toplam **{sum(map(len, groups))} ayet**.",
        "",
        "| Meal | Meali de aynı grup | Farklı grup |",
        "|---|---|---|",
    ]
    differing = {}
    for trans_id, meal in meals.items():
        diff = [g for g in groups if len({meal[r] for r in g}) > 1]
        differing[trans_id] = diff
        lines.append(f"| {trans_id} | {len(groups) - len(diff)} | {len(diff)} |")

    lines += ["", f"{TRANSLATION} için mealleri farklı olan gruplar (ilk 10):", ""]
    for group in differing[TRANSLATION][:10]:
        refs = ", ".join(f"{r.sura}:{r.aya}" for r in group)
        lines.append(f"- {refs}")

    return lines + [""]


# --- U2 -------------------------------------------------------------------


def section_uniqueness(words, timings) -> tuple[list[str], dict[AyahRef, int | None]]:
    refs = list(words)
    global_k = dict(zip(refs, global_prefix_lengths([words[r] for r in refs], GLOBAL_MAX_K), strict=True))

    track_k: dict[AyahRef, int | None] = {}
    by_sura = defaultdict(list)
    for ref in refs:
        by_sura[ref.sura].append(ref)
    for sura_refs in by_sura.values():
        ks = track_prefix_lengths([words[r] for r in sura_refs], TRACK_WINDOW)
        track_k.update(zip(sura_refs, ks, strict=True))

    lines = [
        "## U2 — Tekil tanıma için gereken kelime sayısı",
        "",
        "- **Global (Acquire):** konum bilinmiyor; ayetin ilk k kelimesi Kur'an'ın tamamında tek geçmeli.",
        f"- **Track:** önceki ayet biliniyor; rakipler ±{TRACK_WINDOW} ayet ve önceki ayetin herhangi bir kelimesinden yeniden başlama.",
        "",
        "| Mod | Çözülen | p50 | p90 | p99 | ≤ 1 kelime | ≤ 3 kelime | Ayet dışına taşan | Çözülemeyen |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for mode, ks in (("Global", global_k), ("Track", track_k)):
        considered = {r: k for r, k in ks.items() if not (mode == "Track" and r.aya == 1)}
        solved = [k for k in considered.values() if k is not None]
        spill = [k > len(words[r]) for r, k in considered.items() if k is not None]
        lines.append(
            f"| {mode} | {len(solved)}/{len(considered)} | {pct(solved, 50)} | {pct(solved, 90)} | "
            f"{pct(solved, 99)} | {share([k <= 1 for k in solved])} | {share([k <= 3 for k in solved])} | "
            f"{share(spill)} | {len(considered) - len(solved)} |"
        )

    lines += [
        "",
        "Saniye karşılığı (ilk kelimenin başından k. kelimenin sonuna; kelime timing'i eşleşen ayetler):",
        "",
        "| Okuyucu | Kapsam | Track p50 | Track p90 | Global p50 | Global p90 |",
        "|---|---|---|---|---|---|",
    ]
    for name, per_ayah in timings.items():
        usable = sum(bool(t.word_ends_s) for t in per_ayah.values())
        track_s = [s for r in refs if (s := seconds_to_hear(per_ayah[r], track_k[r])) is not None]
        global_s = [s for r in refs if (s := seconds_to_hear(per_ayah[r], global_k[r])) is not None]
        lines.append(
            f"| {name} | {usable}/{len(per_ayah)} | {pct(track_s, 50):.1f} s | {pct(track_s, 90):.1f} s | "
            f"{pct(global_s, 50):.1f} s | {pct(global_s, 90):.1f} s |"
        )

    hardest = sorted(((k, r) for r, k in global_k.items() if k is not None), reverse=True)[:5]
    unresolved = [r for r, k in global_k.items() if k is None]
    lines += [
        "",
        f"Global modda en zor ayetler: {', '.join(f'{r.sura}:{r.aya} (k={k})' for k, r in hardest)}.",
        f"Global modda {GLOBAL_MAX_K} kelimede çözülemeyen: {len(unresolved)} ayet "
        f"(örnek: {', '.join(f'{r.sura}:{r.aya}' for r in unresolved[:8])}).",
        "",
    ]
    return lines, track_k


# --- U1 -------------------------------------------------------------------


def unit_window(unit: MealUnit, per_ayah: dict[AyahRef, AyahTiming]) -> tuple[float, float]:
    return per_ayah[AyahRef(unit.sura, unit.first)].from_s, per_ayah[AyahRef(unit.sura, unit.last)].to_s


def early_available(ref: AyahRef, per_ayah, track_k, fallback_s: float) -> float:
    """When `ref` is identified. Without word timing, assume the reciter's p90 identification time."""
    timing = per_ayah[ref]
    heard = seconds_to_hear(timing, track_k.get(ref))
    if heard is None:
        return timing.from_s + fallback_s

    return timing.first_word_s + heard


def section_duration(units, meal_s, timings, track_k) -> list[str]:
    total_meal_h = sum(meal_s.values()) / 3600
    lines = [
        "## U1 — Meal süresi ve birikme",
        "",
        f"Meal: {TRANSLATION}, {len(units)} birim, ses: {VOICE} (macOS `say`, varsayılan hız). "
        f"Toplam meal süresi @1.0x: **{total_meal_h:.2f} saat**.",
        "",
        "Oran = meal süresi ÷ tilavet süresi (birim bazında; tilavet süresi ayetler arası duraklamayı içerir).",
        "",
        "| Okuyucu | Tilavet (saat) | Toplam oran @1.0x | Birim oranı p50 | p90 | > 1 olan birim @1.0x | @1.25x |",
        "|---|---|---|---|---|---|---|",
    ]

    for name, per_ayah in timings.items():
        recitation = []
        for unit in units:
            start, end = unit_window(unit, per_ayah)
            recitation.append(end - start)
        ratios = [meal_s[(u.sura, u.first)] / r for u, r in zip(units, recitation, strict=True)]
        lines.append(
            f"| {name} | {sum(recitation) / 3600:.2f} | {total_meal_h / (sum(recitation) / 3600):.2f} | "
            f"{pct(ratios, 50):.2f} | {pct(ratios, 90):.2f} | {share([x > 1 for x in ratios])} | "
            f"{share([x > 1.25 for x in ratios])} |"
        )

    lines += [
        "",
        "### Birikme simülasyonu",
        "",
        "Mealler sırayla, üst üste binmeden çalınır; her sure ayrı simüle edilir. Gecikme (lag) = meal başlangıcı − "
        "mealin çalınabilir olduğu an.",
        "",
        "- **end:** birim tamamen okunduktan sonra çalınabilir.",
        "- **early:** birimin ilk ayeti Track modunda tekil olduğu anda çalınabilir (U2); kelime timing'i "
        "yoksa okuyucunun Track p90 süresi varsayılır.",
        "- **last:** birimin son ayeti tanındığında çalınabilir (okunmamış ayetin anlamı önceden duyulmaz).",
        "- **Onset − son:** meal başlangıcı − birimin tilavet bitişi (negatif = okuyucu birimi bitirmeden meal başladı).",
        "",
        f"| Okuyucu | Politika | Hız | Lag p50 | Lag p90 | Lag max | > {LAG_LIMIT_S:.0f} s lag olan birim | "
        "Onset − son p50 | p90 | En kötü sureler (max lag) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    by_sura = defaultdict(list)
    for unit in units:
        by_sura[unit.sura].append(unit)

    for name, per_ayah in timings.items():
        track_s = [s for r, t in per_ayah.items() if (s := seconds_to_hear(t, track_k.get(r))) is not None]
        fallback_s = pct(track_s, 90)

        for policy in ("end", "early", "last"):
            for speed in SPEEDS:
                lags, onsets, worst = [], [], []
                for sura, sura_units in by_sura.items():
                    sim_units, ends = [], []
                    for unit in sura_units:
                        _, end = unit_window(unit, per_ayah)
                        anchor = unit.refs[0] if policy == "early" else unit.refs[-1]
                        available = end if policy == "end" else early_available(anchor, per_ayah, track_k, fallback_s)
                        sim_units.append(Unit(available_s=available, meal_s=meal_s[(unit.sura, unit.first)]))
                        ends.append(end)
                    sura_lags = simulate_backlog(sim_units, speed)
                    lags += sura_lags
                    onsets += [u.available_s + lag - end for u, lag, end in zip(sim_units, sura_lags, ends, strict=True)]
                    worst.append((max(sura_lags), sura))

                worst_text = ", ".join(f"{s} ({m:.0f} s)" for m, s in sorted(worst, reverse=True)[:3])
                lines.append(
                    f"| {name} | {policy} | {speed}x | {pct(lags, 50):.1f} s | {pct(lags, 90):.1f} s | "
                    f"{max(lags):.0f} s | {share([x > LAG_LIMIT_S for x in lags])} | "
                    f"{pct(onsets, 50):.1f} s | {pct(onsets, 90):.1f} s | {worst_text} |"
                )

    return lines + [""]


def main() -> None:
    words = load_words()
    meals = {t: load_tanzil(RAW / f"{t}.txt") for t in (TRANSLATION, ALT_TRANSLATION)}
    units = meal_units(meals[TRANSLATION])
    timings = load_timings(words)
    meal_s = load_meal_seconds()

    uniqueness, track_k = section_uniqueness(words, timings)
    lines = [
        "# M1 sonuçları (otomatik üretildi: scripts/analyze_m1.py)",
        "",
        "Girdiler data/manifest.json'daki sha256 ile sabitlenmiştir.",
        "",
        *section_duration(units, meal_s, timings, track_k),
        *uniqueness,
        *section_duplicates(words, meals),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
