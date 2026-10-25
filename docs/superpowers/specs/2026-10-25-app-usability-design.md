# iOS App Kullanılabilirlik Tasarımı

Tarih: 2026-10-25 · Onay: İsmail (bölüm 1 ve 2) · Önceki: [M6 raporu](../../../reports/m6-feasibility.md)

## Amaç

M6 app'i ölçüm için yazıldı: tek meal gösteren bir ekran ve Başlat düğmesi. İsmail app'i günlük kullanmak istiyor. Bu iş onu kullanılabilir yapar:

1. Duyulan meal'ler alt alta bir akışta; akış kalıcı, geçmişi okunabilir.
2. Ayet başlıkları sure adıyla: "Ahzâb Sûresi, 40. âyet".
3. Ses düğmesi: kulaklık ve hoparlör için tek kontrol; Kur'an okunan ortamda hoparlör kendiliğinden çalmaz.
4. Yazı boyutu düğmeleri, ekran açık kalsın düğmesi, kilit ekranında meal, uygun simge, daha büyük Başlat/Durdur.

Motor, tanıma ve meal sesi (Piper Eren) değişmez.

## Kapsam dışı

Arapça ayet metni, Beklet düğmesi, ayarlar ekranı (seyrek değişen tercih üçü geçince yeniden değerlendirilir), App Store, Android.

## Mimari

| Birim | Katman | Görev |
|---|---|---|
| `SuraNames` | `TilavetCore` | 114 sure adı, Diyanet yazımı |
| `mealTitle(_:)` | `TilavetCore` | Birim başlığı |
| `Feed`, `FeedEntry` | `TilavetCore` | `Codable` akış modeli |
| `FeedStore` | App | Aktif akış ve geçmiş; `Documents/feeds/` dosyaları |
| `AudioRoute` | App | Ses açık/kapalı, kulaklık algılama, hoparlöre yönlendirme |
| `NowPlaying` | App | Kilit ekranı bilgisi ve oynat/duraklat |
| `Pipeline` | App | Başlayan her meal'i `FeedStore`'a ekler; `replay(unit)`; sesi çalışırken açıp kapatır |
| `ContentView`, `HistoryView`, `FeedView` | App | Ekranlar |

`TilavetCore` saf kalır: dosya ve ses yok.

### Sure adları ve başlık

- Kaynak: Diyanet İşleri Başkanlığı, *Kur'an-ı Kerim Meali* PDF'i (`webdosya.diyanet.gov.tr/kuran/kuranikerim/dosyalar/document/kuran_meal.pdf`), sure başlıkları. Başlıklar büyük harfli; Türkçe kurallarıyla kelime başı büyük harfe çevrilir: "ÂL-İ İMRÂN" → "Âl-i İmrân", "MÜ’MİNÛN" → "Mü’minûn", "TÂ HÂ" → "Tâ Hâ". Kesme işareti PDF'teki gibi (’).
- Başlık: tek ayet "Ahzâb Sûresi, 40. âyet"; çok ayetli birim "Yûsuf Sûresi, 11-12. âyetler".

### Akış verisi

- `FeedEntry`: `sura`, `first`, `last`, `startedAt` (Date). Meal metni saklanmaz; gösterirken `tr.diyanet.txt`'ten alınır. Kayıt hep doğrulanmış metne bağlı kalır.
- `Feed`: `id` (başlangıç zamanı), `entries`.
- Dosya: `Documents/feeds/<id>.json`, her yeni kayıtta atomik yeniden yazılır. Aktif akışın adı `Documents/feeds/active.txt`'te.
- Akışa yalnız başlayan meal'ler (`MealPlayer` `Started`) girer; atlananlar (`Skipped`) girmez. Ses kapalıyken de girer.
- **Yeni akış:** Aktif akış boş değilse geçmişte kalır, boş yeni akış aktif olur.
- **Silme:** Geçmişte sola kaydırarak; aktif akış silinirse boş yeni akış açılır.
- Ölçüm modu (`--autostart`) akışa yazmaz; ölçüm log'ları (`RunLog`) değişmez.

## Ses düğmesi

Tek kontrol: ses açık / kapalı.

| | Açık | Kapalı |
|---|---|---|
| Kulaklık bağlı | Kulaklıktan çalar | Çalmaz |
| Kulaklık yok | **Hoparlörden** çalar | Çalmaz |

