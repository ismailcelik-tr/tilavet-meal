# M2 sonuçları — set: `qlab` (otomatik: scripts/report_m2.py)

599 klip, kaynaklar: everyayah_heldout, qul_alnufais, tlog_holdout. Metrikler normalize metin üzerinde, korpus düzeyinde.
CER-a = elif'siz CER (Uthmani/standart imla farkını nötrler). İlk-3 = ilk 3 kelimenin birebir doğru tanındığı klip oranı.

| Model | Lisans | Kaynak | CER | CER-a | WER | İlk-3 |
|---|---|---|---|---|---|---|
| quran-asr-tiny | MIT | everyayah_heldout | 0.47% | 0.33% | 1.83% | 94.00% |
| quran-asr-tiny | MIT | qul_alnufais | 3.41% | 3.41% | 5.35% | 93.00% |
| quran-asr-tiny | MIT | tlog_holdout | 5.35% | 4.28% | 18.52% | 59.30% |
| quran-asr-tiny | MIT | **all** | 2.71% | 2.42% | 7.10% | 82.14% |
| nvidia-fc-ctc | CC-BY-4.0 | everyayah_heldout | 0.46% | 0.43% | 1.50% | 97.50% |
| nvidia-fc-ctc | CC-BY-4.0 | qul_alnufais | 4.07% | 4.10% | 7.57% | 90.00% |
| nvidia-fc-ctc | CC-BY-4.0 | tlog_holdout | 5.02% | 3.86% | 16.80% | 66.33% |
| nvidia-fc-ctc | CC-BY-4.0 | **all** | 2.88% | 2.62% | 7.42% | 84.64% |
| nvidia-fc-rnnt | CC-BY-4.0 | everyayah_heldout | 0.44% | 0.43% | 1.38% | 98.00% |
| nvidia-fc-rnnt | CC-BY-4.0 | qul_alnufais | 3.56% | 3.67% | 4.65% | 97.00% |
| nvidia-fc-rnnt | CC-BY-4.0 | tlog_holdout | 3.41% | 2.33% | 10.91% | 75.88% |
| nvidia-fc-rnnt | CC-BY-4.0 | **all** | 2.31% | 2.10% | 4.87% | 90.32% |
| tarteel-whisper-base | Apache-2.0 | everyayah_heldout | 0.62% | 0.59% | 2.36% | 96.50% |
| tarteel-whisper-base | Apache-2.0 | qul_alnufais | 3.48% | 3.54% | 4.03% | 98.00% |
| tarteel-whisper-base | Apache-2.0 | tlog_holdout | 7.87% | 6.59% | 23.41% | 53.27% |
| tarteel-whisper-base | Apache-2.0 | **all** | 3.37% | 3.11% | 7.96% | 82.64% |
| whisper-large-v3-turbo | MIT | everyayah_heldout | 1.76% | 1.84% | 5.61% | 82.50% |
| whisper-large-v3-turbo | MIT | qul_alnufais | 2.26% | 2.37% | 4.69% | 93.50% |
| whisper-large-v3-turbo | MIT | tlog_holdout | 7.76% | 6.35% | 22.95% | 55.28% |
| whisper-large-v3-turbo | MIT | **all** | 3.33% | 3.10% | 9.35% | 77.13% |

## Hız ve bellek (M5 MacBook Pro, 16 GB)

| Model | Yükleme | Ses | İşlem | RTF | Peak RSS |
|---|---|---|---|---|---|
| quran-asr-tiny | 1.11 s | 7701.4 s | 23.9 s | 0.0031 | 1188 MB |
| nvidia-fc-ctc | 5.83 s | 7701.4 s | 112.1 s | 0.0146 | 2790 MB |
| nvidia-fc-rnnt | 4.93 s | 7701.4 s | 122.5 s | 0.0159 | 3260 MB |
| tarteel-whisper-base | 4.33 s | 7701.4 s | 1918.5 s | 0.2491 | 1374 MB |
| whisper-large-v3-turbo | 0.67 s | 7701.4 s | 259.6 s | 0.0337 | 2343 MB |

Yükleme süresi ilk çalıştırmada model indirmeyi içerebilir. RTF = işlem ÷ ses süresi. Peak RSS GPU (MLX/MPS) belleğini içermez.
