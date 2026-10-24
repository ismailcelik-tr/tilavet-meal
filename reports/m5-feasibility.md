# M5 — Sağlamlık Raporu ve GO/NO-GO

Tarih: 2026-10-24 · Spec: [m5-robustness-design](../docs/superpowers/specs/2026-10-24-m5-robustness-design.md) · Kör set ham sayıları: [m5-blind.md](m5-blind.md) (`scripts/replay_m3.py --set blind2`) · Motor kuralları: `398b251` · Model: tiny

## Karar özeti

| Kapı | Eşik | Sonuç |
|---|---|---|
| Yanlış meal, clean | ≤ %0.5 | **0/280** ✅ (üç koşul birlikte 0/837, üçler kuralıyla ≤ %0.36) |
| Yanlış meal, hard | ≤ %1 | **0/278** ✅ (≤ %1.1) |
| Recall clean / noisy / hard | ≥ 95 / 75 / 85 | 96.2 / 95.8 / 95.5 ✅ |
| Okuyucu çeşitliliği (hard): min ≥ medyan − 10 | | 91.4 vs 95.4 ✅ |
| 30 s duraklamada meal | 0 | **0** (40 duraklama × 3 koşul) ✅ |
| Kur'an dışı konuşma | ≤ 1 yanlış / saat | **0 yanlış / 42 dk** ✅ (örneklem kısa) |
| Kaynak: RTF / RAM | ≤ 0.3 / ≤ 1.5 GB | 0.034–0.037 / 265 MB ✅ |
| Gecikme, kulaklık dahil (M4) | p50 ≤ 1.5 s, p90 ≤ 3 s | −12.8 / −5.0 s ✅ |

**Öneri: GO.** Her kapı geçti. Mobil aşamaya (M6) geçilebilir. Karar İsmail'in.

GO'nun sınırları:

- Konser kayıtlarında meal çalmıyor (M4; kabul edildi).
- Hoparlörden çalma yankı giderme olmadan işe yaramıyor; kulaklık şart.
- Kur'an dışı konuşma testi 42 dakika. Bir saatlik eşiği güçlü biçimde kanıtlamıyor; M6'da gerçek kullanımla izlenmeli.

## Motor kuralları

M4 kör setindeki 8 yanlışın kök nedenleri incelendi. Spec'teki ilk tahmin (`و` öneki) yanlıştı; gerçek nedenler şunlar:

- **Aday sınırı:** Kalıp ifadenin nadir kelimeleri (`السماوات`, `والأرض`) ~200 yerde hizalanıyor; motor yalnız ilk 8'ini deniyordu. Asıl benzer ayet (21:19) 120. sıradaydı.
- **Hipotez kelimeleriyle oylama:** Yanlış duyulan kelimeler (`فوبدا`, `سييات`) oy vermiyordu. Bu yüzden tek kelimeyle ayrılan 45:33, 39:48'e rakip olamadı.
- **Marj:** Okuyucunun geri dönüp okuduğu 22:55, sıradaki 22:57'nin açılışına benziyordu. Skoru (5) tartışmalı sayılma sınırının (7 − 2) hemen altında kaldı.

| Kural | Değişiklik | Giderdiği (M4) |
|---|---|---|
| **L** (`14b1bb0`) | Benzer pasaj araması, kazananın eşleştiği **derlem kelimeleriyle** oy topluyor; aday sınırı yok. | Kalıp ifade (4), Lost sonrası benzer ayet (1), NVIDIA halüsinasyonu (2) |
| **P** (`398b251`) | Zaten onaylanmış ayetlerdeki rakipler `past_margin = 3` ile tartışmalı sayılıyor. | Tekrarı ilerleme sanmak (1) |

**Ayar verisi** (dev + eski test + M4 kör seti; artık açık, sonuçlar iyimser):

| | Önce | L | L + P |
|---|---|---|---|
| tiny yanlış (toplam) | 3 | 1 | **0** |
| NVIDIA yanlış, M4 kör | 5 | 0 | 0 |
| En büyük recall kaybı | – | 0.6 puan | 0.6 puan |
| p50 gecikme değişimi | – | ≤ +0.1 s | ≤ +0.1 s |

- Global `track_margin = 3`, P'ye üstünlük getirmedi ve 0.1–0.2 s gecikme ekledi; seçilmedi.
- Alternatif B (nadir kelime şartı) gerekmedi.
- L, Acquire adımını ~13 ms'ye çıkarıyor. Bu yalnız konum bilinmezken ödeniyor; replay süresi %15 arttı.

Kurallar `398b251`'de donduruldu (İsmail onayı). Kör set ondan sonra açıldı.

## Yeni kör set (blind2)

- **Okuyucular:** Husary mücevved, Tablavi (mücevved), Gamidi (40 kbps), Huzeyfi.
- **Akışlar:** Okuyucu başına 10, seed 47, toplam 144 dk. Her akışta bir 30 s duraklama var.
- **Model:** yalnız tiny.

