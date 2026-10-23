# M1 — Kağıt Üstü Fizibilite Raporu

Tarih: 2026-10-23 · Ham sayılar: [m1-results.md](m1-results.md) (`scripts/analyze_m1.py` üretir, deterministik)

## Karar özeti

| Soru | Sonuç | Kapı |
|---|---|---|
| **U1** Meal, tilavetten uzun mu? Birikir mi? | Toplamda hayır: oran 0.25 (mücevved) – 0.82 (en hızlı murattal). Ayet bazında hızlı okuyucuda birimlerin %18.6'sı > 1. **Erken başlatma** ile birikme sınırlı kalıyor (max 19 s @1.0x, 13 s @1.25x). | **GO** (koşullu) |
| **U2** Tekil tanıma kaç kelime? | Track: medyan **1 kelime**, %96.4'ü ≤ 3. Acquire: medyan 3, p90 6 kelime. | Olumlu |
| **U3** Aynı Arapça → aynı meal mi? | **Hayır.** 98 grubun 90'ında Diyanet mealleri farklı. | Varsayım çürüdü → tasarım kuralı |

**Öneri:** M2'ye (akustik model bake-off) geç. Tasarım kuralları ve bağlam politikası aşağıda.

## Veri ve yöntem

- Kur'an metni: Tanzil `quran-simple-clean` (CC BY 3.0, değiştirilmeden kullanılır; kaynak: [tanzil.net](https://tanzil.net)).
- Meal: Tanzil `tr.diyanet` (karşılaştırma: `tr.vakfi`); ticari olmayan kullanım.
- Tilavet zamanlaması: quran.com CDN API, 6 okuyucu × 114 sure, ayet ve kelime zaman damgaları. Okuyucular yavaştan hızlıya: Abdulbaset (mücevved, 58.6 saat), Husary (42.6), Alafasy (29.5), Minshawi (28.8), Sudais (21.0), Shuraim (18.2).
- Meal süresi: 5.393 meal biriminin macOS `say -v Yelda` (varsayılan hız) ile render süresi. Toplam **14.89 saat**, ~13.5 karakter/s.
- Tüm girdiler `data/manifest.json` içinde sha256 ile sabit; `tests/test_data_integrity.py` bunu doğrular.
- Doğrulama: 5 rastgele birim yeniden render edildi, CSV ile birebir aynı; tilavet süreleri ham JSON'dan bağımsız hesaplandı.

### Ön bulgu: "meal birimi"

Diyanet meali 6.236 ayeti **5.393 birimde** çeviriyor. **570 birim** birden fazla ayeti tek cümlede kapsıyor (en uzunu 12 ayet). Tanzil aynı metni o ayetlerin her birine yazmış. Vakfı mealinde bu sayı sadece 10. Bu yüzden çalma birimi ayet değil **meal birimi** (`MealUnit`).

## U1 — Süre ve birikme

**Birikme simülasyonu:** Mealler sırayla, üst üste binmeden çalınır. *Lag*, mealin çalınabilir olduğu an ile çalmaya başladığı an arasındaki farktır.

| Politika | Ne zaman çalınabilir | En hızlı okuyucu (Shuraim) @1.0x | @1.25x |
|---|---|---|---|
| **end** | Birim tamamen okunduktan sonra | lag p90 12.9 s, max **53 s**, %7.6'sı > 15 s | max 37 s |
| **early** | İlk ayet Track modunda tekil olunca | lag p90 2.1 s, max **14 s**, %0 > 15 s | max 7 s |

