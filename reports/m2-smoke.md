# M2 sonuçları — set: `smoke` (otomatik: scripts/report_m2.py)

200 klip, kaynaklar: hani-rifai, minshawi-murattal. Metrikler normalize metin üzerinde, korpus düzeyinde.
CER-a = elif'siz CER (Uthmani/standart imla farkını nötrler). İlk-3 = ilk 3 kelimenin birebir doğru tanındığı klip oranı.

| Model | Lisans | Kaynak | CER | CER-a | WER | İlk-3 |
|---|---|---|---|---|---|---|
| quran-asr-tiny | MIT | hani-rifai | 0.67% | 0.49% | 3.35% | 92.00% |
| quran-asr-tiny | MIT | minshawi-murattal | 0.26% | 0.13% | 1.30% | 97.00% |
| quran-asr-tiny | MIT | **all** | 0.47% | 0.31% | 2.32% | 94.50% |
| nvidia-fc-ctc | CC-BY-4.0 | hani-rifai | 0.26% | 0.22% | 0.74% | 98.00% |
| nvidia-fc-ctc | CC-BY-4.0 | minshawi-murattal | 0.22% | 0.22% | 0.74% | 98.00% |
| nvidia-fc-ctc | CC-BY-4.0 | **all** | 0.24% | 0.22% | 0.74% | 98.00% |
| nvidia-fc-rnnt | CC-BY-4.0 | hani-rifai | 0.00% | 0.00% | 0.00% | 100.00% |
| nvidia-fc-rnnt | CC-BY-4.0 | minshawi-murattal | 0.07% | 0.09% | 0.37% | 99.00% |
| nvidia-fc-rnnt | CC-BY-4.0 | **all** | 0.04% | 0.04% | 0.19% | 99.50% |
| tarteel-whisper-base | Apache-2.0 | hani-rifai | 0.04% | 0.04% | 0.19% | 100.00% |
| tarteel-whisper-base | Apache-2.0 | minshawi-murattal | 0.00% | 0.00% | 0.00% | 100.00% |
| tarteel-whisper-base | Apache-2.0 | **all** | 0.02% | 0.02% | 0.09% | 100.00% |
| whisper-large-v3-turbo | MIT | hani-rifai | 3.09% | 2.92% | 11.15% | 70.00% |
| whisper-large-v3-turbo | MIT | minshawi-murattal | 1.23% | 1.15% | 4.65% | 87.00% |
| whisper-large-v3-turbo | MIT | **all** | 2.16% | 2.03% | 7.90% | 78.50% |

## Hız ve bellek (M5 MacBook Pro, 16 GB)

| Model | Yükleme | Ses | İşlem | RTF | Peak RSS |
|---|---|---|---|---|---|
| quran-asr-tiny | 0.77 s | 1413.3 s | 4.5 s | 0.0032 | 458 MB |
| nvidia-fc-ctc | 11.44 s | 1413.3 s | 31.8 s | 0.0225 | 2075 MB |
| nvidia-fc-rnnt | 4.12 s | 1413.3 s | 33.1 s | 0.0234 | 1895 MB |
| tarteel-whisper-base | 4.22 s | 1413.3 s | 332.3 s | 0.2351 | 1077 MB |
| whisper-large-v3-turbo | 0.78 s | 1413.3 s | 72.8 s | 0.0515 | 1743 MB |

Yükleme süresi ilk çalıştırmada model indirmeyi içerebilir. RTF = işlem ÷ ses süresi. Peak RSS GPU (MLX/MPS) belleğini içermez.
