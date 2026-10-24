# M3 — Position Engine Raporu

Tarih: 2026-10-24 · Ham sayılar: [m3-results.md](m3-results.md) (`scripts/replay_m3.py` üretir) · Motor kuralları: `src/tilavet/engine/tracker.py`

## Karar özeti

Test okuyucuları, plan Bölüm 6 eşikleri:

| Kapı | Eşik | NVIDIA | tiny |
|---|---|---|---|
| Yanlış meal, stüdyo (clean) | ≤ %0.5 | **%0** ✅ | **%0** ✅ |
| Yanlış meal, telefon/canlı (hard) | ≤ %1 | **%1.3** ❌ (2/156) | **%0** ✅ |
| Recall, stüdyo | ≥ %95 | %97.5 ✅ | %96.3 ✅ |
| Recall, gürültü (noisy / hard) | ≥ %75 / ≥ %85 | %97.5 / %94.5 ✅ | %95.7 / %95.1 ✅ |
| Okuyucu çeşitliliği (hard): min ≥ medyan − 10 | | 72.4 vs 99.0 ❌ | 86.2 vs 95.1 ✅ |
| Meal başlangıcı − birim sonu, p50 / p90 | ≤ 1.5 / ≤ 3 s | −8.8 / −2.1 s ✅* | −8.1 / −2.6 s ✅* |

