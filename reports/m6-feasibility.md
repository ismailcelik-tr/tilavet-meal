# M6 — iOS Spike Raporu

Tarih: 2026-10-25 · Spec: [m6-ios-spike-design](../docs/superpowers/specs/2026-10-24-m6-ios-spike-design.md) · Cihaz ölçümleri: [m6-device.md](m6-device.md) · Cihaz: iPhone 17 · Model: tiny · Motor kuralları: `398b251`

## Karar özeti

| Soru | Kapı | Sonuç |
|---|---|---|
| Swift çekirdeği Python'la aynı mı | birebir | Normalizasyon 11.236/11.236, hizalama 500/500, motor + policy 80/80 akış birebir ✅ |
| Cihazda ASR Python'la aynı mı | aynı metin | 49/50 klip birebir; CER farkı %0.04 ✅ |
| Loopback: yanlış / recall | 0 / ≥ %85 | **0/68** / %95.7 ✅ (Mac M4 ile aynı) |
| Meal başlangıcı − birim sonu p50 / p90 | ≤ 1.5 / ≤ 3 s | −12.6 / −4.9 s ✅ |
| RTF p90 / bellek / thermal | ≤ 0.3 / ≤ 300 MB / < serious | 0.117 / 157 MB / nominal ✅ |
| Kilitli ekran | dinleme ve meal sürüyor | 13 dk, 25/25 meal, kesinti yok; İsmail kulaklıktan duydu ✅ |
| Pil | bilgi | Ölçülmedi (İsmail kararı) |
| Kulaklık gecikmesi | bilgi | Telefonda ölçülmedi (İsmail kararı); Mac'te ~314 ms |
| Meal paketi ve ses | karar | HE-AAC 16 kbps; ses Yelda yerine Piper Eren (erkek): 398 MB → 122 MB |

**Sonuç:** tiny + motor iPhone 17'de gerçek zamanlı ve Mac'le aynı doğrulukta çalışıyor; kilitli ekranda sürüyor. Mobil fizibilite iPhone 17 için kanıtlandı. Eski cihazlar ve Android ölçülmedi.

## Swift taşıması

Python çekirdeği (normalize, Tanzil, `QuranIndex`, hizalama, `PositionEngine` L + P, `EmissionPolicy`, `MealPlayer`, live session) `ios/TilavetCore`'a satır satır taşındı: 769 satır Swift. App katmanı (ses, sherpa-onnx, log, ölçüm, arayüz) 717 satır.

Doğruluk golden vector'lerle kanıtlandı: Python'un ürettiği girdi-çıktı dosyaları (`scripts/export_golden.py`) Mac'te `swift test` ile karşılaştırılıyor. Tolerans yok; her fark hata sayıldı.

| Test | Girdi | Sonuç |
|---|---|---|
| Normalizasyon | Kur'an + blind2 ASR metinleri, 11.236 | birebir |
| Hizalama | 500 (hipotez, bölge) çifti | birebir |
| Motor + policy | blind2 tiny clean + hard, 80 akış | olaylar ve meal'ler birebir; release'te ~0.4 ms/pencere |
| Player + session | Python testlerinin Swift karşılıkları | geçiyor |

**ASR eşdeğerliği (cihaz):** 50 klipten 49'u Python'la aynı metin. Fark `21.wav`'da tek kelime (ومهدت → ومدت); CER farkı %0.04. Pencere başına RTF 1 / 2 / 4 thread: 0.013 / 0.009 / 0.006 (Mac Python 4 thread: 0.0037). Canlı oturumda 2 thread seçildi.

