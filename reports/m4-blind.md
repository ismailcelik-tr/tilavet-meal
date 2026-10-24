# Kör set sonuçları: blind (otomatik: scripts/replay_m3.py --set blind)

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

## 30 s duraklama ve ASR süresi

| Koşu | Duraklamada meal (10 s sonra) | ASR süresi p50 / p90 (adım 1 s) |
|---|---|---|
| nvidia-fc-rnnt / clean | 0 | 0.191 / 0.202 s |
| nvidia-fc-rnnt / hard | 0 | 0.190 / 0.201 s |
| nvidia-fc-rnnt / noisy | 0 | 0.194 / 0.217 s |
| quran-asr-tiny / clean | 0 | 0.037 / 0.041 s |
| quran-asr-tiny / hard | 0 | 0.035 / 0.040 s |
| quran-asr-tiny / noisy | 0 | 0.035 / 0.040 s |

## Okuyucu bazında

| Koşu | Akış | Meal | Yanlış | Geç | Recall | Mükerrer | Lost | Başlangıçtan p50 | p90 | Birim sonundan p50 | p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nvidia-fc-rnnt / clean / alafasy | 10 | 72 | **0.0%** | 0.0% | 98.6% | 0.0% | 3 | 3.7 s | 6.2 s | -12.5 s | -2.6 s |
| nvidia-fc-rnnt / clean / maher-muaiqly | 10 | 91 | **0.0%** | 0.0% | 98.9% | 0.0% | 1 | 2.9 s | 5.2 s | -8.3 s | -1.6 s |
| nvidia-fc-rnnt / clean / minshawi-mujawwad | 10 | 54 | **1.9%** | 0.0% | 88.3% | 0.0% | 1 | 6.2 s | 10.9 s | -23.1 s | -3.9 s |
| nvidia-fc-rnnt / clean / muhammad-ayyoub | 10 | 78 | **0.0%** | 0.0% | 96.3% | 0.0% | 3 | 3.7 s | 6.2 s | -14.1 s | -4.9 s |
| nvidia-fc-rnnt / hard / alafasy | 10 | 72 | **0.0%** | 0.0% | 98.6% | 0.0% | 2 | 3.0 s | 5.6 s | -14.6 s | -2.6 s |
| nvidia-fc-rnnt / hard / maher-muaiqly | 10 | 90 | **0.0%** | 0.0% | 97.8% | 0.0% | 1 | 2.4 s | 4.7 s | -8.7 s | -2.3 s |
| nvidia-fc-rnnt / hard / minshawi-mujawwad | 10 | 36 | **8.3%** | 0.0% | 51.7% | 0.0% | 14 | 9.2 s | 35.2 s | -17.2 s | -6.6 s |
| nvidia-fc-rnnt / hard / muhammad-ayyoub | 10 | 78 | **0.0%** | 0.0% | 96.3% | 0.0% | 2 | 3.2 s | 5.9 s | -14.3 s | -5.7 s |
| nvidia-fc-rnnt / noisy / alafasy | 10 | 72 | **0.0%** | 0.0% | 98.6% | 0.0% | 2 | 3.2 s | 5.2 s | -14.6 s | -2.7 s |
| nvidia-fc-rnnt / noisy / maher-muaiqly | 10 | 91 | **0.0%** | 0.0% | 98.9% | 0.0% | 1 | 2.5 s | 4.8 s | -8.6 s | -1.9 s |
| nvidia-fc-rnnt / noisy / minshawi-mujawwad | 10 | 53 | **1.9%** | 1.9% | 85.0% | 0.0% | 2 | 6.7 s | 11.2 s | -23.9 s | -4.3 s |
| nvidia-fc-rnnt / noisy / muhammad-ayyoub | 10 | 78 | **0.0%** | 0.0% | 96.3% | 0.0% | 2 | 3.4 s | 5.9 s | -14.1 s | -5.7 s |
| quran-asr-tiny / clean / alafasy | 10 | 72 | **0.0%** | 0.0% | 98.6% | 0.0% | 1 | 3.7 s | 6.4 s | -13.7 s | -2.8 s |
| quran-asr-tiny / clean / maher-muaiqly | 10 | 90 | **0.0%** | 0.0% | 97.8% | 0.0% | 2 | 3.4 s | 6.6 s | -7.7 s | -1.5 s |
| quran-asr-tiny / clean / minshawi-mujawwad | 10 | 53 | **0.0%** | 0.0% | 88.3% | 0.0% | 0 | 6.2 s | 11.0 s | -22.4 s | -3.6 s |
| quran-asr-tiny / clean / muhammad-ayyoub | 10 | 77 | **0.0%** | 0.0% | 95.1% | 0.0% | 2 | 4.1 s | 6.0 s | -13.9 s | -5.9 s |
| quran-asr-tiny / hard / alafasy | 10 | 70 | **0.0%** | 1.4% | 95.9% | 0.0% | 1 | 3.9 s | 7.0 s | -14.1 s | -2.8 s |
| quran-asr-tiny / hard / maher-muaiqly | 10 | 90 | **0.0%** | 0.0% | 97.8% | 0.0% | 2 | 3.2 s | 5.7 s | -7.5 s | -1.3 s |
| quran-asr-tiny / hard / minshawi-mujawwad | 10 | 51 | **3.9%** | 0.0% | 80.0% | 0.0% | 12 | 7.9 s | 15.1 s | -21.7 s | -2.9 s |
| quran-asr-tiny / hard / muhammad-ayyoub | 10 | 76 | **1.3%** | 0.0% | 92.6% | 0.0% | 2 | 4.1 s | 6.0 s | -13.9 s | -6.3 s |
| quran-asr-tiny / noisy / alafasy | 10 | 72 | **0.0%** | 0.0% | 98.6% | 0.0% | 1 | 4.0 s | 6.4 s | -13.2 s | -1.9 s |
| quran-asr-tiny / noisy / maher-muaiqly | 10 | 91 | **0.0%** | 0.0% | 98.9% | 0.0% | 2 | 3.6 s | 6.5 s | -7.3 s | -1.4 s |
| quran-asr-tiny / noisy / minshawi-mujawwad | 10 | 52 | **0.0%** | 0.0% | 85.0% | 0.0% | 2 | 6.2 s | 11.0 s | -22.4 s | -4.5 s |
| quran-asr-tiny / noisy / muhammad-ayyoub | 10 | 77 | **0.0%** | 0.0% | 95.1% | 0.0% | 2 | 4.1 s | 6.0 s | -13.5 s | -5.9 s |
