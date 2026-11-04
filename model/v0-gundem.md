# v0 (Sıfır) — tasarım ve ilk test

Tarih: 4 Kasım 2026. v1–v7 arşivde; bu sürüm sıfırdan kuruldu.

## Ne değişti

| | v1–v7 | v0 |
|---|---|---|
| Beklenen gol | v4'ten sonra ağırlıklı olarak bahis oranından geri hesaplanıyordu | Yalnız takımların xG geçmişinden; oran modelden tamamen ayrı |
| Oran | Modelin girdisi | Karşılaştırma ve fiyat kaynağı |
| Marj | `1/oran` orantılı temizleme | Shin yöntemi |
| Sinyal | GÜÇLÜ/ORTA, çok pazar | Tek sınıf; yalnız fiyat adil olasılığın üstündeyse |
| Pazarlar | 15 pazar | 1X2, DNB, AH, 2.5 alt/üst |
| 1 ₺ sayacı | Tüm öneriler | Yalnız sinyaller; ölçü ROI + CLV |
| Determinizm | Kısmi | Ayar hash'i + veri hash'i her kayıtta |

## Test: 175 bitmiş maç, 1509 pazar satırı

Walk-forward: her maçın takım gücü yalnız o maçtan önceki veriden hesaplandı.
Eğitim 105 maç (21–27 Ekim), test 70 maç (27 Ekim–1 Kasım).

### Model bahis oranını yeniyor mu?

| | log-loss | Brier |
|---|---|---|
| Saf model (xG) | 0,6484 | 0,2287 |
| Marjsız oran (Shin) | **0,6158** | **0,2145** |
| Karışım | 0,6158 | 0,2145 |

Model ağırlığı taraması: eğitimde en iyi **b2 = 0,00**. Yani takım gücü modeli,
bahis oranının üstüne hiçbir bilgi katmıyor. Test setinde de aynı.

Pazar bazında:

| Pazar | Model log-loss | Oran log-loss | Fark |
|---|---|---|---|
| 1X2 (MS1) | 0,6720 | 0,5912 | +0,081 (model kötü) |
| 2,5 gol | 0,6731 | 0,6730 | ±0,000 (eşit) |
| KG | 0,7030 | 0,6894 | +0,014 (model kötü) |

Toplam golde model piyasayla başabaş; maç sonucunda geride.

### Modelin ayrıştığı yer değer mi?

| Ayrışma (model − oran) | n | CLV | Kapanış hareketi |
|---|---|---|---|
| ≤ −0,10 | 245 | +%1,5 | −0,9 |
| −0,02…+0,02 | 278 | +%0,4 | +0,1 |
| +0,05…+0,10 | 209 | −%0,7 | +0,3 |
| ≥ +0,10 | 253 | **−%2,3** | +0,9 |

Model piyasadan yukarı ayrıştığında kapanış oranı **modelin tersine** hareket ediyor.
Yani modelin iddialı olduğu yerler sistematik olarak yanlış. Bu, v7'de görülen
"+%1,4 CLV" sinyalinin v0'ın bağımsız modelinde tekrarlanmadığını gösteriyor.

### Favori/uzun oran yanlılığı var mı?

1X2'de ima olasılığı ≥ %50 olan seçenekler: 108 maç, gerçek isabet %62,0, ima %64,3,
ROI −%8,1. Favoriler hafifçe fazla fiyatlanmış. Uzun oranlarda (0,10–0,15) %17,3'e
karşı %12,4 ima var ama n=52, gürültü.

### xG'ye göre şanssız takım geri döner mi?

Son 5 maçta gol − xG farkı en negatif olan ev sahipleri: 32 maç, galibiyet %50,
CLV −%2,8. Etki yok.

## Sonuç

Bu veriyle (kamuya açık xG + tek büro oranı) piyasayı yenmek mümkün değil.
Sebep modelin kötü yazılması değil: **kapanış oranı zaten bütün kamu bilgisini içeriyor.**

Tek gerçek kaldıraç **fiyat farkı**: aynı sonuca iki büro farklı oran veriyorsa,
adil olasılık (Shin, kaynak A) ile en iyi fiyat (A/B) arasındaki fark edge olur.
v0 bu yüzden sinyali tahminden değil fiyattan üretiyor:

```
adil p = Shin(kaynak A oranları)
fiyat  = max(kaynak A, kaynak B)
EV     = p * fiyat - 1
sinyal: EV >= %3, oran 1,50–2,60, maç başı tek seçim
```

Tek kaynak varken EV tanım gereği negatif (marj kadar) → sinyal yok. Doğru davranış:
edge yoksa oynamamak. Benchmark bunu gösterecek.

## Açık işler

1. İkinci kaynak oranı (Mackolik) çekimi — `--b oran.json` ile şimdiden çalışıyor.
2. 400+ maç birikince b2 ve eşik yeniden taranacak.
3. Yumuşak pazarlar (alt ligler, az kapsanan turnuvalar) ayrı test edilecek.
4. Kadro/eksik bilgisi modele değil, yalnız elle ayara girecek (yarım güçle).