Dikkat isteyen Python–Swift farkları: Python `max` ilk en büyüğü döndürür, Swift'in `max(by:)` sonuncuyu (elle döngü yazıldı); Swift `"\r\n"`'yi tek `Character` sayar (CRLF'li süre CSV'si app'te çöktü, `isNewline` ile düzeldi).

## Cihaz ölçümleri

Ayrıntı ve ham sayılar [m6-device.md](m6-device.md)'de.

- **Loopback (32.4 dk, M4'ün 8 akışı, tek motor oturumu):** 68 meal, 0 yanlış, recall 67/70. Sayılar Mac ile birebir; kaçan 3 meal M4'te de kaçan akışta (`abdulbaset-mujawwad-1`). iPhone ~0.5 s daha geç, eşiğin çok altında.
- **Kaynak:** ASR pencere başına 0.113 s (p50); hiç adım atlanmadı. Bellek en çok 157 MB (Mac Python 265 MB). Thermal hep nominal. CPU örneklemesi güvenilir çıkmadı; yükü ASR süresi gösteriyor (bir çekirdeğin ~%11–23'ü).
- **Kilitli ekran (13 dk, Wi-Fi, CMF Buds):** 25/25 meal doğru sırada; pencereler kesintisiz; bütün meal'ler kulaklıktan duyuldu.
- **Ses oturumu:** `.playAndRecord` + `.allowBluetoothA2DP`, giriş iPhone mikrofonu. Kulaklık A2DP'de kaldı, ses kalitesi düşmedi (HFP'ye inmedi).

## Meal paketi

| Seçenek | Meal | Toplam kurulum (tahmin) | Dinleme (İsmail) |
|---|---|---|---|
| Şu anki set (`say` AAC-LC) | 398 MB | ~445 MB | referans |
| HE-AAC 24 kbps | 195 MB | ~240 MB | – |
| **HE-AAC 16 kbps** | **142 MB** | **~190 MB** | fark yok |
| Cihaz TTS | 0 MB | ~45 MB | kabul edilebilir |

Toplam = meal + model 18 MB + framework 25 MB + metin ~2 MB; test için olan parity klipleri (50 MB) hariç.

**Öneri: HE-AAC 16 kbps, önceden üretilmiş, app'in içinde.** Karar İsmail'in.

- Çalınacak her ses önceden dinlenip doğrulanabiliyor. Projenin ilkesi doğrulanmış meal; bu ilke sesi de kapsıyor.
- Her cihazda ve iOS sürümünde aynı ses. Cihaz TTS'te ses cihazın yüklü Yelda sürümüne bağlı (iPhone'da super-compact; kullanıcı daha iyisini indirmişse o) ve iOS güncellemesiyle değişebilir.
- ~190 MB ile sure bazında indirmeye gerek yok; ilk dinlemede internet istemez.
- Cihaz TTS yedek olarak kalır: U7'de Yelda kayıtlarının app içinde dağıtılmasına lisans çıkmazsa ya da boyut kritik olursa. Gecikmesi sorun değil (ilk birim 0.66 s, sonra < 20 ms).

### Ses seçimi (İsmail)

İsmail erkek ses istedi. Aynı 5 birim dört sesle dinlendi:

| Ses | Kaynak | Perde | Lisans |
|---|---|---|---|
| Yelda | Apple, kadın (şu anki) | ~210 Hz | Apple sesiyle üretilen kaydın dağıtımı belirsiz |
| Cem (Geliştirilmiş) | Apple, erkek; iPhone'da üretildi (`--tts-sample --voice Cem`) | – | Yelda ile aynı soru |
| Piper dfki | Piper'ın resmî Türkçe sesi, erkek | ~105 Hz | CC BY-NC-SA 4.0 (ticari değil) |
| **Piper Eren** | Topluluk modeli `99eren99/piper-turkish-tts`, erkek | ~93 Hz | **Belirtilmemiş** |

**Karar (İsmail): Piper Eren.** Bütün set `scripts/render_meals_piper.py` ile Mac'te üretildi (20 dk, 8 çekirdek): 5.393 birim, 11.9 saat, HE-AAC 16 kbps 122 MB. Eren Yelda'dan ~%16 hızlı (2:282: 62.9 s / 77.7 s). App paketi 487 MB → 224 MB (parity klipleri dahil). İsmail telefonda kulaklıkla denedi: "gayet başarılı".

- **Lisans riski:** Modelin lisansı yok; ürüne geçmeden model sahibinden yazılı izin gerekir (U7). İzin çıkmazsa yedekler: Apple Cem, bulut neural ses, kendi eğitilecek ses.
- `piper-tts` 1.8.0'ın macOS paketi espeak verisini eksik getiriyor; 1.3.0'a sabitlendi. espeak-ng uzun veri yollarını (~160 karakter üstü) reddedip derleme yoluna düşüyor; proje `.venv`'inde yol kısa, sorun yok.

Not: Yelda setinin 398 MB'ının büyük kısmı ses değil; `say` her dosyanın başına 32 KB dolgu koyuyor. Aynı kodek `afconvert` ile 287 MB.

## Sonradan: motor kuralı değişti (25 Eki, saha denemesi)

Bu rapordaki cihaz ölçümleri (loopback, kilitli ekran) eski kuralla yapıldı.

**Sorun (İsmail, saha):** Asr Sûresi'nin 1. âyetinin meali gelmiyordu. Acquire yalnız eşleşmenin bittiği âyeti onaylıyordu. 103:1 tek kelime ("والعصر"); pasaj ancak 103:3 başlarken bulunuyor ve 103:1-2'nin meali hiç çalmıyordu. Kısa âyetle başlayan her pasaj aynı kaybı yaşıyordu.

**Kural (`75a100e`, Swift `3bd0260`):** Acquire, eşleşmedeki en çok 2 önceki âyeti de onaylar; koşul: âyetin en az bir kelimesi eşleşmede olmalı ve âyet tahminen ≤ 7 s önce bitmiş olmalı (yaş: âyetin son eşleşen kelimesinden sonraki kelime sayısı × 12 s / penceredeki kelime sayısı). Meal'ler kuyrukta sırayla çalar (İsmail onayı).

| Set (tiny) | Yanlış eski / yeni | Recall eski / yeni |
|---|---|---|
| M3 test clean / noisy / hard | 0 / 0 | 96.3 / 95.7 / 94.5 → 96.3 / 95.7 / 95.1 |
| M4 kör clean / noisy / hard | 0 / 0 | 95.1 / 95.1 / 93.1 → 95.4 / 95.8 / 94.1 |
| M5 kör (blind2) clean / noisy / hard | 0 / 0 | 96.2 / 95.8 / 95.5 → 97.6 / 97.6 / 96.5 |

Birim sonundan gecikme p90 değişmedi ya da iyileşti (ör. blind2 clean −3.3 → −2.8 s).

- Koşulsuz ilk sürüm kör setlerde 2 yanlış meal üretti: atlanan bir âyeti (74:5) ve 10 s'den eski bir âyeti (79:33) onayladı. İki koşul bunları kapattı; ikisi de test olarak duruyor.
- **Kör setler artık açık:** kural onlara bakılarak daraltıldı. Tarafsız doğrulama İsmail'in saha denemesi (Kevser, Asr, Nasr, İhlâs: sorun yok).

**Hurûf-ı mukattaa (harfle başlayan sureler):** 31 sure × 5 okuyucu (Husary, Alafasy, Sudeys, Minşavi murattal, Rifai), besmele + 1-4. âyetler, canlı pencerelerle tiny. İlk âyetin meali eski kuralla 45/155, yeni kuralla 58/155; yanlış 0; 1-4. âyet recall 363 → 396/510. Tanıma sorun değil ("الم", "طه", "طسم" doğru yazılıyor). Kaçanlar neredeyse hep yalnız harflerden oluşan âyetler: meali de harf adları ("Elif, Lam, Mim."). "الم" altı surenin açılışı ve "ألم" ile aynı; sure ancak sonraki âyetlerle belli oluyor, o an harfler > 7 s geride. Ayrı kural önerilmez: kazanç harf adları, bedeli yanlış meal riski. Anlamlı devamı olan açılışlar (50:1, 68:1) bulunuyor; 12:1 beşin ikisinde kaçtı.

## Taşıma stratejisi

**Öneri: Platform başına yerel yeniden yazım + golden vector'ler; paylaşılan çekirdek yok.**

- Çekirdek küçük (Swift'te 769 satır) ve saf mantık; I/O yok. Swift taşıması golden testlerle birebir eşitlendi.
- Android gelince Kotlin'e aynı yöntemle taşınır: aynı golden dosyalar, aynı testler. sherpa-onnx'in resmi Kotlin API'si ve Android paketi var.
- Paylaşılan Rust/C++ çekirdek tek kaynak sağlar ama iki platformda derleme, FFI ve hata ayıklama yükü getirir. Bu boyutta bir çekirdek için bedeli kazancından büyük.
- Bedeli: motor kuralı değiştiğinde Python, Swift ve Kotlin ayrı ayrı güncellenmeli. Python referans kalır; golden vector'ler yeniden üretilir ve her platform onlarla karşılaştırılır. Fark sessizce kaçamaz.
- Çekirdek büyürse ya da kurallar sık değişirse yeniden değerlendirilir.

## Dersler

- **Codesign hatası** ("code object is not signed at all, In subcomponent: embedded.mobileprovision"): Neden, app içindeki üst düzey kaynak klasörünün adının `Resources` olmasıydı; `Data` yapılınca düzeldi. `6bc018e` commit mesajı ve `scripts/device.py`'deki yorum iCloud extended attribute'larını da neden olarak gösteriyor; bu doğrulanmadı. Derived data'yı Desktop dışına taşımak tek başına düzeltmedi.
- **Mikrofonsuz modlar ekranda çalışmalı.** Parity ve TTS modunda app ön planda değilse iOS askıya alıyor (ilk parity denemesi Expo Go açıkken durdu). Mikrofonlu canlı mod arka planda sürüyor.
- **`AVSpeechSynthesizer.write` uzun metinde cümle aralarında boş buffer gönderiyor.** Boş buffer bitiş sayılınca uzun meal'ler kesildi; bitiş `didFinish` delegate'i olmalı.
- **Wi-Fi `devicectl`** başlatma, yükleme ve dosya çekmede çalıştı. Telefon kilitli kaldıktan bir süre sonra cihaz "unavailable" oldu; kilit açılınca döndü.

## Sınırlamalar

- **Tek cihaz.** iPhone 17 en yeni model; eski iPhone'larda RTF, ısınma ve bellek ölçülmedi. "En az hangi cihaz" sorusu açık.
- **Android yok.** Ölçülmedi.
- **Pil ölçülmedi.** iOS pil seviyesini app'e %5 adımla veriyor; anlamlı ölçüm ≥ 1 saatlik kablosuz koşu ister.
- **Loopback oda koşulunu ölçmüyor.** TV, cami ve canlı okuyucu mesafesi gerçek ortamda denenmedi (M4 sınırı sürüyor).
- **Tek motor oturumu 8 akış boyunca sürdü.** M4'te her akış ayrı oturumdu; akış geçişi okuyucu değişimi gibi davrandı. Gerçek kullanımda okuyucu değişimi bundan seyrek.
- **Kilit, İsmail'in gözlemine dayanıyor.** App kilit durumunu log'a yazmıyor.

## Sonraki adım önerisi (onay bekliyor)

- **Saha denemesi (iPhone):** TV, bilgisayar hoparlörü ve canlı okuyucu; farklı mesafe ve odalar. Loopback'in ölçmediği tek önemli koşul bu. Ground truth yok; İsmail'in gözlemi + log.
- **Pil:** ≥ 1 saat, kablosuz, kilitli; gerçek kullanım süresi için.
- **Paket:** Yapıldı (Piper Eren, HE-AAC 16 kbps). Parity klipleri yayın paketine geçerken çıkarılacak.
- **U7, lisans:** Diyanet meal metni ve Piper Eren sesinin (`99eren99`) app içinde dağıtılması. Ürüne geçmeden önce çözülmeli; paket kararını etkileyebilir.
- **M7 (Klasik Arapça)** planda ayrı bir scope kararı; kapalı derlem varsayımını bozuyor. Ürün yolu seçilirse ertelenebilir.
