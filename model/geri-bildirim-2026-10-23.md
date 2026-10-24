# Geri bildirim · 23 Ekim 2026

9 lig maçı (Süper Lig, 1. Lig, Premier League, LaLiga 2, Serie B, Ligue 1, Bundesliga, Eredivisie, Portekiz). Tahminler maçtan önce neyse öyle kaldı. Toplam örnek 33 maç ve 617 pazar.

## Sonuçlar

| Maç | Skor | Öneriler |
|---|---|---|
| Alanyaspor – Kocaelispor | 1–2 | Beraberlik olmaz ✓ · 1,5 üst ✓ |
| Boluspor – Vanspor | 0–3 | 3,5 alt ✓ |
| Ipswich – Nottingham Forest | 1–1 | 3,5 alt ✓ · Korner 9,5 alt ✓ · KG var ✓ |
| Alavés – Málaga | 1–1 | 2,5 alt ✓ |
| Brest – Nice | 1–2 | Brest kaybetmez ✗ · 3,5 alt ✓ · KG var ✓ |
| Stuttgart – Gladbach | 2–3 | 4,5 alt ✗ · Gladbach +1,75 ✓ · KG var ✓ |
| Go Ahead Eagles – Telstar | 3–2 | 4,5 alt ✗ · KG var ✓ |
| Torino – Monza | 3–2 | 3,5 alt ✗ · KG var ✓ · Monza kaybetmez ✗ |
| Vitória – Marítimo | 5–0 | Marítimo +1 ✗ |

## Karne

- **23 Ekim 13/19.** Toplam 33 maçta 44/79 (v3 ile yeniden hesap); piyasanın beklentisi 46,5.
- Güçlü 21/43, Orta 25/41 (kayıtlı tahminler). **Üç gündür Güçlü, Orta'dan iyi değil.**
- 1. Lig maçında xG yok; `degerlendir.py` artık xG'siz maçı beklenen gol karşılaştırmasında atlıyor.

## Ne oldu

1. **Piyasa payı arttıkça iyileşme sürüyor.** 33 maçta Brier: payı %80 0,2335 · %90 0,2326 · %100 0,2319. Üç değerlendirmede de aynı yön. Takım verisinin beklenen gole kattığı bir şey görünmüyor.
2. **Güçlü "değer" arıyordu, değer yoktu.** Eski Güçlü, modelin piyasadan biraz yukarıda olduğu seçenekleri seçiyordu. Model piyasayı geçemediği için bu farklar gürültüydü; Güçlü önerilerin isabeti piyasanın beklentisinin altında kaldı (19/35, piyasa 22,2).
3. **Son 10 eşiği isabeti öngörmedi.** Adaylarda son 10 sıklığına göre isabet tek yönlü artmıyor; bileşen olarak Brier'i en kötü olan o (0,249). Eşik bazı iyi adayları eliyordu.
4. **Korner ve kart lig ortalamaları kaymış.** 33 maçta korner ortalaması 8,9 (model 9,7'ye çekiyordu, beklenen fazlası +0,9), kart 4,3 (3,8'e çekiyordu, eksiği −0,4).
5. **Gol çizgilerinde piyasanın kendi olasılığı daha iyi.** Beklenen gol piyasadan gelse de skor olasılıkları iki parametreli Poisson'dan kuruluyor; 3,5 ve 4,5 gibi çizgilerde piyasa kuyruğu daha kalın fiyatlıyor. Toplam gol Brier: model 0,2375 · piyasanın olasılığı 0,2319; karşılıklı golde 0,2390 · 0,2339. 22 Ekim'de de aynıydı (0,241 · 0,232).
6. **Gol fazlası.** 33 maçta 116 gol, xG 94,7, beklenen 97,2. Piyasa da aynı ölçüde yanıldı; model kusuru değil, örnek bu hafta gollü. 3,5 alt 79 önerinin 21'inde çıktı, 10'u tuttu.

## Değişenler (model v4)

