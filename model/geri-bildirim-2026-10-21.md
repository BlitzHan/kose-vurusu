# Geri bildirim · 21 Ekim 2026

Şampiyonlar Ligi 3. hafta, 5 maç. Tahminler maçtan önce neyse öyle kaldı; bu not ne tuttu, ne kaçtı ve modelde neyi değiştirdiğimizi anlatıyor.

> 5 maç çok az. Buradaki sayılar yön gösterir, kanıt değildir. Ayarların çoğu bu 5 maça değil, takımların son 10 maçlık geçmişine (~95 maç) dayanıyor.

## Sonuçlar

| Maç | Skor (İY) | Beklenen gol | Gerçek xG | Öneriler |
|---|---|---|---|---|
| Lille – Galatasaray | 2–4 (2–2) | 1,46 – 1,36 | 2,07 – 1,39 | GS kaybetmez ✓ · 3,5 alt ✗ · Korner 9,5 alt ✓ |
| Como – Manchester United | 4–1 (1–0) | 1,57 – 1,34 | 2,11 – 0,99 | Como kaybetmez ✓ · 3,5 alt ✗ · Kart 3,5 üst ✓ |
| Bayern – Arsenal | 2–2 (1–1) | 1,65 – 1,28 | 2,46 – 1,69 | Bayern kaybetmez ✓ · 3,5 alt ✗ · Korner 9,5 üst ✗ |
| Inter – Shakhtar | 1–0 (0–0) | 2,19 – 1,23 | 1,05 – 0,60 | 4,5 alt ✓ · KG var ✗ · Korner 9,5 alt ✓ |
| Real Madrid – Leipzig | 4–1 (1–0) | 2,65 – 1,19 | 3,09 – 1,49 | Korner 9,5 üst ✗ · Leipzig +2 ✗ · KG var ✓ |

## Karne

- **Öneriler 8/15.** Modelin kendi olasılıklarına göre beklenen ~9,8 idi; biraz altında.
- Güçlü 4/7 (beklenen 4,7) · Orta 4/8 (beklenen 5,1).
- Gruplara göre: maç sonucu 3/4, toplam gol **1/4**, korner 2/4, karşılıklı gol 1/2, kart 1/1.
- İlk sıradaki skor 0/5. Normal: o skorların olasılığı %10–13, 5 maçta beklenen ~0,5.

## İyi giden

- **"Kaybetmez" sinyalleri 3/3** (Bayern, Como, Galatasaray).
- **Beklenen gol toplamı gerçeğe yakın:** 5 maçta 15,9 bekledik, xG 16,9 çıktı. 21 gol atıldı; aradaki fark bitiricilik (Como 2,1 xG'den 4 gol, Galatasaray 1,4 xG'den 4 gol).

## Eksikler

1. **3,5 alt üç kez yattı.** Büyük kısmı şans (21 gol / 16,9 xG). Ama yön de var: takım verisinden gelen beklenen gol xG'nin takım başına 0,18 altında kaldı, piyasanınki neredeyse tam isabetti (+0,03). Bu takımların son Şampiyonlar Ligi maçları da ortalama 4,1 gollü (17 maç), lig maçları 3,3.
2. **Korner fazla tahmin edildi.** 50 bekledik, 36 oldu; 5 maçın 4'ünde fazla. Geçmiş veride (~95 maç) bir takımın kendi korner ortalaması, genel ortalamadan (9,7) daha iyi tahmin etmiyor. Korner sayısı Poisson'un varsaydığından daha dağınık (varyans / ortalama ≈ 1,7). Yani model kornerde fazla iddialıydı.
3. **Kartta da aynı durum.** Geçmiş veride takım ortalaması, genel ortalamadan (3,8) daha kötü tahmin ediyor. Bu 5 maçta kart tahminleri tuttu; bu şanstı.
4. **Model piyasadan çok ayrıştığında kaybettik.** Leipzig +2: model %65, piyasa %48 dedi; Madrid 3 farkla kazandı. Madrid için piyasanın beklenen golü 3,15'ti, xG 3,09 çıktı. Bizim takım verimiz 2,23'te kalmıştı.
5. **Muhtemel 11.** 22:00 maçlarının 11'i kesinleşmeden yayında kaldı. Bayern'de ve Madrid'de 11'in 4'ü değişti (7/11 isabet).
6. **Verisi olmayan oyuncu.** Lille'de Diaoune'ye takım ortalaması verildi; 2 golle maçın adamı oldu (8,2).
7. **Puan formülü.** 96 pazarın tamamında en isabetli bileşen "son 10" çıktı (Brier 0,208). Model 0,239, piyasa 0,239. Puan modele %60 ağırlık veriyor. 5 maçla bunu değiştirmek erken; izliyoruz.

## Değişenler (model v2)

Kod: `model/model.py`. v1, 21 Ekim'de kullanılan model; kayıtlı tahminleri birebir üretiyor.

| | v1 | v2 | Neden |
|---|---|---|---|
| Beklenen gol harmanı | takım verisi %50, piyasa %50 | takım verisi %40, piyasa %60 | Piyasa xG'ye daha yakın, sapması yok (madde 1, 4) |
| Korner beklentisi | takım ortalamaları | genel ortalamaya (9,7) %65 çekilir | Takım ortalaması zayıf bilgi (madde 2) |
| Korner dağılımı | Poisson | negatif binom (r = 14) | Gerçek dağılım daha geniş |
| Kart beklentisi | takım ortalamaları | genel ortalamaya (3,8) %75 çekilir | Madde 3 |
| Korner / kart sinyali | Güçlü olabilir | en fazla Orta | Piyasa çoğu zaman sabit 1.83 / 1.83, bilgi taşımıyor |

Aynı 5 maçta v1 ile v2 (`python3 model/karsilastir.py`):

| | v1 | v2 |
|---|---|---|
| Brier, tüm pazarlar (düşük = iyi) | 0,239 | 0,235 |
| Korner | 0,304 | 0,242 |
| Toplam gol | 0,290 | 0,283 |
| Kart | 0,168 | 0,209 (5 maçta kötü; geçmiş veri v2'yi destekliyor) |
| Öneri isabeti | 8/14 | 8/13 |

v2 iki kaybeden korner üst önerisini düşürüyor. 3,5 alt önerileri v2'de de kalıyor: o maçlarda veri ve piyasa aynı yönü gösteriyordu, kayıp çoğunlukla şanstı.

## Değiştirmediklerimiz

- Puan ağırlıkları (%60 model, %25 son 10, %15 piyasa): son 10 iyi göründü ama 5 maç.
- Güçlü / Orta eşikleri, ρ (−0,075), ilk yarı payı (0,48).
- Oyuncu formu çarpanı: 10 takım gözlemi bir şey söylemek için az.

## Süreç

- 22:00 maçlarında kesin 11 açıklanınca (~1 saat önce) son güncellemeyi yapmak.
- Listede verisi olmayan oyuncu 11'e girerse gerçek formunu çekmek, ortalama vermemek.
- Her sonuçtan sonra `python3 model/degerlendir.py` ve `python3 model/karsilastir.py`. 30 maç birikince puan ağırlıklarını ve eşikleri yeniden ayarlamak.
- Asıl analiz aracı iş bilgisayarında. v2 parametreleri oraya da aktarılmalı.
