# M1 sonuçları (otomatik üretildi: scripts/analyze_m1.py)

Girdiler data/manifest.json'daki sha256 ile sabitlenmiştir.

## U1 — Meal süresi ve birikme

Meal: tr.diyanet, 5393 birim, ses: yelda (macOS `say`, varsayılan hız). Toplam meal süresi @1.0x: **14.89 saat**.

Oran = meal süresi ÷ tilavet süresi (birim bazında; tilavet süresi ayetler arası duraklamayı içerir).

| Okuyucu | Tilavet (saat) | Toplam oran @1.0x | Birim oranı p50 | p90 | > 1 olan birim @1.0x | @1.25x |
|---|---|---|---|---|---|---|
| abdulbaset-mujawwad | 58.58 | 0.25 | 0.26 | 0.34 | 0.0% | 0.0% |
| shuraim-murattal | 18.16 | 0.82 | 0.84 | 1.10 | 18.6% | 4.0% |
| sudais-murattal | 21.03 | 0.71 | 0.72 | 0.97 | 8.1% | 1.5% |
| husary-murattal | 42.61 | 0.35 | 0.35 | 0.48 | 0.0% | 0.0% |
| alafasy-murattal | 29.55 | 0.50 | 0.51 | 0.69 | 0.8% | 0.3% |
| minshawi-murattal | 28.80 | 0.52 | 0.53 | 0.71 | 0.7% | 0.2% |

### Birikme simülasyonu

Mealler sırayla, üst üste binmeden çalınır; her sure ayrı simüle edilir. Gecikme (lag) = meal başlangıcı − mealin çalınabilir olduğu an.

- **end:** birim tamamen okunduktan sonra çalınabilir.
- **early:** birimin ilk ayeti Track modunda tekil olduğu anda çalınabilir (U2); kelime timing'i yoksa okuyucunun Track p90 süresi varsayılır.
- **last:** birimin son ayeti tanındığında çalınabilir (okunmamış ayetin anlamı önceden duyulmaz).
- **Onset − son:** meal başlangıcı − birimin tilavet bitişi (negatif = okuyucu birimi bitirmeden meal başladı).

