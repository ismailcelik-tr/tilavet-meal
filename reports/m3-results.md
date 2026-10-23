# M3 sonuçları (otomatik: scripts/replay_m3.py)

EngineConfig: `EngineConfig(acquire_min_matched=4, acquire_min_score=6, acquire_margin=3, acquire_min_votes=3, acquire_max_candidates=8, diagonal_tolerance=8, common_word_limit=500, track_back=30, track_ahead=50, track_min_score=3, track_tie_slack=0, track_margin=2, confirm_words=2, distinct_window=3, prefix_slack=1, max_skip=2, jump_extra=1, lost_after=4, min_words_for_miss=3)`

Yanlış = son 10 s içinde okunmamış bir ayetin meali (yanıltıcı) / tüm çalınan. Geç = doğru meal, ayet bittikten 2–10 s sonra. Recall = ilk kez okunan meal birimlerinden zamanında çalınanlar. Mükerrer = aynı birimin tekrar çalınması. Gecikmeler: meal başlangıcı − birimin okunmaya başlaması / bitmesi (negatif = okuyucu bitirmeden).

## dev

| Koşu | Akış | Meal | Yanlış | Geç | Recall | Mükerrer | Lost | Başlangıçtan p50 | p90 | Birim sonundan p50 | p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nvidia-fc-rnnt / clean | 10 | 62 | **0.0%** | 0.0% | 98.4% | 0.0% | 2 | 3.8 s | 5.9 s | -11.8 s | -5.5 s |
| quran-asr-tiny / clean | 10 | 62 | **0.0%** | 0.0% | 98.4% | 0.0% | 2 | 4.0 s | 6.3 s | -11.2 s | -5.0 s |
| quran-asr-tiny / noisy | 10 | 62 | **0.0%** | 0.0% | 98.4% | 0.0% | 2 | 4.1 s | 7.0 s | -10.7 s | -4.6 s |

## test

| Koşu | Akış | Meal | Yanlış | Geç | Recall | Mükerrer | Lost | Başlangıçtan p50 | p90 | Birim sonundan p50 | p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nvidia-fc-rnnt / clean | 20 | 159 | **0.0%** | 0.0% | 97.5% | 0.0% | 2 | 3.7 s | 7.5 s | -9.1 s | -2.3 s |
| quran-asr-tiny / clean | 20 | 158 | **0.0%** | 0.0% | 96.3% | 0.0% | 1 | 4.0 s | 6.4 s | -8.7 s | -2.7 s |
| quran-asr-tiny / noisy | 20 | 157 | **0.0%** | 0.6% | 95.7% | 0.0% | 4 | 4.3 s | 6.9 s | -8.5 s | -2.2 s |

## Koşulların ses tanıma hatası (ayet klipleri, tüm akışlar)

| Koşu | CER |
|---|---|
| nvidia-fc-rnnt / clean | 1.13% |
| quran-asr-tiny / clean | 0.35% |
| quran-asr-tiny / noisy | 1.01% |

## Okuyucu bazında (test, varsayılan config)

| Koşu | Akış | Meal | Yanlış | Geç | Recall | Mükerrer | Lost | Başlangıçtan p50 | p90 | Birim sonundan p50 | p90 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nvidia-fc-rnnt / clean / abdulbaset-mujawwad | 5 | 25 | **0.0%** | 0.0% | 86.2% | 0.0% | 1 | 6.6 s | 10.0 s | -13.1 s | -5.2 s |
| nvidia-fc-rnnt / clean / hani-rifai | 5 | 40 | **0.0%** | 0.0% | 100.0% | 0.0% | 1 | 3.5 s | 5.2 s | -8.9 s | -3.2 s |
| nvidia-fc-rnnt / clean / minshawi | 5 | 44 | **0.0%** | 0.0% | 100.0% | 0.0% | 0 | 3.7 s | 5.3 s | -9.9 s | -3.6 s |
| nvidia-fc-rnnt / clean / sudais | 5 | 50 | **0.0%** | 0.0% | 100.0% | 0.0% | 0 | 3.4 s | 6.6 s | -5.4 s | -1.3 s |
| quran-asr-tiny / clean / abdulbaset-mujawwad | 5 | 25 | **0.0%** | 0.0% | 82.8% | 0.0% | 0 | 5.9 s | 10.8 s | -12.6 s | -6.7 s |
| quran-asr-tiny / clean / hani-rifai | 5 | 39 | **0.0%** | 0.0% | 97.5% | 0.0% | 1 | 3.8 s | 6.7 s | -8.2 s | -3.0 s |
| quran-asr-tiny / clean / minshawi | 5 | 44 | **0.0%** | 0.0% | 100.0% | 0.0% | 0 | 4.4 s | 6.0 s | -8.6 s | -3.7 s |
| quran-asr-tiny / clean / sudais | 5 | 50 | **0.0%** | 0.0% | 100.0% | 0.0% | 0 | 3.6 s | 5.3 s | -5.3 s | -0.9 s |
| quran-asr-tiny / noisy / abdulbaset-mujawwad | 5 | 24 | **0.0%** | 0.0% | 79.3% | 0.0% | 2 | 6.7 s | 10.8 s | -14.6 s | -5.6 s |
| quran-asr-tiny / noisy / hani-rifai | 5 | 40 | **0.0%** | 2.5% | 100.0% | 0.0% | 2 | 4.3 s | 6.7 s | -7.8 s | -2.2 s |
| quran-asr-tiny / noisy / minshawi | 5 | 44 | **0.0%** | 0.0% | 100.0% | 0.0% | 0 | 4.4 s | 6.1 s | -9.1 s | -3.7 s |
| quran-asr-tiny / noisy / sudais | 5 | 49 | **0.0%** | 0.0% | 98.0% | 0.0% | 0 | 3.6 s | 5.3 s | -5.1 s | -0.8 s |
