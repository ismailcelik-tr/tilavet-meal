# M6 — iOS Spike Tasarımı

Tarih: 2026-10-24 · Onay: İsmail (GO, iOS + Swift) · Plan: M6 · Önceki: [M5 raporu](../../../reports/m5-feasibility.md)

## Amaç

Mobil fizibiliteyi ölçmek; ürün yazmak değil. Cevaplanacak sorular:

1. tiny + motor iPhone'da gerçek zamanlı ve aynı doğrulukta çalışıyor mu? RTF, RAM, CPU, ısınma, pil.
2. Ekran kilitliyken (arka planda) dinleme ve meal çalma sürüyor mu?
3. Meal sesleri (434 MB) için paket stratejisi ne olmalı?
4. Kod mobile nasıl taşınmalı?

## Cihaz ve kısıtlar

- **Cihaz:** iPhone 17 (İsmail), ücretli Apple Developer hesabı. Telefon kilitlenmeyecek şekilde ayarlı; ölçümler Mac'ten `xcrun devicectl` ile uzaktan başlatılır.
- **Android yok:** Android ölçümü kapsam dışı; raporda yazılır.
- **Genelleme:** iPhone 17 en yeni model; eski cihazlar için sonuç genellenmez.
- **Kulaklık:** CMF Buds 2a.

## Yaklaşım: Swift'te yeniden yazım + golden vector'ler

Python çekirdeği (normalizasyon, `QuranIndex`, hizalama, `PositionEngine` (L + P), `EmissionPolicy`, `MealPlayer`, live session) Swift'e taşınır. Doğruluk, Python'un ürettiği referans girdi-çıktı dosyalarıyla (golden vector) kanıtlanır.

Reddedilenler:

- Python'u cihazda çalıştırmak: ağır; ses katmanı yine Swift.
- Ortak Rust/C++ çekirdek: Android gelince yeniden değerlendirilir.

## Bileşenler

| Bileşen | Görev | Yer |
|---|---|---|
| `TilavetCore` (Swift Package) | Saf mantık: normalize, index, align, engine, policy, player, session. I/O yok, saat dışarıdan. | `ios/TilavetCore` |
| `TilavetCoreTests` | Golden vector testleri; Mac'te `swift test` ile çalışır, cihaz gerekmez | aynı paket |
| `TilavetApp` (SwiftUI) | Ses I/O, sherpa-onnx, meal oynatma, log, ölçüm | `ios/TilavetApp` (XcodeGen `project.yml`) |
| `scripts/export_golden.py` | Golden vector dosyalarını üretir | Python |
| `scripts/device_eval.py` | Cihaz log'u ve kaydını ground truth'a göre puanlar (M4 loopback koduyla) | Python |

**Araçlar:** XcodeGen (Xcode projesini metin dosyasından üretir; brew ile kurulur, yalnız geliştirme aracı). sherpa-onnx'in resmi iOS xcframework'ü, Python'daki sürümle aynı (2.0.0). Bir xcframework, Xcode'a eklenen hazır derlenmiş kütüphanedir.

## Uygulama

- **Ses oturumu:** `AVAudioSession` `.playAndRecord`, `.allowBluetoothA2DP`, giriş iPhone mikrofonuna sabit. Kulaklık A2DP'de kalır; HFP'ye düşmez (M4 dersi).
- **Giriş:** `AVAudioEngine` input tap → 16 kHz mono'ya dönüştürme → live session (12 s pencere, 1 s adım; Python'la aynı).
- **ASR:** sherpa-onnx `OfflineRecognizer` (Zipformer CTC), `model.int8.onnx`, `tokens.txt`, `spelling.json`. İş parçacığı sayısı ölçülerek seçilir (1, 2, 4).
- **Meal:** pakete yalnız ölçüm akışlarının birimleri girer (M4 canlı oturumunun 8 akışı + kendi denemeler için Fatiha). Önceden üretilmiş AAC, `AVAudioPlayer`. Kuyruk kuralları `MealPlayer` ile aynı.
- **Arayüz:** Başlat/Durdur, çalınan mealin metni ve ayet numarası (çok ayetli birimde "birlikte çevrilmiştir" notu), durum (dinliyor / takip kaybedildi).
- **Arka plan:** `UIBackgroundModes: audio`. Oturum ön planda başlar, kilitli ekranda sürer.
- **Ölçüm modu:** Başlatma argümanlarıyla (`--autostart`, `--duration`) Mac'ten başlatılır. Uygulama `Documents/` altına yazar:
  - mikrofon kaydı (wav);
  - olay log'u (jsonl, Python'la aynı şema);
  - kaynak örnekleri: her 5 s'de RAM, CPU, thermal state, pil seviyesi.

  Dosyalar `devicectl` ile Mac'e alınır.

