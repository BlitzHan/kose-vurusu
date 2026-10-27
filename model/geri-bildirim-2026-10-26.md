# Geri bildirim · 26 Ekim 2026

5 lig maçı (Süper Lig, LaLiga, Ligue 1). Tahminler maçtan önce neyse öyle kaldı. Toplam örnek 89 maç.

Not: sonuçlar maç sayfalarından okundu; oyuncu reytingleri yok (`r: null`). Karne ve değerlendirme etkilenmiyor.

## Sonuçlar

(G) = Güçlü. "kazanır (iade)" beraberlikte iade pazarı.

| Maç | Skor | Öneriler |
|---|---|---|
| Galatasaray – Fenerbahçe | 2–1 | KG var ✓ (G) · Galatasaray kazanır (iade) ✓ · Korner 9,5 alt ✗ |
| Beşiktaş – Başakşehir | 2–0 | 2,5 üst ✗ (G) · İlk gol Beşiktaş ✓ (G) · Başakşehir +1,5 ✗ |
| Çaykur Rizespor – Trabzonspor | 3–4 | Trabzonspor kazanır (iade) ✓ (G) · 3,5 alt ✗ · KG var ✓ |
| Sevilla – Osasuna | 2–0 | 1,5 üst ✓ (G) · Sevilla kazanır (iade) ✓ (G) · Kart 5,5 alt ✓ |
| Paris Saint-Germain – Lyon | 2–0 | 2,5 üst ✗ (G) · İlk gol PSG ✓ (G) · Kart 3,5 alt ✗ |

## Karne

- **26 Ekim 9/15**; piyasanın beklentisi 9,3. Toplam 89 maçta 142/237 (piyasa 141,7).
- **Güçlü 6/8** (piyasa 5,4) · **Orta 3/7** (piyasa 3,9). Güçlü dördüncü gün de piyasanın üstünde; Orta yine geride.
- Skor (1. sıradaki) 0/5.

## Ne oldu

1. **Genel tablo piyasayla başa baş.** 96 pazarda Brier: v5 0,221 · piyasa 0,223. İlk gol (0,175 · 0,183) ve kart (0,234 · 0,242) önde, maç sonucu ve toplam gol eşit.
2. **Korner yine geride.** Korner Brier 0,254 · piyasa 0,248; beşinci günde de en zayıf grup. Tek korner önerisi (Galatasaray maçı 9,5 alt) 14 kornerle tutmadı.
3. **Favorinin 2–0'ı "2,5 üst"ü bozdu.** Beşiktaş ve PSG maçında model toplam 3,4–3,5 gol bekledi (ev sahibi tek başına 2,4–2,5), ikisi de 2–0 bitti. PSG'de xG 0,96'da kaldı; Beşiktaş'ta 1,94 ama rakip hiç üretmedi (0,43).
4. **Rizespor 3–4 sürpriz.** İlk yarı 2–0 Rizespor; Trabzonspor ikinci yarıda 4 gol attı. Taraf (Trabzonspor iade) doğru, 3,5 alt doğal olarak gitti.
5. **Derbide kart patladı.** Galatasaray – Fenerbahçe 11 kart; bu maçta kart önerisi yoktu.
6. **Kadroların hepsi muhtemel 11'di**; kesin 11 güncellemesi yapılmadı.

## Değişenler: model v6

89 maçlık örnekle üç değişiklik. Biten maçların tahminleri değişmedi; v6 bundan sonraki maçlarda kullanılacak.

1. **Orta için piyasa en az %55.** v5 ile 89 maç baştan hesaplandığında Orta 77/138 (%56) tuttu, piyasanın beklentisi 77,6'ydı; yani piyasadan bir farkı yoktu. Piyasa %55'in altındayken Orta 27/58 tuttu, üstündeyken 50/80. Eşikle Orta 61/97 (%63; piyasa 57,2). Güçlü değişmedi (84/105, %80).
2. **Korner olasılığının %75'i piyasadan.** Kartta işe yaramıştı. Korner Brier 0,249'dan 0,247'ye iniyor; küçük ama doğru yönde.
3. **Öne çıkan skor en olası sonucun içinden.** Model en olası tek skor olarak 89 maçın 63'ünde 1-1 verdi; gerçekte yalnız 6 maç 1-1 bitti. Artık önce en olası sonuç (ev / beraberlik / deplasman), sonra onun en olası skoru seçiliyor. 89 maçta 1. skor isabeti 11'den 13'e çıkıyor ve skor, sinyallerle aynı yöne bakıyor. Uyarı: tek skor tutturmanın tavanı %10–12; buradan büyük sıçrama beklenmemeli.

Toplam (89 maç, v5 → v6): öneri 161/243 (%66) → 145/202 (%72); Brier 0,2318 → 0,2316.

Not: eşikler aynı veriden seçildi; gerçek sınav sonraki günler. %58 eşiği %57'ye düşürüyor, yani sonuç gürültülü; 30 maç sonra yeniden bakılacak.
