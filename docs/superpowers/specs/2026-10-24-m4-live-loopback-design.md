# M4 — Canlı Zincir ve Loopback Tasarımı

Tarih: 2026-10-24 · Onay: İsmail (yaklaşım A, tam set) · Plan: M4 + Bölüm 6

## Amaç

1. Canlı zincirin uçtan uca gecikmesini ölçmek: mikrofon → ASR → motor → meal sesi (AirPods).
2. Simüle gürültü yerine gerçek akustik yolda (hoparlör → oda → mikrofon) doğruluğu ölçmek.
3. M3'ün benzer ayet hatalarını düzeltmek ve düzeltmeyi hiç bakılmamış bir kör sette sınamak.

## Kullanım ve donanım

- **Tilavet kaynağı:** hoparlör, TV ya da canlı okuyucu. Yalnız mikrofon kullanılır; başka uygulamanın sesi yakalanmaz.
- **Meal çıkışı:** Bluetooth kulaklık (AirPods).
- **Loopback düzeni:** MacBook hoparlörü → MacBook mikrofonu. Hoparlör ve mikrofon aynı kasada; oda yankısı az, bu yüzden TV'den kolay bir koşul.
- **Giriş cihazı adıyla sabitlenir:** `MacBook Pro Mikrofonu`. Neden: AirPods mikrofonu açılırsa kulaklık HFP profiline düşer ve meal sesi bozulur.

## Yaklaşım A: kaydet, iki modelle oynat; canlıyı aynı oturumda ölç

Her akış hoparlörden bir kez çalınır. Aynı sırada:

- Mikrofon sesi wav dosyasına yazılır (inceleme için; revizyon sonrası iki modelle yeniden oynatma yapılmıyor, bkz. Setler).
- Mikrofon sesi canlı boru hattına da girer: tiny → `PositionEngine` → `EmissionPolicy` → `MealPlayer`. Her karar zaman damgasıyla loglanır.
- NVIDIA'nın gecikmesi, M3'teki gibi ölçülen işlem süresiyle replay'den hesaplanır. Canlıda yalnız tiny çalışır, çünkü CPU'yu kayıtla paylaşmaz.
- Gözetimsiz oturumda meal sesi sessiz çıkışa gider; hoparlöre gitseydi mikrofona geri girerdi. Çalma anı aynı kuyruk kurallarıyla hesaplanır. AirPods çıkış gecikmesi ayrıca tık testiyle ölçülüp eklenir.

**Zaman hizalama.** Kayıt, referans wav ile cross-correlation yöntemiyle karşılaştırılır; bulunan ofset hoparlör → mikrofon gecikmesidir. Ground truth zamanları bu ofset kadar kaydırılır.

## Setler

**Revizyon (smoke sonrası, İsmail onayı):** Smoke'ta (`shuraim-2`) oda kaydının CER'i clean ile aynı çıktı (%0,10), SNR 29 dB. MacBook hoparlöründen aynı kasadaki mikrofona giden yol akustik zorluk eklemiyor. Bu yüzden:

| Set | Sesli süre | Kullanım |
|---|---|---|
| Canlı oturum: eski testten 8 akış | ~33 dk | Yalnız canlı zincirin gecikmesi ve kararlılığı |
| Dev + eski test | 0 | Düzeltmenin ayarı, mevcut simüle önbellekle (hard ağırlıklı) |
| Yeni kör set: 4 okuyucu | 0 | Dondurulmuş kuralların tek sınavı; bilgisayarda clean / noisy / hard |

Canlı oturumda çalınan akışlar: `abdulbaset-mujawwad-1`, `abdulbaset-mujawwad-4`, `hani-rifai-3`, `hani-rifai-4`, `minshawi-0`, `minshawi-1`, `sudais-0`, `sudais-4`.

Oturum sırasında bilgisayar hafifçe kullanılabilir. Yasak olanlar: ses çalan uygulamalar (Rahatsız Etmeyin açık), mikrofon kullanan uygulamalar, ağır CPU işi.

**Kör set:**
- Aday okuyucular: Alafasy, Maher al-Muaiqly, Muhammad Ayyoub, Minshawi Mücevved. Erişilebilirlik kurulumda kontrol edilir.
- Pasajlar yeni bir seed ile seçilir.
- Kurallar dondurulana kadar kör setin ASR metnine, akış bazlı sonuçlarına ve `--debug` çıktısına bakılmaz. Set yalnız İsmail'in onayıyla açılır.
- Leakage: NVIDIA bu okuyucuları muhtemelen gördü. Raporda yazılır.

