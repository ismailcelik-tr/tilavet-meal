# M4 — Canlı Zincir ve Kör Set Raporu

Tarih: 2026-10-24 · Spec: [m4-live-loopback-design](../docs/superpowers/specs/2026-10-24-m4-live-loopback-design.md) · Kör set ham sayıları: [m4-blind.md](m4-blind.md) (`scripts/replay_m3.py --blind`) · Motor kuralları: `993514c`

## Karar özeti

| Kapı (Bölüm 6) | Eşik | tiny | NVIDIA |
|---|---|---|---|
| Canlı oturum: yanlış / recall | ≤ %1 / ≥ %85 | **%0** (0/68) / %95.7 ✅ | – (yalnız tiny canlı) |
| Gecikme, kulaklık dahil: meal başlangıcı − birim sonu p50 / p90 | ≤ 1.5 / ≤ 3 s | −12.8 / −5.0 s ✅ | – |
| Birikme: 15 s'yi aşan bekleme | yok | 0 ✅ | – |
| Kör set, yanlış meal clean | ≤ %0.5 | **%0** (0/292) ✅ | **%0.34** (1/295) ✅ |
| Kör set, yanlış meal hard | ≤ %1 | **%1.05** (3/287) ❌ sınırda | **%1.09** (3/276) ❌ sınırda |
| Kör set, recall clean / noisy / hard | ≥ 95 / 75 / 85 | 95.4 / 95.1 / 92.5 ✅ | 96.1 / 95.4 / 88.6 ✅ |
| Kör set, okuyucu çeşitliliği (hard): min ≥ medyan − 10 | | 80.0 vs 94.3 ❌ | 51.7 vs 97.1 ❌ |

