# tilavet-meal

Feasibility prototype: listen to Quran recitation and play the verified Turkish meal (translation of meaning) of the ayah being recited, with minimal delay. Mac-first; mobile only after the approach is validated.

Runtime translates nothing. It identifies the position in a closed corpus (6,236 ayahs) and plays a pre-verified meal.

## Status

| Milestone | Scope | State |
|---|---|---|
| M1 | Corpus, meal units, paper feasibility (no ML) | Done: [report](reports/m1-feasibility.md) (Turkish) |
| M2 | Acoustic model bake-off on Mac | Done: [report](reports/m2-feasibility.md) (Turkish), NVIDIA FastConformer hybrid selected |
| M3 | Position engine, offline real-time simulation | Done: [report](reports/m3-feasibility.md) (Turkish), 0 wrong meals clean/10 dB; NVIDIA 1.3% at 0 dB |
| M4 | Live mic + headphone playback, loopback, blind set | Done: [report](reports/m4-feasibility.md) (Turkish), 0 wrong meals live; blind hard ~1%, mujawwad weakest; tiny primary |
| M5 | Robustness, new blind set, non-Quran speech, go/no-go | Done: [report](reports/m5-feasibility.md) (Turkish), 0 wrong of 837 blind meals; GO recommended |
| M6 | iOS spike: Swift port, on-device ASR, measurements | Done: [report](reports/m6-feasibility.md) (Turkish), Swift core equals Python; iPhone 17: 0 wrong of 68 live meals, RTF 0.12, 157 MB, works locked |

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

# M3: ASR passes one at a time (shared CPU skews measured latency)
uv run python scripts/build_streams.py
uv run --group onnx python scripts/asr_windows.py --model quran-asr-tiny --condition clean|noisy|hard
uv run --group nemo python scripts/asr_windows.py --model nvidia-fc-rnnt --condition clean|noisy|hard
uv run python scripts/replay_m3.py             # -> reports/m3-results.md

# M4: loopback (MacBook speaker -> mic), blind set, live app
uv run --group onnx --group audio python scripts/loopback.py --streams shuraim-2 --volume 50
uv run python scripts/build_streams.py --set blind
uv run --group onnx python scripts/asr_windows.py --set blind --model quran-asr-tiny --condition clean|noisy|hard
uv run python scripts/replay_m3.py --set blind # -> reports/m4-blind.md
uv run python scripts/render_meals.py          # macOS `say`, ~20 min, ~430 MB
uv run --group onnx --group audio python scripts/live.py --output "<headphone name>"

# M5: blind2 set (tiny), rule comparison on opened sets, process sampling
uv run python scripts/build_streams.py --set blind2
uv run --group onnx python scripts/asr_windows.py --set blind2 --model quran-asr-tiny --condition clean|noisy|hard
uv run python scripts/replay_m3.py --tune past_margin=3   # opened sets only
uv run python scripts/replay_m3.py --set blind2          # -> reports/m5-blind.md
uv run python scripts/sample_process.py <pid>

# M6: golden vectors, iOS app on a paired iPhone, device runs
uv run python scripts/export_golden.py
cd ios/TilavetCore && swift test && cd -
uv run --group piper python scripts/render_meals_piper.py   # Piper Eren, HE-AAC 16 kbps, ~20 min
sh scripts/ios_resources.sh
uv run python scripts/device.py build
uv run --group audio python scripts/device_loopback.py --volume 50
uv run python scripts/package_options.py
```

## Data sources

Raw data is downloaded locally and not redistributed in this repository.

- Quran text: [Tanzil Project](https://tanzil.net), `quran-simple-clean`, CC BY 3.0 (verbatim use only).
- Turkish translations: [Tanzil](https://tanzil.net/trans/) `tr.diyanet`, `tr.vakfi`; non-commercial use only.
- Recitation timings: [quran.com](https://quran.com) API, used for evaluation only.
- Held-out benchmark: [Quran-Lab/quranic-asr-benchmark](https://huggingface.co/datasets/Quran-Lab/quranic-asr-benchmark), gated, research evaluation only; only aggregate scores are published here.
- Per-ayah recitations: [EveryAyah](https://everyayah.com), evaluation only, not redistributed.
