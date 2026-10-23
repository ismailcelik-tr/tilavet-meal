"""Convert the Quran-Lab held-out benchmark into our eval-set format.

Download first (gated, needs `hf auth login` and approved access):
    snapshot_download("Quran-Lab/quranic-asr-benchmark", repo_type="dataset", local_dir="data/raw/qlab")
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "qlab"
OUT = ROOT / "data" / "derived" / "sets" / "qlab.jsonl"


def main() -> None:
    rows = []
    for line in (SOURCE / "benchmark.jsonl").read_text(encoding="utf-8").splitlines():
        clip = json.loads(line)
        rows.append(
            {
                "id": clip["id"],
                "source": clip["source"],
                "audio": str((SOURCE / clip["audio"]).relative_to(ROOT)),
                "text": clip["reference_text"],
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"wrote {OUT.relative_to(ROOT)} ({len(rows)} clips)")


if __name__ == "__main__":
    main()