## Bileşenler

| Bileşen | Görev | Bağımlılık |
|---|---|---|
| `AudioSource` | Mikrofondan 16 kHz mono parçalar; taşma sayacı | `sounddevice` |
| `Recognizer` | Mevcut | ONNX / NeMo |
| `PositionEngine`, `EmissionPolicy` | Mevcut, saf; saat dışarıdan verilir | Yok |
| `MealPlayer` | Kuyruk ve çalma zamanlaması; sink dışarıdan verilir | Yok (saf) |
| `MealStore` | Birim → önceden üretilmiş ses dosyası | `say` → AAC |
| Live session | Yukarıdakileri bağlar; en güncel pencereyi işler | Yok (saf, test edilebilir) |

Meal sesleri tek seferlik üretilir: 5.393 birim, Yelda, ~20 dk, ~200 MB. Dosyalar `data/derived` altında kalır, git'e girmez.

## Kuyruk politikası

- Meal'ler sırayla çalar, üst üste binmez, cümle ortasında kesilmez (M1, R3).
- 15 s'den uzun bekleyen bir meal, arkasında daha yeni bir meal varsa atlanır ve loglanır. 15 s, Bölüm 6'daki birikme eşiği.
- 1,25x hız M4'te yok. Birikme ölçümü gerektirirse eklenir.

## Benzer ayet düzeltmesi

Hedeflenen iki hata türü:

- **(a)** Acquire modunda ayırt edici kelimesi bozulan benzer pasaj (M3: 37:169 → 37:40).
- **(b)** Pencere kenarındaki bozuk kelimeyle sıradaki ayetin erken onayı (M3: 71:13).

Aday çözümler:

- (a) için: tartışmalı kelime kuralını (`track_margin`) Acquire'a da uygulamak.
- (b) için: açılış kelimelerinin art arda iki pencerede görülmesini istemek. Maliyeti her onaya ~1 s gecikme.

Seçim, dev ve eski test setinin simüle verisiyle yapılır. Her kural TDD ile eklenir. Gecikme maliyeti raporlanır.

## Hata durumları

- Cihaz adıyla bulunamazsa program net bir mesajla durur; başka cihaza geçmez.
- Mikrofon tamponu taşarsa kayıp örnekler sayılır ve loglanır.
- ASR gerçek zamandan yavaşsa bekleyen pencereler atlanır, en güncel pencere işlenir. Atlananlar loglanır.
- Kayıt yarıda kalırsa biten akışlar atlanır (`asr_windows.py` kalıbı).

## Test

TDD ile yazılacak saf parçalar:

- `MealPlayer`: sahte saat, sahte sink.
- Ofset hesabı: yapay olarak geciktirilmiş sinyal.
- Live session: sahte kaynak ve sahte ASR.

`sounddevice` adapter'ları ince kalır ve cihazda elle doğrulanır.

## Çalıştırma sırası

1. **Smoke run (~3,5 dk):** tek bir dev akışı (`shuraim-2`, 192 s). Ortamı, mikrofon iznini, ses seviyesini ve hizalamayı doğrular. Tam oturumdan önce İsmail'e sonuç sunulur.
2. Canlı oturum: eski testten 8 akış, ~33 dk. Kaldığı yerden devam eder.
3. Tık testi: AirPods çıkış gecikmesi (manuel, ~2 dk).
4. Düzeltme, dev ve eski test üzerinde. Kör set kurulur, ASR geçişleri sırayla yapılır, sonuçlara bakılmaz.
5. Kuralları dondurma (onay) → kör seti açma (onay).
6. Canlı deneme: İsmail, gerçek kaynakla (~30 dk).
7. M4 raporu.

## Kabul (Bölüm 6)

- **Gecikme**, AirPods dahil: meal başlangıcı − birim sonu p50 ≤ 1,5 s, p90 ≤ 3 s.
- **Birikme:** 15 s'yi aşan bekleme yok.
- **Canlı oturum:** yanlış ≤ %1, recall ≥ %85. Not: oda koşulu clean'e eşdeğer.
- **Kör set:** Bölüm 6 koşul eşikleri (clean = stüdyo, hard = telefon/canlı); ayrıca üçler kuralıyla üst sınır.

## Kapsam dışı

- 1,25x hız.
- Konu bağı seçenekleri (anons, hızlandırılmış önceki meal).
- Tam sure kayıtları (`mfa-quran-hafs`): M5'e kaldı.
- Kur'an dışı konuşma testi.
