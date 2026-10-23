# M2 — Akustik Model Karşılaştırması

Tarih: 2026-10-23 · Ham sayılar: [m2-qlab.md](m2-qlab.md) (karar seti), [m2-smoke.md](m2-smoke.md) (pipeline doğrulama)

## Karar özeti

| Kapı (plan) | Sonuç |
|---|---|
| Telefon/amatör kayıtlarda CER ≤ %8 ve RTF ≤ 0.2 olan ≥ 1 permissive-lisanslı model | **Geçti.** NVIDIA FastConformer (CC-BY-4.0): telefon CER %3.41, RTF 0.016 |

**Öneri:** Birincil ön uç **NVIDIA `stt_ar_fastconformer_hybrid_large_pcd_v1.0`**. Tek modelde iki çıkış var:
- **RNN-T:** metin için. Telefon kayıtlarında en iyi sonuç.
- **CTC:** M3'te aday ayetleri puanlamak için.

Mobil için hafif yedek: **quran-asr-tiny** (MIT, 19 MB, sherpa-onnx ile iOS/Android'e hazır).

## Değerlendirme verisi

- **Quran-Lab held-out benchmark** (revizyon `d9fc635`, 600 klip, 2.1 saat; gated, sadece ASR araştırması, ses yeniden dağıtılmaz).
  - `everyayah_heldout`: stüdyo, 3 okuyucu
  - `qul_alnufais`: stüdyo, hiçbir açık setin eğitiminde olmayan okuyucu
  - `tlog_holdout`: sıradan insanların telefon kayıtları
- **Leakage notu:** `everyayah_heldout` benchmark yazarlarının eğitiminden ayrılmış, ama her modelden değil. quran-asr-tiny bu 3 okuyucudan 2'sini görmüş (model kartı). NVIDIA ve tarteel modelleri EveryAyah ile eğitildi. **Adil karşılaştırma `qul_alnufais` ve `tlog_holdout`.**
- Benchmark'ta bir tlog klibi iki kez listelenmiş. Resmi skor 600, bizim rapor 599 benzersiz klip sayar; etki ihmal edilebilir.

## Ölçüm düzeneğinin doğrulanması

Resmi `score.py` ile bizim ölçümümüz, leaderboard'daki bağımsız ölçümlerle örtüşüyor:

| Model | Leaderboard WER / CER | Bizim (resmi scorer) |
|---|---|---|
| quran-asr-tiny (int8) | 7.08 / 2.86 | 7.09 / 2.84 |
| NVIDIA FastConformer (CTC) | 7.44 / 3.08 | 7.44 / 3.08 |

## Sonuçlar (resmi scorer, WER %)

| Model | Lisans | Boyut | Genel | QUL | **Telefon** | Telefon CER* | İlk-3 telefon* | RTF |
|---|---|---|---|---|---|---|---|---|
| **NVIDIA FC — RNN-T** | CC-BY-4.0 | 115M | **4.91** | 4.69 | **10.98** | **3.41** | **75.9%** | 0.016 |
| NVIDIA FC — CTC | CC-BY-4.0 | 115M | 7.44 | 7.61 | 16.77 | 5.02 | 66.3% | 0.015 |
| quran-asr-tiny | MIT | 16M | 7.09 | 5.35 | 18.41 | 5.35 | 59.3% | **0.003** |
| tarteel-whisper-base | Apache-2.0 | 74M | 7.95 | 4.03 | 23.27 | 7.87 | 53.3% | 0.249 |
| Whisper large-v3-turbo | MIT | 809M | 9.45 | 4.73 | 22.88 | 7.76 | 55.3% | 0.034 |

\* Bizim metrikler (normalize, boşluk dahil CER). İlk-3 = ilk 3 kelime birebir doğru. RTF: M5 CPU (Whisper turbo: MLX GPU, tarteel: MPS).

## Bulgular

1. **Aynı NVIDIA modelinin RNN-T çıkışı, CTC çıkışından belirgin daha iyi.** Telefonda WER 16.8 → 11.0, ilk-3 %66 → %76. Leaderboard yalnızca CTC çıkışını listeliyor; bu fark orada görünmüyor.
2. **Stüdyo ile telefon arasındaki fark büyük.** Her modelde telefon WER'i stüdyonun 2–10 katı. Ürünün gerçek ortamı (hoparlörden okuyucu, oda yankısı) stüdyodan çok telefona yakın. M5'in gürültü/yankı testleri bu yüzden kritik.
3. **İlk-3 metriği Track için yeterli değil.** Telefon kayıtlarında en iyi model bile kliplerin %24'ünde ilk 3 kelimeyi birebir tutturamıyor. Position Engine birebir kelime eşleşmesine değil, bulanık eşleme ve CTC puanlamasına dayanmalı. M1'deki "1 kelime yeter" yalnızca bilgi-kuramsal alt sınırdı.
4. **Genel amaçlı Whisper elendi.** Hem daha kötü hem CTC çıktısı yok. tarteel-whisper-base de telefonda zayıf ve 16 kat yavaş.
5. **quran.com zaman damgaları bazı okuyucularda kaymış.** Hani ar-Rifai'de yaklaşık bir kelime. M3'te gecikme ölçümünün ground truth'u bu yüzden ya EveryAyah ayet dosyaları ya da `Quran-Lab/mfa-quran-hafs` forced aligner (Apache-2.0) olmalı.

## Sınırlamalar

- **Klip bazlı, offline transkripsiyon.** NVIDIA modeli streaming değil. Canlı akışta parça parça (chunked) çalıştırıldığında doğruluk düşer; M3'te ölçülecek.
- **Peak RSS** önceden yüklenen ~0.5 GB sesi içeriyor, GPU belleğini içermiyor. Model belleği tablodakinden düşük.
- **Mobil:** NVIDIA modeli için ONNX export (sherpa-onnx destekliyor) ve int8 boyut/hız M6'da doğrulanacak. Risk düşükse M3'te erken bir export denemesi yapılabilir.

## M3 önerisi (onay bekliyor)

**Position Engine, offline gerçek zamanlı simülasyon:**
- NVIDIA hibrit modeli chunked çalıştırılır.
- RNN-T metniyle Acquire (bulanık top-K).
- CTC ile aday doğrulama ve Track.
- Test: EveryAyah ayet dosyalarından birleştirilmiş akışlar; pause/tekrar/atlama enjekte edilir, ground truth otomatik. Ayrıca tam sure kayıtları (mfa-quran-hafs ile hizalanmış).
- Ölçüt: yanlış-ayet oranı, recall, commit gecikmesi (plan Bölüm 6).
