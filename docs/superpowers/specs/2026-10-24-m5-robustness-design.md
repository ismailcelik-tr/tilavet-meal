# M5 — Sağlamlık ve GO/NO-GO Tasarımı

Tarih: 2026-10-24 · Onay: İsmail (tam M5) · Plan: M5 + Bölüm 6 · Önceki: [M4 raporu](../../../reports/m4-feasibility.md)

## Amaç

1. M4 kör setinde yanlış meal üreten mekanizmaları motor kurallarıyla gidermek ve sonucu hiç bakılmamış yeni bir kör sette sınamak.
2. Planın ölçülmemiş iki kapısını ölçmek: 30 s duraklama ve Kur'an dışı konuşma.
3. Kaynak kullanımını ölçmek.
4. Mobil aşamadan (M6) önce GO/NO-GO kararı.

Birincil model **tiny** (M4 önerisi). NVIDIA yalnız ayar verisinde, karşılaştırma için kalır.

## Kapsam dışı (İsmail kararı)

- **Konser kayıtları.** Dinleyici sesi ve yankı yüzünden meal çalmaması kabul edilebilir. Gerçek kayıt etiketleme ve ASR ince ayarı yapılmaz.
- SNR ve yankı matrisi: M3'ün clean / noisy / hard koşulları yeterli.

## 1. Motor kuralları

**Ayar verisi:** dev + eski test + M4 kör seti (artık açık), mevcut ASR önbelleğiyle. Hard koşul ağırlıklıdır.

Kök neden analizi (spec yazıldıktan sonra, M4 vakaları üzerinde):

- **Mekanizma 1:** `و` farkı sorun değil; bulanık hizalama 21:19'a zaten 9 puan veriyor (24:41: 10). 21:19 hiç hizalanmıyor, çünkü pencerenin nadir kelimeleri (`السماوات`, `والأرض`) ~200 yerde hizalanıyor ve aday sınırı 8. 21:19 120. sırada.
- **Mekanizma 3:** 45:33 hiç aday olmuyor. Rakip arama hipotezin kelimeleriyle oy topluyor; bulanık eşleşen kelimeler (`فوبدا`, `سييات`) oy vermiyor.
- **Mekanizma 4:** 22:55'in tekrarı rakip olarak bulunuyor ama skoru (5) kazananın (7) `track_margin` (2) sınırının altında; kelimeler tartışmalı sayılmıyor. `track_margin = 3` vakayı düzeltiyor.

| Mekanizma (M4) | Kural | Alternatif |
|---|---|---|
| 1 ve 3 (5 yanlış) | **L:** Benzer pasaj araması, kazananın eşleştiği **derlem kelimeleriyle** oy toplar ve aday sınırı uygulanmaz. Prototip: iki vaka da çözülüyor; Acquire adımı ~13 ms. | **B:** Acquire'da en az N nadir kelime şartı; L yetmezse ölçülür. |
| 4 (1 yanlış) | **P:** Zaten onaylanmış ayetlerdeki rakipler daha geniş marjla (`past_margin = 3`) tartışmalı sayılır. | Global `track_margin = 3`: vakayı çözüyor, bir meali 2 s geciktiriyor. Veriyle karşılaştırılır. |
| 2. NVIDIA halüsinasyonu (2 yanlış) | Ayrı kural yok; tiny birincil. | |

Kural ve parametreler kesin değil; ayar sırasında verinin gösterdiğine göre değişebilir. Değişmeyecek olanlar:

- Her kural TDD ile eklenir: önce M4 vakasından türetilmiş, başarısız olan bir test yazılır.
- Her kural için ayar verisinde yanlış, recall ve gecikme etkisi ayrı ayrı raporlanır.
- **Kabul sınırı:** Hiçbir koşulda recall 1 puandan fazla düşmüyor ve p50 gecikme 0.5 s'den fazla artmıyorsa kural kabul edilir. Sınırı aşarsa karar İsmail'in.
- **Dondurma:** Kurallar commit'le dondurulur (İsmail onayı). Sonra yeni kör set açılır (İsmail onayı). Açıldıktan sonra motor değişmez.

**Sonuç (2026-10-24, İsmail):**
- L ve P kabul edildi; ayar verisinde tiny yanlış 3 → 0, NVIDIA (M4 kör) 5 → 0, recall kaybı ≤ 0.6 puan, p50 ≤ +0.1 s.
- Global `track_margin = 3` P'ye üstünlük getirmedi, gecikme ekledi; seçilmedi. B gerekmedi.
- **Kurallar `398b251`'de donduruldu.**

## 2. Yeni kör set

- **Okuyucular:** EveryAyah'ta hiç kullanılmamış, ikisi mücevved. Erişim kontrol edildi (HTTP 200):

