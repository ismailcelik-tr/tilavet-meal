# tilavet-meal

Feasibility prototype: listen to Quran recitation and play the verified Turkish meal (translation of meaning) of the ayah being recited, with minimal delay. Mac-first; mobile only after the approach is validated.

Runtime translates nothing. It identifies the position in a closed corpus (6,236 ayahs) and plays a pre-verified meal.

## Status

| Milestone | Scope | State |
|---|---|---|
| M1 | Corpus, meal units, paper feasibility (no ML) | Done: [report](reports/m1-feasibility.md) (Turkish) |
| M2 | Acoustic model bake-off on Mac | Next |
| M3–M5 | Position engine, live mic + playback, robustness, go/no-go | Planned |

## Run

```sh
uv sync
uv run python scripts/fetch_data.py            # pinned inputs -> data/raw, sha256 in data/manifest.json
uv run python scripts/render_meal_durations.py # macOS `say`, ~20 min
uv run python scripts/analyze_m1.py            # -> reports/m1-results.md
uv run pytest
```

## Data sources

Raw data is downloaded locally and not redistributed in this repository.

- Quran text: [Tanzil Project](https://tanzil.net), `quran-simple-clean`, CC BY 3.0 (verbatim use only).
- Turkish translations: [Tanzil](https://tanzil.net/trans/) `tr.diyanet`, `tr.vakfi`; non-commercial use only.
- Recitation timings: [quran.com](https://quran.com) API, used for evaluation only.