Çıkarımlar:
1. **Erken başlatma sadece gecikme iyileştirmesi değil, hızlı okuyucuda zorunluluk.** Ayet sonunu beklemek, uzun ayetlerden sonra (2:282'nin meali 78 s) 30–50 s birikme üretiyor.
2. early politikasında medyan meal, birim **bitmeden** 9–27 s önce başlıyor (okuyucuya göre). Plandaki "ayet sonundan sonra p50 ≤ 1.5 s" hedefi teoride rahatça karşılanıyor.
3. 1.25x hız, kalan uç durumları yarıya indiriyor. Gerekirse kullanılacak bir kaldıraç; varsayılan olması şart değil.

**Sınırlamalar (iyimser taraf):**
- Tanıma **kusursuz ve anlık** varsayıldı. Gerçek ASR'nin chunk gecikmesi (~0.5–1 s) ve hataları M3'te eklenecek.
- Yelda'nın hızı ölçüldü. Erkek ses / neural ses %10–20 yavaşsa oranlar aynı ölçüde kayar; script `--voice` parametresiyle yeniden ölçer.
- Hızlı **hadr** okuyuşu ve canlı teravih ölçülmedi. Shuraim/Sudais en yakın vekil.
- Her sure ayrı simüle edildi; surelerin ilk ayet süresine Besmele dahil.
- Kelime timing'i ayetlerin %78–94'ünde kullanılabildi; kalanlarda okuyucunun Track p90 süresi varsayıldı.

## U2 — Tekil tanıma

| Mod | p50 | p90 | ≤ 3 kelime | Saniye p50 (hızlı → yavaş okuyucu) |
|---|---|---|---|---|
| Track (önceki ayet biliniyor; ±3 ayet + önceki ayetin içinden yeniden başlama) | 1 | 2 | %96.4 | 0.8 s → 2.2 s |
| Global / Acquire (konum bilinmiyor) | 3 | 6 | %68.7 | 1.8 s → 4.7 s |

- Acquire modunda ayetlerin %5.6'sı, kendisi bitmeden tekil olmuyor; sonraki ayetin kelimeleri gerekiyor. En zor ayetler 70:29–30 ve 23:5–6 (iki surede neredeyse aynı pasaj, 25–29 kelime).
- Bu, ASR hatası **olmadan** bilgi-kuramsal alt sınır. ASR hatası, Track'te birkaç kelimelik güven payı gerektirecek.

## U3 — Metni aynı ayetler

- 98 grup, 280 ayet; 24 grup tek sure içinde (ör. Rahman nakaratı, 31 tekrar), 74 grup sureler arası.
- Diyanet'te gruplardan sadece 8'inin meali aynı; Rahman 55:13'ün 31 tekrarında **4 farklı** meal metni var.
- Neden: 44 grupta ayet çok ayetli bir meal birimine dahil, meal bağlama göre farklı. Kalanlarda çevirmen kelime seçimi farklı.

## Tasarım kuralları (M3–M4'e girdi)

1. **R1 — Duplicate bekleme:** Acquire modunda aday bir duplicate grubuna düşüyorsa, bağlam (sonraki ayet) gelene kadar commit yok. Sadece oturum başında / "Lost" sonrası gecikme ekler; Track modu bu grupları bağlamdan çözer.
2. **R2 — Erken commit:** Track modunda ilk 1–3 kelimeyle commit. Ayet sonunu bekleyen politika hızlı okuyucuda birikiyor.
3. **R3 — Cümle birimi bölünmez:** Meal her zaman bütün bir cümle birimi olarak çalınır (bkz. Bağlam politikası).

## Bağlam politikası

Soru (İsmail): Ayetler birbirine bağlıysa, ortadan başlayan bir ayetin meali tek başına anlaşılır mı?

İki ayrı bağ katmanı var:

**1. Cümle bağı:** Ayet, önceki/sonraki ayetle aynı cümlenin parçası.
- Yaygın: ayetlerin **%22.7'si (1.413 ayet)** Diyanet'te çok ayetli bir cümle biriminde.
- Ayet ayet çeviri bu durumda anlamsız parçalar üretiyor. Örnek, Vakfı 114:4 tek başına: *"O sinsi vesvesenin şerrinden,"*. Diyanet aynı üç ayeti tek cümlede veriyor.
- **Çözüm:** Çalma birimi cümle birimidir. Sistem bir birimin ortasındaki ayete girerse (oturum başı, yeniden yakalama) birimin **tamamı** baştan çalınır. Önceki ayetlerin anlamı cümle içinde zaten gelir.
- Diyanet'in 570 çok ayetli biriminin **hiçbiri** Tanzil'in 556 rükû sınırından biriyle bölünmüyor. İmam rükû noktasında durursa birim yarıda kalmaz. Erken başlatmanın "okunmamış ayetin anlamını önceden söyleme" riski bu yüzden düşük. Kalan risk, imamın rükû dışı bir yerde durması; M5'te gerçek kayıtla ölçülecek.
- "last" politikası (birimin son ayeti tanınınca çal) bu riski sıfırlar, ama hızlı okuyucuda birikmeyi geri getirir: Shuraim max lag 14 s → 40 s, birimlerin %3'ü > 15 s. **Öneri: early (birim başı).**
- **Sonuç: Diyanet İşleri meali bu hedefe Vakfı'dan daha uygun.** Cümle sınırlarını zaten veriyor.

**2. Konu bağı:** Hangi kıssa, kim konuşuyor ("dediler", kim?).
- Kesintisiz dinlemede kendiliğinden sağlanır, çünkü kullanıcı önceki mealleri zaten duymuştur. Sorun sadece **giriş noktalarında**: oturum başı, imamın yeni rekâta surenin ortasından başlaması, takip kaybı sonrası.
- Özet üretmek (LLM vb.) doğrulanmış meal ilkesini bozar → **yapılmaz**.
- Giriş noktası için öneriler, M4'te ölçülecek:
  - (a) Kısa künye anonsu: "Bakara suresi, 255. ayet". Doğrulanmış metadata, ~2 s.
  - (b) Okuyucu yavaşsa önceki birim(ler)in mealini hızlandırılmış "yakalama" olarak çal. Bütçe U1'den hesaplanır: mücevvedde oran 0.25, yani bol zaman; hızlı murattalde yok.
  - (c) Mobilde önceki meallerin ekranda metin olarak gösterilmesi.

## Senin vermen gereken karar

- Meal: Bağlam analizine göre öneri **Diyanet İşleri** (cümle birimleri hazır).
- Giriş noktası politikası (a/b/c) M4'e kadar açık kalabilir.

## M2 önerisi (onay bekliyor)

Plandaki kapsam geçerli: 3–4 Kur'an'a özel CTC modeli + Whisper baseline, leakage'sız okuyucularda CER, RTF, RAM. M1'den eklenen tek şey: CER yanında "**ilk 3 kelimenin doğru tanınma oranı**". U2'ye göre Track'in ihtiyaç duyduğu sinyal bu.