**Öneri:** Birincil model **tiny** olsun (M2'deki NVIDIA kararının yerine). Canlı zincir çalışıyor: gecikme ve birikme sorunu yok, gerçek akustik yolda yanlış meal çıkmadı. Açık risk tek bir yerde toplanıyor: **mücevved okuyuş**. Kör setteki 8 yanlışın 7'si tek bir mücevved okuyucuda. Gerçek bir konser kaydında ise hiç meal çalınmadı. M5 bu noktaya odaklanmalı.

## Canlı zincir (loopback)

**Düzen:** Akış MacBook hoparlöründen çalındı ve MacBook mikrofonuyla kaydedildi. Aynı anda canlı boru hattı çalıştı: tiny → `PositionEngine` → `EmissionPolicy` → `MealPlayer`. Ground truth'un zaman kayması cross-correlation ile bulundu (`scripts/loopback.py`).

**Smoke (`shuraim-2`):** SNR 29 dB. Oda kaydının CER'i (%0.10) clean ile aynı çıktı. Hoparlörle mikrofon aynı kasada olduğu için bu yol akustik zorluk eklemiyor. Bu yüzden 2.5 saatlik oturum 33 dakikaya indirildi (spec revizyonu).

**33 dakikalık oturum** (eski testten 8 akış; Abdulbaset mücevved, Hani ar-Rifai, Minshawi, Sudais):

| Ölçüm | Değer |
|---|---|
| Meal / yanlış / geç | 68 / 0 / 0 |
| Recall | 67/70 (kaçan 3 meal: `abdulbaset-mujawwad-1`'in ilk kilitlenmesi, M3 bulgu 4) |
| Meal başlangıcı − ayet başı, p50 / p90 | 4.4 / 6.8 s |
| Meal başlangıcı − birim sonu, p50 / p90 | −13.2 / −5.4 s |
| Kuyruk beklemesi / atlanan meal | 0 / 0 |
| Mikrofon taşması / atlanan pencere | 0 / 0 |
| SNR / oda CER | 14–26 dB / %0–1.32 |

`minshawi-0`'da oda gürültüsü daha yüksekti; oturum sırasında bilgisayar kullanılıyordu. Recall yine 10/10.

**Kulaklık gecikmesi** (`scripts/click_test.py`, CMF Buds 2a, 3'er tekrar): hoparlör medyanı 87 ms, kulaklık 401 ms; Bluetooth ek gecikme **~314 ms**. Ölçümün güvenlik kontrolü (SNR ≥ 10 dB) fazla sıkı çıktı ve iki kez durdu. Altı ölçüm SNR'dan bağımsız tutarlıydı, medyan kabul edildi. Oturum gecikmelerine yuvarlanmış 0.4 s eklenince meal başlangıcı − ayet başı p50 4.8 s, meal başlangıcı − birim sonu −12.8 / −5.0 s.

## Benzer ayet düzeltmesi

M3'ün iki hata türünden:

- **(a) Acquire'da benzer pasaj: düzeltildi.** Kazanan pasajın nadir kelimeleri başka yerde hizalanıyorsa o yer, oy eşiğinin altında kalsa da rakip olarak aranıyor (`acquire_rival_votes = 2`). Dev ve eski test setinde NVIDIA hard yanlışı 2'den 1'e indi, başka koşulda bedeli yok. Ana set sonuçları bu kuralla yeniden üretildi; NVIDIA hard %1.3'ten %0.6'ya indi ([m3-results.md](m3-results.md)).
- **(b) Pencere kenarında sıradaki ayetin erken onayı: düzeltilmedi, karar İsmail'in.** Açılış kelimelerini iki ardışık pencerede görmek (kalıcılık) hatayı gideriyordu. Ama bedeli her onaya ~1 s gecikme ve 2.5 puana kadar recall kaybıydı. Tek kazancı, doğru sıradaki ayetin birkaç saniye erken çalınmaması. Kabul edilebilir bulundu ve reddedildi.

Kurallar `993514c`'de donduruldu (`15876b8`). Kör set ondan sonra açıldı ve motor değişmedi.

## Kör set

**Kurulum:** 4 yeni okuyucu (Alafasy, Maher al-Muaiqly, Muhammad Ayyoub, Minshawi mücevved). Okuyucu başına 10 akış, seed 29. Akışlar M3 ile aynı yöntemle üretildi (tekrar, atlama, duraklama). Spec okuyucu başına 5 akış diyordu, 10'a çıkarıldı: 0 hatada üçler kuralının verdiği üst sınır ~%2'den ~%1'e iner. ASR geçişleri bitene kadar ne metne ne sonuçlara bakıldı.

**Sonuçlar** (40 akış; ayrıntı [m4-blind.md](m4-blind.md)):

| Koşu | Meal | Yanlış | Recall | Lost | Meal − ayet başı p50 / p90 | CER |
|---|---|---|---|---|---|---|
| tiny / clean | 292 | 0% (≤ %1.0, üçler kuralı) | 95.4% | 5 | 4.1 / 7.1 s | 0.34% |
| tiny / noisy | 292 | 0% (≤ %1.0) | 95.1% | 7 | 4.2 / 7.4 s | 0.84% |
| tiny / hard | 287 | **1.05%** | 92.5% | 17 | 4.0 / 8.0 s | 3.54% |
| NVIDIA / clean | 295 | 0.34% | 96.1% | 8 | 3.7 / 7.2 s | 2.12% |
| NVIDIA / noisy | 294 | 0.34% | 95.4% | 7 | 3.3 / 7.0 s | 2.11% |
| NVIDIA / hard | 276 | **1.09%** | 88.6% | 19 | 3.0 / 7.2 s | 9.83% |

**Hard sınırda.** Her iki model 3 yanlış verdi. %95 güven aralığı kabaca %0.4–3; bu örneklem %1 eşiğinden ayırt etmiyor.

**Hatalar tek okuyucuda toplanıyor.** 8 yanlışın 7'si Minshawi mücevvedde. Bu okuyucu çıkarılınca tiny hard 1/236 (%0.4), NVIDIA 0. M3'te de en zayıf okuyucu mücevvedydi (Abdulbaset). Yani bu tek seferlik bir sapma değil, bir örüntü.

| hard recall | Alafasy | Maher | Ayyoub | Minshawi mücevved |
|---|---|---|---|---|
| tiny | 95.9% | 97.8% | 92.6% | **80.0%** |
| NVIDIA | 98.6% | 97.8% | 96.3% | **51.7%** |

## Hata mekanizmaları (kör set, 8 yanlış, 4 olay)

1. **Kalıp ifade + pencere kenarı (4 yanlış: NVIDIA clean/noisy/hard, tiny hard; `minshawi-mujawwad-8`).**
   - Mücevved çok yavaş: 12 s'lik pencerede yalnız 21:19'un başı duyuluyor, `وله من في السماوات والأرض`.
   - Pencere kenarı baştaki `و`'yu kesince `له من في السماوات والأرض` kalıyor. Bu, birebir yalnız 24:41'de (NVIDIA hard'da 27:65) geçiyor.
   - Skor 10, en yakın rakip 7: marj 3, eşik tam karşılanıyor. 21:19 rakip olarak bile çıkmıyor, çünkü `وله` ayrı bir kelime.
   - Yanlış meal ~14 s'de çalıyor. ~8 s sonra takip kayboluyor, sonra doğru yere kilitleniyor.
   - **Yeni mekanizma.** ASR gürültüsü değil, clean'de de oluyor: pencerede ayırt edici kelime yok, yalnız sık geçen bir kalıp ifade var.
2. **NVIDIA halüsinasyonu (2 yanlış, NVIDIA hard, `minshawi-mujawwad-2`).** NVIDIA 0 dB gürültüde okunmayan ama Kur'an'da geçen ifadeler üretiyor: `ما لم ينزل به سلطانا` (22:71), `والله بصير بما تعملون` (49:18). Motor bunları gerçek okuyuş gibi buluyor. Bu akışta recall 0/4. tiny'de bu davranış görülmedi.
3. **Lost sonrası benzer ayet (1 yanlış, tiny hard, `minshawi-mujawwad-1`).** Takip kaybolunca motor surenin bağlamını unutuyor. 45:33 yerine 39:48'i seçiyor; iki ayet tek kelimeyle ayrılıyor (`عملوا` / `كسبوا`). M3 (a) türünün Lost sonrası hali.
4. **Tekrarı ilerleme sanmak (1 yanlış, tiny hard, `muhammad-ayyoub-1`).** Okuyucu 22:55–56'yı tekrar okuyor. Motor 22:55'in tekrarını sıradaki 22:57 sanıyor; ikisinde de `الذين كفروا` geçiyor. 22:57'nin meali **44 s erken** çalıyor. Bu, (b)'de kabul edilen "birkaç saniye erken" türü değil; dinleyiciyi yanıltır.

## Canlı deneme (İsmail, gerçek kaynak)

Kulaklık CMF Buds 2a, model tiny. Kayıtlar: `data/derived/m4/live/`.

| Kaynak | Sonuç |
|---|---|
| Telefon hoparlörü, Fatiha + Bakara başı (stüdyo kaydı) | 1:2–1:7 ve 2:2–2:4 doğru. Yanlış yok. |
| Telefon hoparlörü, Abdulbaset mücevved, **YouTube konser kaydı** (Tekvir) | **Hiç meal yok.** tiny anlamsız metin üretiyor (`وتقوحوش حوقصوز`). 59 pencerenin hiçbirinde Acquire adayı yok. NVIDIA daha iyi ama kilitlenmeye yetmiyor. Ses seviyesi sorun değil: Fatiha bölümünden yüksek. |
| İsmail'in sesi, kulaklık | Fatiha 1:3–1:7, İhlas 112:2–4 doğru. İlk ayetler (1:2, 112:1) Acquire için kelime biriktirirken kaçıyor. |
| İsmail'in sesi, meal MacBook hoparlöründen | Geri besleme: Türkçe meal mikrofona giriyor, tiny onu Arapça benzeri metne çeviriyor (`كتاب ومس ذان`), takip iki kez kayboluyor. Yanlış meal yok. |

Gözlemler:

- **Konser kaydında çöküş, M4'ün en önemli bulgusu.** Olası neden kayıt türü: salon yankısı ve dinleyici nidaları (`الله` ilk pencerelerde görünüyor). Testlerdeki mücevved kayıtlar stüdyo kaydıydı. Aynı okuyucunun stüdyo kaydıyla karşılaştırma yapılmadı, neden doğrulanmadı. Türkiye'de TV yayınları ve cami okuyuşları bu koşula yakın.
- **Besmele:** Kur'an metninde yalnız 1:1 olarak geçiyor. Bakara başındaki Besmele okununca 1:1'in meali çalındı. Okunanla anlamca doğru, ama etiket 1:1.
- **5 dakikalık tekrar kuralı:** Aynı sure 5 dakika içinde yeniden okununca motor doğru takip ediyor ama meal çalmıyor (`EmissionPolicy` cooldown). Okuyucu tekrarları için doğru davranış; kısa denemelerde sessizlik gibi görünüyor.
- **Hoparlörden çalma, yankı giderme olmadan işe yaramaz.** Kulaklık şart. Mobilde işletim sisteminin yankı gidermesi (iOS voice processing, Android AEC) bunu çözebilir; ölçülmedi.

## Model seçimi

M2'de NVIDIA seçilmişti (telefon kayıtlarında CER daha düşüktü). M3 ve M4 bu kararı değiştiriyor:

- Kör sette hard'da tiny NVIDIA'dan iyi: CER %3.54'e karşı %9.83, recall 92.5'e karşı 88.6, en zayıf okuyucuda 80.0'a karşı 51.7.
- NVIDIA gürültüde halüsinasyon yapıyor. Bu, yanlış meal üreten bir mekanizma (bulgu 2).
- Clean'de NVIDIA bir yanlış verdi, tiny hiç vermedi.
- tiny pencere başına ~6 kat hızlı (M3: 0.034'e karşı 0.21 s) ve küçük; mobil için uygun.
- NVIDIA'nın tek üstünlüğü: konser kaydında tiny'den daha anlamlı metin üretti. Yine de kilitlenmeye yetmedi.

## Sınırlamalar

- **Loopback, oda koşulunu ölçmüyor.** Hoparlör ve mikrofon aynı kasada. TV veya canlı okuyucu mesafesi ve yankısı yalnız canlı denemede, sayısal ground truth olmadan görüldü.
- **Kör sette leakage.** NVIDIA bu okuyucuları muhtemelen gördü (EveryAyah). tiny'nin model kartına göre Minshawi'nin murattal kaydı eğitimde yok; mücevved kaydı ve diğer üç okuyucu için bilgi yok.
- **Küçük örneklem.** Koşu başına ~290 meal: hard'daki %1 eşiği bu sayıyla ayırt edilemiyor. Clean'de 0 hata, üçler kuralıyla yalnız ≤ %1.0 diyor; %0.5 eşiğini kanıtlamak için ~600 meal gerekir.
- **Kör set artık kör değil.** Hata ayrıntılarına bakıldı. Bir sonraki kural değişikliği yeni bir kör set ister.
- **Canlı deneme kısa ve gayri resmi.** Toplam ~10 dakika, ground truth yok, tek konser kaydı.
- **Ölçülmeyenler:** Kur'an dışı konuşma (hutbe, sohbet); tam sure kayıtları; TV hoparlöründen oda mesafesi; mobil cihaz.
- **Meal ses boyutu:** 5.393 birim, 434 MB (AAC, 22 kHz). Mobil paket için büyük; tahmin 210 MB'tı.

## M5 önerisi (onay bekliyor)

Mücevved ve gerçek kayıt dayanıklılığı:

1. **Gerçek mücevved kayıtları ve ground truth.** Konser ve cami kayıtları ile `Quran-Lab/mfa-quran-hafs` hizalı tam sure kayıtları. Önce konser çöküşünün nedeni ayrılır: aynı okuyucunun stüdyo ve konser kaydı karşılaştırılır.
2. **Motor (TDD, her biri ayrı ölçülür):**
   - Acquire'da kalıp ifadeye kilitlenmeme: en az N nadir kelime ya da sık geçen ifadelerin skorunun düşürülmesi (mekanizma 1, 2).
   - Lost sonrası son konuma yakın adayı tercih etme (mekanizma 3).
   - Okuyucu tekrarını ilerlemeden ayırma (mekanizma 4).
3. **ASR:** konser koşulu için tiny'nin ince ayarı (fine-tuning) ya da yankı ve dinleyici sesini içeren veri ile yeniden değerlendirme. Kapsamı 1'in sonucuna bağlı.
4. **Yeni kör set:** en az iki mücevved okuyucu, okuyucu başına 10+ akış.