| Okuyucu | Politika | Hız | Lag p50 | Lag p90 | Lag max | > 15 s lag olan birim | Onset − son p50 | p90 | En kötü sureler (max lag) |
|---|---|---|---|---|---|---|---|---|---|
| abdulbaset-mujawwad | end | 1.0x | 0.0 s | 0.0 s | 25 s | 0.1% | 0.0 s | 0.0 s | 27 (25 s), 26 (21 s), 33 (20 s) |
| abdulbaset-mujawwad | end | 1.25x | 0.0 s | 0.0 s | 17 s | 0.0% | 0.0 s | 0.0 s | 27 (17 s), 20 (14 s), 26 (12 s) |
| abdulbaset-mujawwad | early | 1.0x | 0.0 s | 0.0 s | 2 s | 0.0% | -26.9 s | -8.7 s | 112 (2 s), 68 (1 s), 114 (0 s) |
| abdulbaset-mujawwad | early | 1.25x | 0.0 s | 0.0 s | 1 s | 0.0% | -26.9 s | -8.7 s | 112 (1 s), 114 (0 s), 113 (0 s) |
| abdulbaset-mujawwad | last | 1.0x | 0.0 s | 0.0 s | 28 s | 0.1% | -24.1 s | -7.7 s | 26 (28 s), 27 (24 s), 18 (19 s) |
| abdulbaset-mujawwad | last | 1.25x | 0.0 s | 0.0 s | 19 s | 0.0% | -24.1 s | -7.8 s | 26 (19 s), 27 (16 s), 18 (11 s) |
| shuraim-murattal | end | 1.0x | 2.2 s | 12.9 s | 53 s | 7.6% | 2.2 s | 12.9 s | 2 (53 s), 7 (38 s), 26 (38 s) |
| shuraim-murattal | end | 1.25x | 0.0 s | 5.4 s | 37 s | 1.6% | 0.0 s | 5.4 s | 2 (37 s), 26 (29 s), 27 (28 s) |
| shuraim-murattal | early | 1.0x | 0.0 s | 2.1 s | 14 s | 0.0% | -8.7 s | -1.8 s | 54 (14 s), 12 (12 s), 47 (11 s) |
| shuraim-murattal | early | 1.25x | 0.0 s | 0.0 s | 7 s | 0.0% | -8.9 s | -2.7 s | 68 (7 s), 7 (7 s), 12 (6 s) |
| shuraim-murattal | last | 1.0x | 0.0 s | 8.4 s | 40 s | 3.0% | -6.6 s | 2.7 s | 26 (40 s), 27 (37 s), 18 (32 s) |
| shuraim-murattal | last | 1.25x | 0.0 s | 2.4 s | 32 s | 0.5% | -7.7 s | -1.3 s | 26 (32 s), 27 (27 s), 18 (24 s) |
| sudais-murattal | end | 1.0x | 0.0 s | 8.9 s | 49 s | 3.7% | 0.0 s | 8.9 s | 2 (49 s), 7 (39 s), 26 (37 s) |
| sudais-murattal | end | 1.25x | 0.0 s | 3.5 s | 34 s | 0.9% | 0.0 s | 3.5 s | 2 (34 s), 27 (28 s), 26 (28 s) |
| sudais-murattal | early | 1.0x | 0.0 s | 0.3 s | 19 s | 0.0% | -10.3 s | -3.0 s | 5 (19 s), 12 (12 s), 68 (9 s) |
| sudais-murattal | early | 1.25x | 0.0 s | 0.0 s | 13 s | 0.0% | -10.5 s | -3.2 s | 5 (13 s), 68 (6 s), 7 (5 s) |
| sudais-murattal | last | 1.0x | 0.0 s | 4.9 s | 40 s | 1.4% | -8.7 s | -0.5 s | 26 (40 s), 27 (34 s), 18 (30 s) |
| sudais-murattal | last | 1.25x | 0.0 s | 1.0 s | 31 s | 0.3% | -9.2 s | -2.1 s | 26 (31 s), 27 (25 s), 18 (22 s) |
| husary-murattal | end | 1.0x | 0.0 s | 0.0 s | 27 s | 0.4% | 0.0 s | 0.0 s | 27 (27 s), 2 (27 s), 4 (26 s) |
| husary-murattal | end | 1.25x | 0.0 s | 0.0 s | 19 s | 0.1% | 0.0 s | 0.0 s | 27 (19 s), 20 (18 s), 4 (17 s) |
| husary-murattal | early | 1.0x | 0.0 s | 0.0 s | 5 s | 0.0% | -20.9 s | -6.8 s | 68 (5 s), 103 (3 s), 112 (2 s) |
| husary-murattal | early | 1.25x | 0.0 s | 0.0 s | 2 s | 0.0% | -20.9 s | -6.8 s | 103 (2 s), 68 (2 s), 101 (1 s) |
| husary-murattal | last | 1.0x | 0.0 s | 0.0 s | 31 s | 0.1% | -18.6 s | -6.0 s | 26 (31 s), 27 (27 s), 18 (21 s) |
| husary-murattal | last | 1.25x | 0.0 s | 0.0 s | 23 s | 0.0% | -18.7 s | -6.0 s | 26 (23 s), 27 (19 s), 18 (13 s) |
| alafasy-murattal | end | 1.0x | 0.0 s | 2.3 s | 40 s | 1.2% | 0.0 s | 2.3 s | 2 (40 s), 27 (33 s), 26 (33 s) |
| alafasy-murattal | end | 1.25x | 0.0 s | 0.0 s | 25 s | 0.3% | 0.0 s | 0.0 s | 27 (25 s), 2 (24 s), 33 (24 s) |
| alafasy-murattal | early | 1.0x | 0.0 s | 0.0 s | 8 s | 0.0% | -14.7 s | -5.0 s | 68 (8 s), 7 (5 s), 89 (4 s) |
| alafasy-murattal | early | 1.25x | 0.0 s | 0.0 s | 5 s | 0.0% | -14.7 s | -5.0 s | 68 (5 s), 112 (3 s), 103 (2 s) |
| alafasy-murattal | last | 1.0x | 0.0 s | 0.0 s | 38 s | 0.3% | -13.0 s | -4.0 s | 26 (38 s), 27 (31 s), 18 (27 s) |
| alafasy-murattal | last | 1.25x | 0.0 s | 0.0 s | 29 s | 0.1% | -13.1 s | -4.3 s | 26 (29 s), 27 (23 s), 18 (19 s) |
| minshawi-murattal | end | 1.0x | 0.0 s | 2.9 s | 35 s | 1.2% | 0.0 s | 2.9 s | 2 (35 s), 27 (34 s), 26 (34 s) |
| minshawi-murattal | end | 1.25x | 0.0 s | 0.0 s | 26 s | 0.4% | 0.0 s | 0.0 s | 27 (26 s), 2 (25 s), 26 (25 s) |
| minshawi-murattal | early | 1.0x | 0.0 s | 0.0 s | 8 s | 0.0% | -13.5 s | -4.1 s | 68 (8 s), 7 (6 s), 85 (3 s) |
| minshawi-murattal | early | 1.25x | 0.0 s | 0.0 s | 5 s | 0.0% | -13.5 s | -4.1 s | 68 (5 s), 7 (2 s), 103 (2 s) |
| minshawi-murattal | last | 1.0x | 0.0 s | 0.0 s | 39 s | 0.4% | -11.9 s | -3.2 s | 26 (39 s), 27 (34 s), 18 (26 s) |
| minshawi-murattal | last | 1.25x | 0.0 s | 0.0 s | 30 s | 0.2% | -12.1 s | -3.5 s | 26 (30 s), 27 (26 s), 18 (19 s) |

