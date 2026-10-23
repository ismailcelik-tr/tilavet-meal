"""Score every benchmarked model on a set; write reports/m2-<set>.md."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from tilavet.asr import MODELS
from tilavet.eval import fold_alef, prefix_match, score

ROOT = Path(__file__).resolve().parents[1]
SETS = ROOT / "data" / "derived" / "sets"
RESULTS = ROOT / "data" / "derived" / "bench"
REPORTS = ROOT / "reports"

PREFIX_WORDS = 3
ALL = "all"


def _pct(x: float) -> str:
    return f"{100 * x:.2f}%"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", required=True)
    args = parser.parse_args()

    rows = {r["id"]: r for r in map(json.loads, (SETS / f"{args.set}.jsonl").read_text().splitlines())}
    sources = sorted({r["source"] for r in rows.values()})
    out = RESULTS / args.set

    lines = [
        f"# M2 sonuçları — set: `{args.set}` (otomatik: scripts/report_m2.py)",
        "",
        f"{len(rows)} klip, kaynaklar: {', '.join(sources)}. Metrikler normalize metin üzerinde, korpus düzeyinde.",
        "CER-a = elif'siz CER (Uthmani/standart imla farkını nötrler). "
        f"İlk-{PREFIX_WORDS} = ilk {PREFIX_WORDS} kelimenin birebir doğru tanındığı klip oranı.",
        "",
        "| Model | Lisans | Kaynak | CER | CER-a | WER | İlk-3 |",
        "|---|---|---|---|---|---|---|",
    ]
    speed = []

    for name in MODELS:
        hyp_path = out / f"{name}.jsonl"
        if not hyp_path.exists():
            continue

        hyps = {h["id"]: h["text"] for h in map(json.loads, hyp_path.read_text().splitlines())}
        groups = defaultdict(list)
        for clip_id, row in rows.items():
            groups[row["source"]].append((row["text"], hyps[clip_id]))
            groups[ALL].append((row["text"], hyps[clip_id]))

        for source in [*sources, ALL]:
            refs, texts = zip(*groups[source], strict=True)
            plain = score(refs, texts)
            folded = score([fold_alef(r) for r in refs], [fold_alef(t) for t in texts])
            prefix = sum(prefix_match(r, t, PREFIX_WORDS) for r, t in groups[source]) / len(refs)
            label = f"**{source}**" if source == ALL else source
            lines.append(
                f"| {name} | {MODELS[name].license} | {label} | {_pct(plain.cer)} | {_pct(folded.cer)} | "
                f"{_pct(plain.wer)} | {_pct(prefix)} |"
            )

        speed.append(json.loads((out / f"{name}.summary.json").read_text()))

    lines += [
        "",
        "## Hız ve bellek (M5 MacBook Pro, 16 GB)",
        "",
        "| Model | Yükleme | Ses | İşlem | RTF | Peak RSS |",
        "|---|---|---|---|---|---|",
    ]
    for s in speed:
        lines.append(
            f"| {s['model']} | {s['load_s']} s | {s['audio_s']} s | {s['proc_s']} s | {s['rtf']} | {s['peak_rss_mb']} MB |"
        )
    lines += [
        "",
        "Yükleme süresi ilk çalıştırmada model indirmeyi içerebilir. RTF = işlem ÷ ses süresi. "
        "Peak RSS GPU (MLX/MPS) belleğini içermez.",
        "",
    ]

    path = REPORTS / f"m2-{args.set}.md"
    path.write_text("\n".join(lines))
    print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
