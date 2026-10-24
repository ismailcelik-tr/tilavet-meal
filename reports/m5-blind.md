# Kör set sonuçları: blind2 (otomatik: scripts/replay_m3.py --set blind2)

EngineConfig: `EngineConfig(acquire_min_matched=4, acquire_min_score=6, acquire_margin=3, acquire_min_votes=3, acquire_max_candidates=8, acquire_rival_votes=2, diagonal_tolerance=8, common_word_limit=500, track_back=30, track_ahead=50, track_min_score=3, track_tie_slack=0, track_margin=2, past_margin=3, confirm_words=2, distinct_window=3, prefix_slack=1, max_skip=2, jump_extra=1, lost_after=4, min_words_for_miss=3)`

Tanımlar `m3-results.md` ile aynı. Üst sınır: yanlış 0 ise üçler kuralı (%95, 3/meal), değilse yok.

| Koşu | Yanlış üst sınır | Akış | Meal | Yanlış | Geç | Recall | Mükerrer | Lost | Başlangıçtan p50 | p90 | Birim sonundan p50 | p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| quran-asr-tiny / clean | ≤1.1% | 40 | 280 | **0.0%** | 1.1% | 96.2% | 0.0% | 3 | 4.3 s | 8.4 s | -12.8 s | -3.3 s |
| quran-asr-tiny / hard | ≤1.1% | 40 | 278 | **0.0%** | 0.7% | 95.5% | 0.0% | 15 | 4.4 s | 10.0 s | -12.8 s | -2.9 s |
| quran-asr-tiny / noisy | ≤1.1% | 40 | 279 | **0.0%** | 1.1% | 95.8% | 0.0% | 9 | 4.4 s | 8.6 s | -12.7 s | -3.3 s |

## Ses tanıma hatası (ayet klipleri)

| Koşu | CER |
|---|---|
| quran-asr-tiny / clean | 0.18% |
| quran-asr-tiny / hard | 3.82% |
| quran-asr-tiny / noisy | 0.66% |

## 30 s duraklama ve ASR süresi

| Koşu | Duraklamada meal (10 s sonra) | ASR süresi p50 / p90 (adım 1 s) |
|---|---|---|
| quran-asr-tiny / clean | 0 | 0.037 / 0.043 s |
| quran-asr-tiny / hard | 0 | 0.034 / 0.037 s |
| quran-asr-tiny / noisy | 0 | 0.036 / 0.042 s |

## Okuyucu bazında

| Koşu | Akış | Meal | Yanlış | Geç | Recall | Mükerrer | Lost | Başlangıçtan p50 | p90 | Birim sonundan p50 | p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| quran-asr-tiny / clean / ghamdi | 10 | 74 | **0.0%** | 0.0% | 96.1% | 0.0% | 0 | 4.0 s | 7.0 s | -11.8 s | -2.6 s |
| quran-asr-tiny / clean / hudhaify | 10 | 78 | **0.0%** | 2.6% | 98.7% | 0.0% | 1 | 3.8 s | 6.7 s | -9.4 s | -2.3 s |
| quran-asr-tiny / clean / husary-mujawwad | 10 | 55 | **0.0%** | 1.8% | 93.1% | 0.0% | 0 | 8.0 s | 14.0 s | -22.1 s | -4.9 s |
| quran-asr-tiny / clean / tablawi | 10 | 73 | **0.0%** | 0.0% | 96.0% | 0.0% | 2 | 3.8 s | 6.0 s | -12.1 s | -3.9 s |
| quran-asr-tiny / hard / ghamdi | 10 | 73 | **0.0%** | 0.0% | 94.8% | 0.0% | 2 | 3.9 s | 6.2 s | -12.1 s | -2.0 s |
| quran-asr-tiny / hard / hudhaify | 10 | 78 | **0.0%** | 2.6% | 98.7% | 0.0% | 2 | 3.7 s | 6.0 s | -9.6 s | -1.8 s |
| quran-asr-tiny / hard / husary-mujawwad | 10 | 54 | **0.0%** | 0.0% | 91.4% | 0.0% | 5 | 9.2 s | 16.0 s | -22.1 s | -3.9 s |
| quran-asr-tiny / hard / tablawi | 10 | 73 | **0.0%** | 0.0% | 96.0% | 0.0% | 6 | 4.1 s | 6.8 s | -12.0 s | -2.9 s |
| quran-asr-tiny / noisy / ghamdi | 10 | 74 | **0.0%** | 0.0% | 96.1% | 0.0% | 2 | 4.0 s | 7.0 s | -11.7 s | -2.7 s |
| quran-asr-tiny / noisy / hudhaify | 10 | 78 | **0.0%** | 2.6% | 98.7% | 0.0% | 2 | 3.7 s | 6.2 s | -10.0 s | -2.7 s |
| quran-asr-tiny / noisy / husary-mujawwad | 10 | 55 | **0.0%** | 1.8% | 93.1% | 0.0% | 2 | 8.2 s | 15.0 s | -22.1 s | -4.7 s |
| quran-asr-tiny / noisy / tablawi | 10 | 72 | **0.0%** | 0.0% | 94.7% | 0.0% | 3 | 4.0 s | 6.1 s | -12.1 s | -4.1 s |