## U2 — Tekil tanıma için gereken kelime sayısı

- **Global (Acquire):** konum bilinmiyor; ayetin ilk k kelimesi Kur'an'ın tamamında tek geçmeli.
- **Track:** önceki ayet biliniyor; rakipler ±3 ayet ve önceki ayetin herhangi bir kelimesinden yeniden başlama.

| Mod | Çözülen | p50 | p90 | p99 | ≤ 1 kelime | ≤ 3 kelime | Ayet dışına taşan | Çözülemeyen |
|---|---|---|---|---|---|---|---|---|
| Global | 6235/6236 | 3 | 6 | 13 | 10.0% | 68.7% | 5.6% | 1 |
| Track | 6122/6122 | 1 | 2 | 5 | 74.4% | 96.4% | 0.7% | 0 |

Saniye karşılığı (ilk kelimenin başından k. kelimenin sonuna; kelime timing'i eşleşen ayetler):

| Okuyucu | Kapsam | Track p50 | Track p90 | Global p50 | Global p90 |
|---|---|---|---|---|---|
| abdulbaset-mujawwad | 5285/6236 | 1.9 s | 4.2 s | 4.7 s | 10.3 s |
| shuraim-murattal | 5859/6236 | 0.8 s | 1.6 s | 1.8 s | 3.8 s |
| sudais-murattal | 5253/6236 | 1.0 s | 1.9 s | 2.2 s | 4.5 s |
| husary-murattal | 5498/6236 | 2.2 s | 4.1 s | 4.4 s | 9.0 s |
| alafasy-murattal | 4882/6236 | 1.3 s | 2.8 s | 2.9 s | 6.3 s |
| minshawi-murattal | 5375/6236 | 1.7 s | 3.1 s | 3.3 s | 6.4 s |

Global modda en zor ayetler: 70:29 (k=29), 23:5 (k=29), 70:30 (k=25), 23:6 (k=25), 2:122 (k=24).
Global modda 40 kelimede çözülemeyen: 1 ayet (örnek: 114:6).

## U3 — Metni birebir aynı ayetler

Normalize Arapça metni aynı olan **98 grup**, toplam **280 ayet**.

| Meal | Meali de aynı grup | Farklı grup |
|---|---|---|
| tr.diyanet | 8 | 90 |
| tr.vakfi | 7 | 91 |

tr.diyanet için mealleri farklı olan gruplar (ilk 10):

- 2:5, 31:5
- 2:47, 2:122
- 2:162, 3:88
- 3:89, 24:5
- 3:182, 8:51
- 5:10, 5:86
- 6:4, 36:46
- 6:10, 21:41
- 6:15, 39:13
- 7:107, 26:32
