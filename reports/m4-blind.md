# M4 kör set sonuçları (otomatik: scripts/replay_m3.py --blind)

EngineConfig: `EngineConfig(acquire_min_matched=4, acquire_min_score=6, acquire_margin=3, acquire_min_votes=3, acquire_max_candidates=8, acquire_rival_votes=2, diagonal_tolerance=8, common_word_limit=500, track_back=30, track_ahead=50, track_min_score=3, track_tie_slack=0, track_margin=2, confirm_words=2, distinct_window=3, prefix_slack=1, max_skip=2, jump_extra=1, lost_after=4, min_words_for_miss=3)`

Tanımlar `m3-results.md` ile aynı. Üst sınır: yanlış 0 ise üçler kuralı (%95, 3/meal), değilse yok.

| Koşu | Yanlış üst sınır | Akış | Meal | Yanlış | Geç | Recall | Mükerrer | Lost | Başlangıçtan p50 | p90 | Birim sonundan p50 | p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nvidia-fc-rnnt / clean | – | 40 | 295 | **0.3%** | 0.0% | 96.1% | 0.0% | 8 | 3.7 s | 7.2 s | -12.8 s | -2.5 s |
| nvidia-fc-rnnt / hard | – | 40 | 276 | **1.1%** | 0.0% | 88.6% | 0.0% | 19 | 3.0 s | 7.2 s | -13.3 s | -2.8 s |
| nvidia-fc-rnnt / noisy | – | 40 | 294 | **0.3%** | 0.3% | 95.4% | 0.0% | 7 | 3.3 s | 7.0 s | -13.2 s | -2.7 s |
| quran-asr-tiny / clean | ≤1.0% | 40 | 292 | **0.0%** | 0.0% | 95.4% | 0.0% | 5 | 4.1 s | 7.1 s | -12.8 s | -2.0 s |
| quran-asr-tiny / hard | – | 40 | 287 | **1.0%** | 0.3% | 92.5% | 0.0% | 17 | 4.0 s | 8.0 s | -12.8 s | -2.5 s |
| quran-asr-tiny / noisy | ≤1.0% | 40 | 292 | **0.0%** | 0.0% | 95.1% | 0.0% | 7 | 4.2 s | 7.4 s | -12.7 s | -2.4 s |

## Ses tanıma hatası (ayet klipleri)

| Koşu | CER |
|---|---|
| nvidia-fc-rnnt / clean | 2.12% |
| nvidia-fc-rnnt / hard | 9.83% |
| nvidia-fc-rnnt / noisy | 2.11% |
| quran-asr-tiny / clean | 0.34% |
| quran-asr-tiny / hard | 3.54% |
| quran-asr-tiny / noisy | 0.84% |