| id | Klasör | Tarz |
|---|---|---|
| `husary-mujawwad` | `Husary_128kbps_Mujawwad` | mücevved |
| `tablawi` | `Mohammad_al_Tablaway_128kbps` | mücevved |
| `ghamdi` | `Ghamadi_40kbps` | murattal, düşük bit hızı |
| `hudhaify` | `Hudhaify_128kbps` | murattal |

  Not: Husary'nin murattal kaydı dev setinde. Ses aynı, tarz farklı; raporda yazılır.

- **Akışlar:** Okuyucu başına 10, yeni seed. Yöntem M3 ile aynı (tekrar, atlama, duraklama). Her akışa ayrıca **bir adet 30 s duraklama** eklenir (bkz. 3).
- **ASR:** Yalnız tiny, clean / noisy / hard.
- **Körlük:** Dondurma onayına kadar ASR metnine ve sonuçlarına bakılmaz.
- **Leakage:** tiny'nin model kartı bu okuyucuları listelemiyor; eğitimde olup olmadıkları bilinmiyor. Raporda yazılır.

## 3. 30 s duraklama

- Kör set akışlarında her akışa bir 30 s sessizlik eklenir. Konumu, bir ayet sonunda rastgele seçilir.
- **Metrik:** Duraklama başladıktan 10 s sonra ile bittiği an arasında çalınan meal sayısı. İlk 10 s, son okunan ayetin meali için meşrudur.
- **Kapı:** 0.

## 4. Kur'an dışı konuşma

- **Oturum (İsmail, ~1 saat, gözetimsiz):** Telefondan ~30 dk Türkçe sohbet ya da vaaz ve ~30 dk Arapça hutbe ya da ders çalınır.
  - Uygulama: `scripts/live.py`, tiny.
  - Kulaklık bağlı ama takılı değil; meal hoparlöre gidip mikrofona geri girmesin.
  - Bilgisayardan ses çalınmaz.
- **Değerlendirme:** Çalınan her meal, kaydın o anı dinlenip kontrol edilir. Hutbede gerçekten okunan bir ayetin meali doğru sayılır. Geri kalanı yanlıştır.
- **Kapı:** Saatte ≤ 1 yanlış meal.

## 5. Kaynak kullanımı

- Kur'an dışı konuşma oturumunda `live.py` süreci 5 s arayla `ps` ile örneklenir: CPU %, RSS. RSS, sürecin RAM'de kapladığı alandır. Yeni bağımlılık yok.
- **RTF** = pencere başına ASR süresi ÷ adım (1 s). Canlı zincir her adımda 12 s'lik pencereyi işler; yük budur.
- **Kapı:** RTF ≤ 0.3, RAM ≤ 1.5 GB.

## GO/NO-GO

GO için hepsi gerekir (yeni kör set, tiny):

| Kapı | Eşik |
|---|---|
| Yanlış meal, clean | ≤ %0.5; üçler kuralı üst sınırı ayrıca yazılır |
| Yanlış meal, hard | ≤ %1 |
| Recall clean / noisy / hard | ≥ 95 / 75 / 85 |
| 30 s duraklamada meal | 0 |
| Kur'an dışı konuşma | ≤ 1 yanlış / saat |
| Kaynak | RTF ≤ 0.3, RAM ≤ 1.5 GB |
| Gecikme (M4'ten, kulaklık dahil) | p50 ≤ 1.5 s, p90 ≤ 3 s (meal başlangıcı − birim sonu) |

Okuyucu çeşitliliği kapısı ölçülür ve raporlanır, ama tek başına NO-GO sebebi değildir. Mücevvedde **susma** kabul edilebilir. Mücevvedde **yanlış meal** ise yanlış meal kapısına dahildir.

Örneklem sınırda kalırsa (M4'teki gibi), rapor "ayırt edilemiyor" der. Karar İsmail'indir.

## Bileşenler

| Bileşen | Değişiklik |
|---|---|
| `src/tilavet/engine/tracker.py` | Kurallar ve `EngineConfig` parametreleri (TDD) |
| `scripts/build_streams.py` | `--set blind2`: yeni okuyucular, seed, 30 s duraklama |
| `scripts/asr_windows.py` | `blind2` seti |
| `scripts/replay_m3.py` | Ayar raporu (üç setin hepsi) ve `blind2` raporu; 30 s duraklama metriği |
| `src/tilavet/eval` | Duraklama metriği (TDD) |
| `scripts/sample_process.py` | `ps` ile CPU ve RSS örnekleme |
| `reports/m5-*.md` | Sonuçlar ve karar raporu |

## Çalıştırma sırası

1. Kör set akışlarının üretimi ve ASR (arka planda, ~1 saat). Sonuçlara bakılmaz.
2. Motor kuralları, ayar verisi üzerinde, TDD ile. Her kuralın etkisi raporlanır.
3. Dondurma (onay) → kör seti açma (onay).
4. Kur'an dışı konuşma oturumu ve kaynak ölçümü (İsmail; 1–3'ten bağımsız, istenen zaman).
5. M5 raporu ve GO/NO-GO önerisi → İsmail kararı.
