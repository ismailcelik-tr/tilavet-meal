# tilavet-meal

Feasibility prototype: listen to Quran recitation and play the verified Turkish meal (translation of meaning) of the ayah being recited, with minimal delay. Mac-first; mobile only after the approach is validated.

Runtime translates nothing. It identifies the position in a closed corpus (6,236 ayahs) and plays a pre-verified meal.

## Status

| Milestone | Scope | State |
|---|---|---|
| M1 | Corpus, meal units, paper feasibility (no ML) | Done: [report](reports/m1-feasibility.md) (Turkish) |
| M2 | Acoustic model bake-off on Mac | Done: [report](reports/m2-feasibility.md) (Turkish), NVIDIA FastConformer hybrid selected |
| M3 | Position engine, offline real-time simulation | In progress: engine + [interim results](reports/m3-results.md) |
| M4–M5 | Live mic + playback, robustness, go/no-go | Planned |

## Run

```sh
uv sync
uv run python scripts/fetch_data.py            # pinned inputs -> data/raw, sha256 in data/manifest.json
uv run python scripts/render_meal_durations.py # macOS `say`, ~20 min
uv run python scripts/analyze_m1.py            # -> reports/m1-results.md
uv run pytest

# M2: one model per process, each model family in its own dependency group
uv run python scripts/build_smoke_set.py
uv run --group onnx python scripts/bench_asr.py --model quran-asr-tiny --set smoke
uv run --group nemo python scripts/bench_asr.py --model nvidia-fc-ctc --set smoke
uv run --group mlx  python scripts/bench_asr.py --model whisper-large-v3-turbo --set smoke
uv run python scripts/report_m2.py --set smoke
# held-out benchmark (gated): see scripts/build_qlab_set.py, then --set qlab
```

## Data sources

Raw data is downloaded locally and not redistributed in this repository.

- Quran text: [Tanzil Project](https://tanzil.net), `quran-simple-clean`, CC BY 3.0 (verbatim use only).
- Turkish translations: [Tanzil](https://tanzil.net/trans/) `tr.diyanet`, `tr.vakfi`; non-commercial use only.
- Recitation timings: [quran.com](https://quran.com) API, used for evaluation only.
- Held-out benchmark: [Quran-Lab/quranic-asr-benchmark](https://huggingface.co/datasets/Quran-Lab/quranic-asr-benchmark), gated, research evaluation only; only aggregate scores are published here.
- Per-ayah recitations: [EveryAyah](https://everyayah.com), evaluation only, not redistributed.