\* Simülasyon: ASR süresi dahil; mikrofon, oynatma ve TTS gecikmesi hariç (M4'te ölçülecek). Negatif değer, mealin okuyucu birimi bitirmeden başladığı anlamına gelir.

**Öneri:** M4'e geç. Motor, sentetik akışlarda clean ve 10 dB gürültüde hiç yanlış meal vermedi. 0 dB'de (hard) NVIDIA iki yanlış verdi; ikisi de bilinen bir hata türü (benzer ayet, bozulan ayırt edici kelime). Düzeltme M4'te, yeni bir kör kontrol setiyle yapılmalı.

## Değerlendirme düzeni

- **Akışlar:** EveryAyah ayet dosyaları mushaf sırasıyla birleştirildi. %12 tekrar, %6 atlama, %8 uzun duraklama (8–20 s) eklendi. 6 okuyucu × 5 akış = 30 akış, toplam 86 dakika. Ground truth dosya adlarından gelir (`scripts/build_streams.py`).
- **Dev / test ayrımı:** dev = Husary, Shuraim. test = Hani ar-Rifai, Minshawi, Abdulbaset (mücevved), Sudais.
- **Koşullar:**
  - `clean`: ham ses.
  - `noisy`: 10 dB SNR + telefon bandı + oda yankısı.
  - `hard`: 0 dB SNR + aynı filtre.
- **Canlı simülasyon:** 12 s pencere, 1 s adım. Her pencerenin ASR çıktısı ve ölçülen işlem süresi önbelleğe alınır (`scripts/asr_windows.py`); motor bu önbellek üzerinden oynatılır. Meal zamanı = pencere sonu + o pencerenin ASR süresi.
- **Metrikler:**
  - **Yanlış:** son 10 s içinde okunmamış bir ayetin meali (yanıltıcı).
  - **Geç:** doğru meal, ama birim bittikten 2–10 s sonra.
  - **Recall:** ilk kez okunan meal birimlerinden zamanında çalınanlar.
  - **Mükerrer:** aynı birimin tekrar çalınması.

## Sonuçlar (test okuyucuları)

| Koşu | Meal | Yanlış | Geç | Recall | Lost | Başlangıçtan p50 / p90 | CER |
|---|---|---|---|---|---|---|---|
| NVIDIA / clean | 159 | 0% | 0% | 97.5% | 2 | 3.7 / 7.5 s | 1.13% |
| NVIDIA / noisy | 159 | 0% | 0% | 97.5% | 1 | 3.6 / 6.6 s | 1.62% |
| NVIDIA / hard | 156 | **1.3%** | 0% | 94.5% | 8 | 3.8 / 8.9 s | 7.48% |
| tiny / clean | 158 | 0% | 0% | 96.3% | 1 | 4.0 / 6.4 s | 0.35% |
| tiny / noisy | 157 | 0% | 0.6% | 95.7% | 4 | 4.3 / 6.9 s | 1.01% |
| tiny / hard | 155 | 0% | 0.6% | 95.1% | 7 | 4.3 / 7.9 s | 5.11% |

Dev okuyucularında altı koşunun hepsinde yanlış %0, recall %98.4. Hiçbir koşuda mükerrer meal yok.

## Bulgular

1. **Clean ve 10 dB gürültüde yanlış meal yok.** Tekrar, atlama ve duraklamalar dahil. Meal, ayet başladıktan medyan 3.6–4.3 s sonra çalıyor. Birimlerin %90'ından fazlasında okuyucu birimi bitirmeden başlıyor.
2. **Hard'da NVIDIA'nın iki yanlışı:**
   - **abdulbaset-mujawwad-1, t=57 s: 37:169 yerine 37:40.**
     - Okuyucu `لكنا عباد الله المخلصين` okuyor. ASR ilk kelimeyi `لا` duydu: `لهم لا عباد الله المخلصين`.
     - Bu, Saffat'ta dört kez geçen `إلا عباد الله المخلصين` ifadesine (37:40, 74, 128, 160) çok yakın.
     - Motor bu sırada konumu bilmiyordu (Acquire modu). Fazladan gelen `لهم` kelimesi muhtemelen 37:41'deki (`أولئك لهم`) eşleşmeyle 37:40'a oy verdi ve onu diğer üç eşinden ayırdı.
   - **sudais-3, t=84 s: 71:13 okuyucu o ayete gelmeden 3 s önce.**
     - Pencerenin sağ kenarında ASR, 71:12'nin sonundaki `ويجعل لكم أنهارا` kısmını `ويجعل ما لكم` olarak duydu. `ما لكم`, 71:13'ün ilk iki kelimesi.
     - Sıradaki ayet olduğu için motor ek kanıt istemedi.
   - **Ortak nokta:** Gürültü, ayetleri ayıran kelimeyi komşu bir ayetin kelimesine dönüştürüyor. Track modunda sıra dışı onaylar bu yüzden ek kanıt istiyor. Acquire modunda ve sıradaki ayette bu koruma yok.
3. **Hard'da tiny, NVIDIA'dan iyi.** CER %5.11'e karşı %7.48, yanlış %0'a karşı %1.3. M2'de telefon kayıtlarında sonuç tersiydi (NVIDIA CER %3.41, tiny %5.35). İki ihtimal var: simüle edilen bozulma gerçek telefon sesinden farklı, ya da NVIDIA ağır gürültüde daha çok uyduruyor (halüsinasyon). M2'deki birincil model kararı bu tek ölçümle değişmez; M4'te gerçek kayıtla iki model birlikte ölçülmeli.
4. **Mücevved en zayıf okuyucu.**
   - Recall: clean'de %86.2 (NVIDIA) / %82.8 (tiny); hard'da %72.4 / %86.2.
   - abdulbaset-mujawwad-1'de ilk kilitlenme clean'de bile 39–41 s sürüyor. Nedeni: ilk iki ayet (37:166, 37:167) üçer kelime, mücevvedde her biri ~15 s. Acquire en az 4 eşleşen kelime istiyor; kelimeler yeterince hızlı birikmiyor.
   - İlk ayet(ler)in meali kaçıyor ama yanlış meal çalınmıyor. Bu kayıp tasarım gereği: sessizlik, yanlış mealden iyidir.
5. **Hard'da takip kaybı (Lost) artıyor:** test akışlarında 8 (NVIDIA) ve 7 (tiny); clean'de 1–2. Kayıp sonrası yeniden kilitlenme, recall düşüşünün ana kaynağı.

## Test setinin körlüğü

**Test seti kör değil.** Motorun beş kuralı test akışlarındaki gerçek hatalara bakılarak eklendi (`tracker.py` modül docstring'i ve `EngineConfig`). Kurallar:

- açılış kelimeleriyle onay;
- ayete özgü eşik;
- eşitlikte en yeni kelime ve konum;
- sıra dışı onaya ek kelime;
- tartışmalı kelimeleri düşme.

Clean ve noisy test sonuçları bu yüzden iyimser.

`hard` koşulu tek bağımsız kontroldür. Kurallar `1045492`'de donduruldu, `hard` sonuçları ondan sonra üretildi (`3604265`) ve motor değiştirilmedi. `--sweep` parametre taraması çalıştırılmadı.

## Sınırlamalar

- **Sentetik akış.** Stüdyo kaydı ayet dosyaları birleştirildi. Gerçek tilavette ayet geçişleri, nefes, vakf ve ibtida (durup geri dönerek başlama) farklı. Gürültü ve yankı simüle edildi; hoparlör ve mikrofon zinciri yok.
- **Leakage.** NVIDIA EveryAyah ile eğitildi; test kayıtlarının kendisini görmüş olabilir. tiny, model kartına göre Hani ar-Rifai ve Minshawi'yi görmedi; diğer ikisini muhtemelen gördü.
- **Küçük örneklem.** Koşu başına ~156 meal: tek bir hata oranı 0.6 puan değiştirir. Plan ≥ 8 okuyucu istiyordu, test setinde 4 var.
- **Ölçülmeyenler:**
  - Kur'an dışı konuşma (hutbe, sohbet).
  - Tam sure kayıtları (plan M3 (b)).
  - Tilawa karşılaştırması (plan M3 (c)).
  - 30 s'lik duraklama (akışlarda en fazla 20 s).
- **Kaynak kullanımı.** ASR süresi M5 CPU'da, tek süreçte ölçüldü. Pencere başına p50: NVIDIA 0.21 s, tiny 0.034 s. 1 s adımda bu, NVIDIA için sürekli ~%21 tek çekirdek demek. 12 s'lik pencere her saniye baştan işlendiği için iş 12 kat tekrarlanıyor.

## Açık sorular

- Acquire ve sıradaki-ayet onayında benzer ayet koruması (bulgu 2) M4'te eklensin mi? Eklenirse yeni bir kör set gerekir: `Quran-Lab/mfa-quran-hafs` ile hizalanmış gerçek kayıtlar ya da yeni okuyucular.
- Mücevvedde ilk ayetin kaçması kabul mü? Alternatif: Acquire'ı kısa ayetler için gevşetmek. Bunun bedeli yanlış meal riskinin artması.
- Birincil model: M4'te gerçek kayıtla NVIDIA ve tiny birlikte ölçülsün.

## M4 önerisi (onay bekliyor)

Canlı mikrofon + EmissionPolicy + kulaklık çıkışı (plan M4):

- `sounddevice` ile ses yakalama.
- Pre-render meal oynatma.
- Loopback ölçüm düzeneği: kayıt hoparlörden çalınır, mikrofon alır, çıkış zaman damgalanır. Bunun için İsmail'in izni gerekiyor.
- Gerçek uçtan uca gecikme ölçümü.
- NVIDIA ve tiny birlikte çalışır.
- Bulgu 2'nin düzeltmesi yalnız yeni kör setle değerlendirilir.
