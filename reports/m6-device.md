# M6 — iPhone Ölçümleri

Tarih: 2026-10-25 · Spec: [m6-ios-spike-design](../docs/superpowers/specs/2026-10-24-m6-ios-spike-design.md) · Cihaz: iPhone 17 ("Fox") · Model: tiny, 2 thread · Motor kuralları: `398b251` · Betik: `scripts/device_loopback.py`

## Loopback: doğruluk, gecikme, kaynak

| Kapı | Eşik | Sonuç |
|---|---|---|
| Yanlış meal | 0 | **0/68** ✅ |
| Recall | ≥ %85 | 67/70 (%95.7) ✅ |
| Meal başlangıcı − birim sonu p50 / p90 | ≤ 1.5 / ≤ 3 s | −12.6 / −4.9 s ✅ (kulaklık dahil ~−12.2 / −4.5 s) |
| RTF (pencere başına ASR süresi / 1 s adım), p90 | ≤ 0.3 | 0.117 ✅ |
| Bellek (`phys_footprint`) en yüksek | ≤ 300 MB | 157 MB ✅ |
| Thermal state | "serious" altında | yalnız "nominal" ✅ |

**Düzen:** M4'ün 8 canlı oturum akışı (10 s baş sessizliği, aralarda 5 s, toplam 32.4 dk) MacBook hoparlöründen %50 sesle çalındı. iPhone 20–30 cm uzakta, ekran açık, kablolu. App Mac'ten `--autostart --mute --threads 2` ile başlatıldı. Meal'ler log'a yazıldı ama çalınmadı (`--mute`), böylece meal sesi mikrofona geri girmedi. Kayıt ile referans arasındaki kayma cross-correlation ile bulundu: 7.68 s.

| Ölçüm | iPhone 17 | M4, Mac (kulaklıksız) |
|---|---|---|
| Meal / yanlış / geç | 68 / 0 / 0 | 68 / 0 / 0 |
| Recall | 67/70 | 67/70 |
| Meal başlangıcı − ayet başı p50 / p90 | 4.8 / 7.7 s | 4.4 / 6.8 s |
| Meal başlangıcı − birim sonu p50 / p90 | −12.6 / −4.9 s | −13.2 / −5.4 s |
| ASR süresi / pencere p50 / p90 | 0.113 / 0.117 s | – |
| Atlanan adım (ASR yetişemedi) | 0 | – |

Bulgular:

- **Doğruluk Mac ile aynı.** Meal sayısı, yanlış ve recall birebir tutuyor. Kaçan 3 meal'in hepsi `abdulbaset-mujawwad-1`'de (37:164 ve 37:175 birimleri); M4'te de kaçanlar bu akıştaydı.
- **iPhone ~0.5 s daha geç.** Gecikme yine eşiğin çok altında: meal, birimin okunuşu bitmeden ~5–13 s önce başlıyor (early politikası). CMF Buds'ın ~0.4 s Bluetooth gecikmesi eklenince de geçiyor. Telefonda kulaklık gecikmesi Görev 9'da ayrıca ölçülecek.
- **Kaynak bol.** ASR saniyenin ~%11'ini kullanıyor; eşik %30. Bellek açılışta 57 MB, oturum boyunca en çok 157 MB (M5'te Mac Python 265 MB). Telefon hiç ısınmadı.
- **Tek motor oturumu.** M4'te her akış ayrı oturumdu; burada 8 akış tek oturumda, arka arkaya çalındı. Akış değişimi okuyucu ve pasaj değişimi gibi davranıyor; motor her geçişte yeniden kilitlendi ve yanlış meal çıkmadı.

Sınırlar:

- **CPU ölçümü güvenilir değil.** `thread_basic_info.cpu_usage` 5 s'de bir alınan anlık bir değer; medyan %4 çıktı. 2 thread ile 0.113 s/s ASR süresi ~%11–23 bir çekirdek yükü demek. Değer ASR anına denk gelmeyen örnekleri ölçüyor; CPU için ASR süresi esas alınmalı.
- **Pil ölçülmedi.** Bu koşuda telefon kabloda şarj oldu (%70 → %80). Ayrı pil koşusu İsmail'in kararıyla atlandı; iOS pil seviyesini app'e %5 adımla veriyor, 30 dk'lık koşu zaten kaba bir tahmin verirdi.
- **Loopback oda koşulunu ölçmüyor.** Hoparlör ile telefon yakın ve aynı masada (M4 sınırı).
- **Tek cihaz.** iPhone 17 en yeni model; eski cihazlara genellenemez.