Kod: `model/model.py`. v1–v3 kayıtlı tahminleri birebir üretmeye devam ediyor; yeni maçlar v4 ile hesaplanır.

| | v3 | v4 | Neden |
|---|---|---|---|
| Beklenen gol | takım verisi %20 · piyasa %80 | piyasa × çarpan^0,25 × ayar^0,5 | Madde 1. Form, eksik ve elle ayar piyasayı biraz oynatır; tamamen silinmez |
| Güçlü | model ≥%58, piyasa ≥%50, değer −0,05…+0,15 | model ≥%64, piyasa ≥%60, değer ≥ −0,08 | Madde 2. Güçlü artık "değer" değil, model ve piyasanın birlikte yüksek olasılık verdiği seçenek |
| Son 10 eşiği | Güçlü ≥%55, Orta ≥%50 | yok (son 10 puanda ve bilette kalır; sayılamayan pazar yine öneri olmaz) | Madde 3 |
| Korner / kart ortalaması | 9,7 / 3,8 | 9,3 / 4,0 | Madde 4; gözlenene doğru yarı yolda |
| Toplam gol ve KG olasılığı | skor matrisinden | %25 matris · %75 piyasanın olasılığı | Madde 5. Tam piyasa (0,2297) biraz daha iyi; form ve eksik bilgisi tamamen silinmesin diye %75 |

Elle ayar (`--ayar-ev`, `--ayar-dep`) kayda `model.ayar` olarak yazılır ve beklenen gole yarım güçle uygulanır: 0,95 → ×0,975.

Aynı 33 maçta (`python3 model/karsilastir.py data/tahminler.json v1 v2 v3 v4`):

| | v1 | v2 | v3 | v4 | Piyasa |
|---|---|---|---|---|---|
| Brier, tüm pazarlar | 0,2398 | 0,2361 | 0,2335 | **0,2302** | 0,233 |
| Toplam gol | 0,251 | 0,248 | 0,241 | 0,233 | 0,232 |
| Korner | 0,272 | 0,242 | 0,242 | 0,236 | 0,254 |
| Öneri isabeti | 46/87 | 45/82 | 44/79 | 68/97 | |
| Öneride piyasanın beklentisi | | | 46,5 | 58,3 | |
| Güçlü / Orta | | | 19/35 · 25/43 | 30/38 · 38/59 | |

v4 olasılıklarda ilk kez piyasanın önüne geçiyor. Fark korner, kart ve ilk golden geliyor; gol pazarlarında piyasayla aynı düzeyde. Öneriler piyasanın beklentisinden +10 fazla tuttu; Güçlü (30/38, piyasa 25,3) Orta'dan (38/59, piyasa 33,0) iyi.

**Uyarı:** Güçlü eşikleri, korner/kart ortalamaları ve gol pazarı payı bu 33 maça bakılarak seçildi; öneri isabetindeki üstünlük örnek içi ve büyük kısmı gürültü olabilir (±4–5). Gerçek sınav sonraki günler. Brier iyileşmesi (piyasa payı) üç ayrı örnekte aynı yönde olduğu için daha güvenilir.

## Değiştirmediklerimiz

- **Puan ağırlıkları** (%60 model, %25 son 10, %15 piyasa).
- **Orta eşikleri** (model ≥%54, değer −0,08…+0,30).
- **3,5 alt yoğunluğu.** v4'te de en sık öneri (97'de 17). Günde aynı pazara sınır koymak ürün kararı; açık.
- Gol ortalaması: bu haftaki gol fazlasını piyasa da kaçırdı; düzeltme yok.

## Süreç

- Sonuç topla: yerel sunucu (`model/sunucu.py 8643`) sayfasının konsolunda `t.sonuc(id, kok)`; 9 maç paralel tek çağrıda.
- **Kesin 11 güncellemesi hâlâ yapılmıyor.** 23 Ekim'de de hepsi muhtemel 11; v4'te etkisi küçük (çarpan^0,25), ama eksik oyuncu bilgisi yine değerli.
