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
- **Pil bu koşuda ölçülmedi.** Telefon kabloda şarj oldu (%70 → %80). Pil ölçümü Görev 9'da, kablosuz.
- **Loopback oda koşulunu ölçmüyor.** Hoparlör ile telefon yakın ve aynı masada (M4 sınırı).
- **Tek cihaz.** iPhone 17 en yeni model; eski cihazlara genellenemez.

Ham veri: `data/derived/m6/loopback/` (`summary.json`, `live.jsonl`, `metrics.jsonl`, `mic.f32`).