Ham veri: `data/derived/m6/loopback/` (`summary.json`, `live.jsonl`, `metrics.jsonl`, `mic.f32`).

## Kilitli ekran

**Düzen:** Telefon kablosuz (`devicectl` Wi-Fi üzerinden; başlatma ve dosya çekme sorunsuz), CMF Buds bağlı ve İsmail'in kulağında. App Mac'ten `--autostart --threads 2` ile sesli başlatıldı. İsmail ekranı ~3. saniyede kilitledi. 20 s sonra MacBook hoparlöründen 3 akış çalındı (`abdulbaset-mujawwad-4`, `hani-rifai-3`, `sudais-0`; 12 dk). Oturum 13 dk.

| Ölçüm | Sonuç |
|---|---|
| Meal (çalınan / beklenen birim) | 25 / 25, sıra birebir, yanlış 0 |
| Pencere | 779; en büyük aralık 1.0 s; atlanan adım 0 |
| `Playback` (`AVAudioPlayer` başladı) | 25; meal kararından ~0.7 s sonra |
| ASR süresi / pencere p50 / en çok | 0.115 / 0.136 s |
| Bellek en çok / thermal | 157 MB / nominal |
| Kulaklık (İsmail) | Bütün meal'ler duyuldu; kesilme, atlama, bozulma yok |

**Sonuç:** Kilitli ekranda dinleme ve kulaklıktan meal çalma kesintisiz sürüyor; kaynak kullanımı kilit açık koşuyla aynı. App kilit durumunu log'a yazmıyor; kilit İsmail'in gözlemine dayanıyor.

Ham veri: `data/derived/m6/lock/` (`live.jsonl`, `metrics.jsonl`).

## Kulaklık gecikmesi

Telefonda ölçülmedi; İsmail'in kararıyla atlandı (birkaç yüz ms gecikme kullanımda sorun değil). Mac'teki ölçüm (M4): CMF Buds 2a ek gecikmesi ~314 ms. Loopback gecikmesi buna ~0.4 s eklense de kapıların çok altında.

## Meal paketi seçenekleri

`scripts/package_options.py` (boyutlar bütün setin dönüştürülmesiyle) ve app'in `--tts-sample` modu (cihaz TTS). Örnekler: `data/derived/m6/package/samples/` (1:2, 112:1, 12:11–12, 2:255, 2:282).

| Seçenek | 5.393 birim | Not |
|---|---|---|
| Şu anki set (`say`, AAC-LC ~32 kbps) | 398 MB | `say` her dosyanın başına 32 KB dolgu koyuyor |
| AAC-LC 32 kbps (`afconvert`) | 287 MB | Aynı kodek ve bit hızı, dolgu 4 KB |
| HE-AAC 24 kbps | 195 MB | |
| HE-AAC 16 kbps | 142 MB | |
| Cihaz TTS (`AVSpeechSynthesizer`) | 0 MB | Ses önceden doğrulanamaz |

Diğer kurulum içeriği: model 18 MB, Kur'an ve meal metni ~2 MB, sherpa-onnx framework. Bugünkü app 487 MB; bunun 50 MB'ı yalnız test için olan parity klipleri.

**Cihaz TTS:**

- Telefondaki tek Türkçe ses `com.apple.voice.super-compact.tr-TR.Yelda` (kalite 1, varsayılan). Daha yüksek kaliteli Yelda indirilmemiş.
- Beş birimin ses süresi Mac'te `say` ile üretilenlerle birebir aynı (ör. 2:282 77.68 s). Aynı ses ve motor.
- İlk sese kadar süre: ilk birimde 0.66 s (synthesizer açılışı), sonrakilerde 8–18 ms. 77.7 s'lik 2:282'nin tamamı 0.72 s'de üretildi.
- Synthesizer uzun metinde cümle aralarında boş buffer gönderiyor (2:282'de 5). İlk denemede boş buffer bitiş sayıldı ve uzun birimler kesildi; bitiş `didFinish` delegate'ine bağlanınca düzeldi.
- Risk: iOS güncellemesi sesi ya da okunuşu değiştirebilir; çalınacak ses önceden dinlenip doğrulanamaz.

**Dinleme (İsmail):** HE-AAC 16 kbps ile şu anki set arasında duyulur fark yok. Cihaz TTS sesi kabul edilebilir. Öneri [M6 raporunda](m6-feasibility.md#meal-paketi).
