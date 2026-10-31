# Geri bildirim · 30 Ekim 2026

6 lig maçı (Süper Lig, LaLiga, Ligue 1, Bundesliga), model v6. Tahminler maçtan önce neyse öyle kaldı. Toplam örnek 122 maç; bunun 33'ü v6 (27 ve 30 Ekim).

Not: sonuçlar yeniden doğrudan veri kaynağından çekildi; oyuncu reytingleri geri geldi. 27 Ekim için ayrı not yazılmamıştı, v6 bölümü onu da kapsıyor.

Bu not üç günlük serinin ilki (30 Ekim, 31 Ekim, 1 Kasım). Pazartesi üçü birlikte okunup v7 kararı verilecek; aşağıdaki "Gelişime açık yönler" o toplantının gündemi.

## Sonuçlar

(G) = Güçlü. "kazanır (iade)" beraberlikte iade pazarı.

| Maç | Skor | Öneriler |
|---|---|---|
| Konyaspor – Galatasaray | 0–4 | 3,5 alt ✗ · İlk gol Galatasaray ✓ · KG var ✗ |
| Villarreal – Espanyol | 0–1 | 2,5 üst ✗ (G) |
| Le Havre – PSG | 1–5 | 2,5 üst ✓ (G) · İlk yarı PSG ✓ |
| Nice – Rennes | 5–2 | 3,5 alt ✗ (G) · Rennes kaybetmez ✗ · KG var ✓ |
| Lille – Lens | 1–0 | Lens kaybetmez ✗ (G) |
| Elversberg – Mainz | 4–1 | KG var ✓ (G) · Kart 4,5 alt ✗ · Mainz kazanır (iade) ✗ |

## Karne

- **30 Ekim 5/13**; piyasanın beklentisi 8,1. Kötü gün.
- **Güçlü 2/5** (piyasa 3,3) · **Orta 3/8** (piyasa 4,8).
- Skor (1. sıradaki) 0/6.
- **v6 toplamı (33 maç): Güçlü 22/35** (piyasa 23,0) · **Orta 15/30** (piyasa 17,7). 26 Ekim'deki geriye dönük hesap Güçlü için %80 vermişti; gerçekte %63. Eşikler aynı veriden seçildiği için bu düşüş bekleniyordu.
- Tüm dönem (122 maç): Güçlü 97/145 (piyasa 94,1) · Orta 82/157 (piyasa 88,2).

## Ne oldu

1. **Gol bolluğu.** Maç başı 4,0 gol; model 3,1 bekledi. İki "3,5 alt" (Konya, Nice) bu yüzden gitti. Nice – Rennes'de xG 3,44–2,61; maç gerçekten açık oynandı.
2. **Deplasman tarafı üç kez yanıldı.** Rennes kaybetmez, Lens kaybetmez, Mainz kazanır (iade). Lille – Lens'te xG 1,63–0,19, Elversberg ilk yarıyı 3–0 kapattı. Üçünde de model piyasayla aynı yöndeydi; yani bu "modelin hatası" değil, piyasanın da yanıldığı maçlar.
3. **Villarreal 0–1.** Model ve piyasa 3,5 gol bekledi; maçta toplam xG 1,04. Saf şanssızlık değil ama tek maç.
4. **Kart alt yine tutmadı.** Elversberg – Mainz'da model kart 4,5 alt için %65 dedi, piyasa %58. Mainz tek başına 6 kart gördü. Modelin piyasadan en çok ayrıldığı öneri buydu ve kaybetti.

## Gelişime açık yönler (v7 gündemi)

Önce dürüst tablo: 122 maçta model **piyasayla neredeyse aynı**, biraz geride. Tüm pazarlarda Brier 0,238, piyasa 0,236. Öneri puanları ile piyasa olasılıkları arasındaki fark çoğu öneride 1–2 puan. Yani şu anki öneriler "piyasanın en olası gördüğü pazarlar" ve piyasanın biraz altında tutuyor.

### 1. Modelin işe yaradığı ve yaramadığı yerleri ayır

| Grup | Brier model · piyasa (122 maç) | v6 (33 maç) | Yorum |
|---|---|---|---|
| Maç sonucu | 0,235 · 0,235 | 0,239 · 0,245 | v6'da piyasanın önünde |
| İlk gol | 0,235 · 0,234 | 0,252 · 0,257 | v6'da önde |
| İlk yarı | 0,226 · 0,224 | 0,226 · 0,220 | geride |
| Toplam gol | 0,237 · 0,233 | 0,256 · 0,255 | geride |
| Karşılıklı gol | 0,242 · 0,237 | 0,245 · 0,239 | geride |
| Korner | 0,256 · 0,248 | 0,258 · 0,249 | en zayıf; %75 piyasa payıyla bile geride |
| Kart | 0,256 · 0,251 | 0,282 · 0,273 | geride |