- Kulaklık: çıkış rotasında Bluetooth A2DP/HFP/LE, kablolu kulaklık ya da AirPlay dışı bir kulaklık portu.
- Kulaklıksız açıkken çıkış hoparlöre zorlanır (`overrideOutputAudioPort(.speaker)`); bugünkü ahize davranışı kalkar.
- **Varsayılan:** App kulaklık bağlıyken açılırsa açık, değilse kapalı.
- **Kulaklık çıkarsa** (rota değişimi, `oldDeviceUnavailable`) ses kapanır. Hoparlöre yalnız kullanıcı açınca geçilir.
- **Kulaklık bağlanırsa** (`newDeviceAvailable`) ses açılır (İsmail, cihaz denemesi).
- Durum satırının altında sesin nereye gittiği yazar: "Kulaklık: <ad>", "Telefon hoparlörü" ya da "Ses kapalı".
- Ses açma/kapama ve rota değişimleri çalışma log'una (`live.jsonl`: `Start`, `Sound`, `Route`) yazılır; `Playback` yalnız ses gerçekten çaldıysa.
- **Kapatınca** çalan meal hemen durur.
- **Açınca** son meal hâlâ çalıyorsa ya da biteli 30 s'den az olduysa baştan çalar; değilse sonraki meal beklenir.
- Ses kapalıyken karta dokunmak çalmaz; ses düğmesi kısa vurgulanır.
- `--mute` ölçüm argümanı ses kapalı demektir.

## Ekran

Yukarıdan aşağıya:

1. **Üst çubuk:** "Tilavet Meal"; sağda Geçmiş (saat), Yeni akış (+), Ses (hoparlör / üstü çizili hoparlör), yazı boyutu (A− / A+).
   - **Yazı boyutu:** A− ve A+ meal kartlarının yazısını küçültür/büyütür; Dinamik Yazı'nın üstüne çarpan olarak uygulanır (0.8×–2.0×, adım 0.15). Seçim `UserDefaults`'ta saklanır. Yaşlı kullanıcılar için.
2. **Durum satırı:** Yükleniyor · Ses bekleniyor (pencerede < 2 kelime) · Okuma duyuluyor · âyet aranıyor · Takip ediliyor · <Sure> Sûresi · Takip kaybedildi · âyet aranıyor · Durduruldu. Âyet 20 s'den uzun aranırsa altta turuncu not: "Kısa ve sık geçen ifadelerde âyet hemen bulunamayabilir; okumaya devam edin." (Fatiha gibi kalıp ifadeler birden çok surede geçer; motor yanlış meal vermektense susar.)
3. **Akış:** Kartlar alt alta: başlık, meal metni, çok ayetli birimde "(… birbirine bağlı olduğu için birlikte çevrilmiştir.)" notu, saat (SS:dd). Son meal ya da dokunulan meal vurgulu. Yazı iOS Dinamik Yazı'ya uyar.
   - Yeni kart gelince akış her zaman en alta kayar (İsmail: kullanıcı kaydırmak zorunda kalmasın).
   - Karta dokununca o meal baştan çalar (ses açıksa) ve vurgu o karta geçer; yeni meal gelince vurgu son karta döner.
   - Boş akışta: "Başlat'a basın; duyulan âyetlerin meali burada listelenir."
4. **Ekran açık kalsın:** Güneş simgesi + "Ekran açık kalsın" yazılı anahtar. Yalnız dinlerken etkili (`isIdleTimerDisabled`); Durdur'da normal kilitlenme. Seçim `UserDefaults`'ta saklanır; varsayılan kapalı (ekran pili dinlemeden çok harcar).
5. **Başlat / Durdur:** Ekran genişliğinde, ~64 pt. Başlat yeşil, Durdur kırmızı.

**Geçmiş (sheet):** Akışlar yeniden eskiye: "25 Eki 14:20 · Yûsuf → Bakara · 23 meal". Dokununca salt okunur akış; kartlara dokununca meal çalar. Sola kaydırarak silme.

**Kilit ekranı:** `MPNowPlayingInfoCenter`: başlık = ayet başlığı, alt satır "Tilavet Meal". Oynat/duraklat = Başlat/Durdur (`MPRemoteCommandCenter`). Bilinmeyen: iOS bilgiyi genelde yalnız ses çalarken gösterir; ses kapalıyken görünmeyebilir. Cihazda denenip raporlanır.

## Simge

Açık kitap ve üzerinden yükselen ses dalgaları; koyu yeşil zemin, krem/altın çizgi. Swift (CoreGraphics) ile 1024×1024 çizilir; 2-3 taslak masaüstüne konur, İsmail seçer. Seçilen `Assets.xcassets/AppIcon` olarak eklenir (`project.yml`).

## Test

- **TDD (`swift test`):** `SuraNames` 114 kayıt, 1 → "Fâtiha", 3 → "Âl-i İmrân", 23 → "Mü’minûn", 33 → "Ahzâb", 114 → "Nâs"; `mealTitle` tek ve çok ayetli; `Feed` JSON gidiş-dönüş eşitliği.
- **Cihazda elle (İsmail + Claude):** akış kayması ve "Yeni meal ↓"; app kapanıp açılınca akış; Yeni akış, geçmiş, silme; ses düğmesinin tablo davranışı (kulaklıklı/kulaklıksız, kulaklık çıkarma, 30 s kuralı); ekran açık kalsın; yazı boyutu (uygulama kapanıp açılınca korunur); kilit ekranı; simge.
- Golden testler ve ölçüm modları (`--autostart`, `--asr-parity`, `--tts-sample`) çalışmaya devam eder.