## Doğrulama (Mac, cihazsız)

| Test | Girdi | Beklenen |
|---|---|---|
| Normalizasyon | Kur'an metni + blind2 ASR metinleri | Python `normalize` ile birebir aynı |
| Hizalama | Rastgele 500 (hipotez, bölge) çifti | Aynı `Alignment` (skor, çiftler) |
| Motor + policy | blind2 tiny clean ve hard, 80 akış, kayıtlı pencereler (`t`, metin) | Aynı olay dizisi ve meal'ler, birebir |
| Player + session | M4 testlerindeki senaryolar | Aynı |

Benzerlik ölçüsü (`rapidfuzz` Indel) Swift'te LCS ile yazılır; golden testler bunu da kapsar.

**ASR eşdeğerliği (cihazda):** 50 ayet klibi; Swift sherpa-onnx çıktısı ile Python çıktısı karşılaştırılır. Beklenti: aynı metin. Fark çıkarsa CER farkı raporlanır.

## Cihazda ölçüm

1. **Loopback doğruluk ve gecikme.**
   - M4'teki 8 akış (~33 dk) Mac hoparlöründen çalınır, iPhone dinler.
   - `device_eval.py`: iPhone kaydı ile referans wav arasındaki kaymayı bulur (`estimate_offset`), olayları ground truth'a göre puanlar.
   - Kapı: yanlış 0, recall ≥ %85, meal başlangıcı − birim sonu p50 ≤ 1.5 s, p90 ≤ 3 s (M4 eşikleri).
2. **Kaynak.** Aynı oturumda RTF, RAM, CPU, thermal state.
   - Kapı: RTF ≤ 0.3, RAM ≤ 300 MB, thermal state "serious"a çıkmıyor.
3. **Pil.** 30 dk oturum, telefon şarjdan ve kablodan ayrık (Wi-Fi üzerinden `devicectl`). Saatlik % tahmini raporlanır; eşik yok, bilgi amaçlı.
4. **Arka plan.** Ölçüm modunda ekran programla karartılamaz. Kilit testi için İsmail ekranı bir kez elle kilitler (~10 dk); meal'ler kulaklıktan gelmeye devam etmeli.
5. **Kulaklık gecikmesi.** iPhone'dan tık sinyali CMF Buds'a çalınır, Mac mikrofonu kaydeder. M4'teki `click_test.py` yöntemi.

## Paket boyutu analizi

Karar önerisi için ölçülür, ürüne uygulanmaz:

| Seçenek | Ölçüm |
|---|---|
| HE-AAC düşük bit hızı (ör. 16 ve 24 kbps) | Toplam boyut; 5 örnek birim İsmail'e dinletilir |
| Sure bazında indirme (Background Assets / ilk açılışta) | İlk kurulum boyutu: model + motor + metin |
| Cihaz TTS (`AVSpeechSynthesizer`, Türkçe) | 0 MB; başlatma gecikmesi; seslendirme önceden doğrulanamaz, İsmail örnek dinler |

## Kapsam dışı

- App Store dağıtımı, TestFlight.
- Android.
- Hoparlör modu ve yankı giderme (kulaklık şart, M4).
- Erkek ses (Cem) ve lisans (U7, paralel).

## Çalıştırma sırası

1. `TilavetCore` + golden testler (Mac).
2. Uygulama iskeleti, sherpa-onnx, ASR eşdeğerliği (cihaz).
3. Canlı dinleme ve meal (İsmail kısa deneme: Fatiha).
4. Loopback ölçümü + kaynak (gözetimsiz, ~35 dk).
5. Pil (30 dk, kablosuz) + kilitli ekran (İsmail, ~10 dk) + kulaklık gecikmesi.
6. Paket boyutu analizi (İsmail örnekleri dinler).
7. M6 raporu: taşıma ve paket stratejisi önerisi, "en az hangi cihaz" belirsizliği.