**Öneri:** korner, kart, karşılıklı gol ve toplam golde olasılığı tamamen piyasadan al (model payı 0). Model katkısını yalnız maç sonucu ve ilk golde tut. Bu hem Brier'i iyileştirir hem öneri listesindeki "model piyasadan ayrıldı, kaybetti" vakalarını (Elversberg kart alt gibi) keser.

### 2. Toplam gol önerileri: iki yönde de kayıp

- 3,5 alt: 35/59 (piyasa 37,6). v6'da 9/18 (piyasa 11,5). En sık verilen öneri ve en çok kaybettiren.
- 2,5 üst: 13/23 (piyasa 15,0).
- Gol seviyesi sürekli yüksek: 8 günün 7'sinde gerçek gol beklenenin üstünde. 122 maçta maç başı 3,31 gol, model 3,04. Piyasanın beklentisi de benzer şekilde düşük.

**Öneri:** (a) Toplam gol olasılığını doğrudan piyasadan al; (b) "3,5 alt" için ek eşik ya da geçici kaldırma test et; (c) lig bazında sezon gol ortalamasıyla λ çarpanı (1,05–1,08) `karsilastir.py` ile dene. Uyarı: (c) kısa bir gol bolluğuna fazla uydurma riski taşır.

### 3. Öneri puanları fazla iyimser

| Öneri puanı | Tuttu | Ortalama puan |
|---|---|---|
| 0,50–0,55 | %48 (12/25) | 0,54 |
| 0,55–0,60 | %58 (43/74) | 0,58 |
| 0,60–0,65 | %57 (56/98) | 0,62 |
| 0,65–0,70 | %67 (50/75) | 0,67 |
| 0,70+ | %64 (18/28) | 0,72 |

0,60 üstünde gerçek isabet gösterilen puanın 4–8 puan altında. Bu, "en yükseği seç" seçiminin doğal sonucu: puanı şans eseri şişmiş pazarlar listeye giriyor.

**Öneri:** seçim puanı olarak piyasa olasılığını kullan, model yalnız eleme yapsın (model piyasadan belirgin düşükse öneriyi düşür). Sitede gösterilen yüzdeye küçük bir kalibrasyon düzeltmesi.

### 4. Orta seviyesi hâlâ değer üretmiyor

v6'daki %55 piyasa eşiğine rağmen Orta 15/30 (piyasa 17,7). Tüm dönemde 82/157 (piyasa 88,2).

**Öneri:** Orta'yı bilet önerisi olmaktan çıkarıp yalnız "veri ne diyor" bilgisi olarak göster ya da Orta için model ile piyasanın aynı yönde ve en az %60 olmasını şart koş.

### 5. Örnek büyüklüğü ve sınama yöntemi

300 öneride ±1 standart sapma yaklaşık ±9 isabet. Yukarıdaki farkların çoğu (Orta −6, toplam gol −4,6) bu bandın içinde; tek başına kesin kanıt değil. v6'daki hayal kırıklığı da eşiklerin aynı veriden seçilmesinden geldi.

**Öneri:** v7 değişikliklerini 27 Ekim öncesi maçlarla seç, 27 Ekim sonrası maçlarla sına (ayrı test seti). Kural: test setinde piyasayı geçmeyen değişiklik girmez.

### 6. Küçük hatalar

- **Önem metni lig maçlarında yanlış şablonu kullanıyor.** Süper Lig ve Eredivisie maçlarında "İlk 8'de; kazanırsa son 16'ya doğrudan çıkma yolunda öne geçer" ve "Play-off bölgesinde; galibiyet ilk 8'e yaklaştırır" yazıyor. Bu Avrupa kupası lig aşaması metni; 31 Ekim ve 1 Kasım maçlarında sitede görünüyor.
- **`degerlendir.py` korner verisi olmayan maçta çöküyordu** (27 Ekim'de 13 alt lig kupa maçı). Düzeltildi: o maçlar korner/kart sapmasından atlanıyor.
- 27 Ekim kupa maçlarının 22'sinde kadro verisi yoktu (0/0); buna rağmen öneriler 30/46 tuttu (piyasa 28,9). Bu da piyasa tabanının tek başına yeterince iyi olduğunu destekliyor.

## Pazartesi için

31 Ekim (30 maç) ve 1 Kasım (23 maç) sonuçları gelince aynı tablolar 175 maçla yeniden çıkacak. Karar verilecek sorular:

1. Korner, kart, KG ve toplam golde model payı sıfıra insin mi?
2. Öneri seçimi piyasa olasılığıyla mı yapılsın?
3. Orta öneri olarak kalsın mı?
4. Önem metni hatası v7 ile birlikte mi düzeltilsin, hemen mi?