| Koşu | Meal | Yanlış | Geç | Recall | Lost | Meal − ayet başı p50 / p90 | CER |
|---|---|---|---|---|---|---|---|
| clean | 280 | 0 | 1.1% | 96.2% | 3 | 4.3 / 8.4 s | 0.18% |
| noisy | 279 | 0 | 1.1% | 95.8% | 9 | 4.4 / 8.6 s | 0.66% |
| hard | 278 | 0 | 0.7% | 95.5% | 15 | 4.4 / 10.0 s | 3.82% |

**Mücevved:** M4'ün zayıf noktasıydı, burada yanlış meal yok. Bedeli gecikme: Husary mücevvedde meal ayet başından p50 8–9 s sonra geliyor (diğerlerinde ~4 s). Uzun mücevved ayetlerinde bu yine de birim bitmeden önce (birim sonundan p50 −22 s).

| hard recall | Gamidi | Huzeyfi | Husary mücevved | Tablavi |
|---|---|---|---|---|
| tiny | 94.8% | 98.7% | 91.4% | 96.0% |

## Kur'an dışı konuşma

Telefon hoparlörü, MacBook mikrofonu, kulaklık bağlı ama takılı değil. Kayıt: `data/derived/m4/live/20261024-212524`.

| Bölüm | Süre | Meal | Doğrulama |
|---|---|---|---|
| Türkçe sohbet (YouTube, reklamlar dahil) | ~30 dk | 6 | Altısı da hocanın Arapça okuduğu ayetler: 39:53 (iki kez), 36:65, 25:63, 93:5. ASR metninde görülüyor (`قل يا عبادي الذين أسرفوا`, `اليوم نختم على أفواههم`…). **Yanlış 0.** |
| Arapça konuşma (YouTube `fIU7heH1uMw`) | ~11 dk | 0 | İsmail'e göre ayet okunmadı. |

- **Tekrar kuralı:** 39:53'ün ikinci meali 8 dakika sonra çalındı. Hoca ayeti yeniden okumuştu ve 5 dakikalık tekrar kuralı dolmuştu. Doğru davranış.
- **Alıntı uzunluğu:** Bir alıntı birkaç kelimeyse meal tam ayetin mealidir. Hoca ayetin yalnız bir parçasını okuduysa dinleyici daha uzun bir meal duyar. Bu bir ürün kararıdır; hata sayılmadı.

## Kaynak kullanımı

- **ASR süresi:** pencere başına p50 0.034–0.037 s, 1 s adımda RTF ~0.035. Mac M5'te, tek çekirdek.
- **Canlı oturum (42 dk, `ps` ile 5 s arayla):** CPU medyan %12, en yüksek %77.
- **RAM:** Boru hattının kendisi 265 MB (model + motor + 30 s ses).
  - Oturumdaki 1.2 GB tepe ölçüm amaçlıydı: canlı kaydın bellekte tutulması (~165 MB) ve oturum sonundaki kurtarma adımı. Mobilde bu kayıt tutulmaz.

## Olay: mikrofon akışı kapanırken donma

42 dakikalık oturum sonunda CoreAudio, mikrofon akışını durdururken (`AudioOutputUnitStop`) dakikalarca dondu. Kayıt ve log yalnız bellekteydi.

- **Kurtarma:** lldb ile sürece bağlanıldı ve kaydı diske yazan Python kodu çalıştırıldı.
- **Düzeltme:** `live.py` artık akışı kapatmadan önce diske yazıyor (`32500df`).
- **Mobil notu:** Ses oturumunun kapanışı ayrı ele alınmalı (iOS AVAudioSession, Android AudioRecord).

## Sınırlamalar

- **Sentetik akışlar:** Kör set stüdyo kayıtlarından üretildi. Gerçek tilavet geçişleri ve vakf/ibtida (durup geri dönerek başlama) farklı.
- **Husary'nin sesi dev setinde var** (murattal). Kör setteki mücevved kaydı tarz olarak farklı, ama ses aynı.
- **Leakage:** tiny'nin model kartı bu okuyucuları listelemiyor; eğitimde olup olmadıkları bilinmiyor.
- **Örneklem:**
  - Koşu başına ~280 meal. Tek koşulda 0 hata, üçler kuralıyla ≤ %1.1 diyor; clean'deki %0.5 eşiği yalnız üç koşul birlikte (837 meal) kanıtlanıyor.
  - Kur'an dışı konuşma 42 dk.
- **Ölçülmeyenler:** cami ve TV oda akustiği (yalnız M4'teki kısa canlı denemeler); hadr (hızlı) tempo ayrı ölçülmedi; mobil cihaz; pil.
- **Konser kayıtları:** meal yok (M4, kabul edildi).

## M6 önerisi (GO ise, onay bekliyor)

Plan Bölüm 5:

- sherpa-onnx ile iOS/Android'de aynı tiny modelin ölçülmesi: RTF, RAM, pil.
- Paket boyutu: model + meal sesleri (434 MB, sıkıştırma gerekli).
- Arka planda mikrofon izni ve yankı giderme (hoparlör modu için).
- Çekirdeğin taşınma stratejisi: Swift/Kotlin'de yeniden yazım ya da paylaşılan çekirdek.
- **Paralel (U7):** Diyanet meal metni ve seslendirme lisansı.
