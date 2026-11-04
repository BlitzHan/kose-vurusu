# Okuma 1 · sıfırdan

Tarih: 4 Kasım 2026. v1–v7 ve v0 (Sıfır) arşivde. Sürüm adı artık `okuma-N`; ilk sürüm `okuma-1`.

## Bakış açısı

Eski sürümler oranları yenmeye çalıştı. Takım verisiyle (xG, form, lig gücü) kurulan her model
bitmiş maçlarda oranlardan kötü çıktı. v0, AEK–Real Madrid'de AEK'yi favori gösterdi. Değer
eşiği yüzünden de 9 maçta tek öneri çıkardı.

Okuma tersini yapar: **olasılığın kaynağı oranlardır**, büro kesintisi temizlenir, başka hiçbir
şey eklenmez. Bizim işimiz bu olasılıkları okumak: her maça tam bir tahmin ve sinyal listesi,
her sinyalin yanında son 10 maç kanıtı.

## Kurallar (`model/okuma.py`)

| Parça | Kural |
|---|---|
| Olasılık | Her pazar grubu kendi içinde güç yöntemiyle marjsız (1X2, İY, ilk gol, KG, her gol/korner/kart çizgisi) |
| Beklenen gol | 1X2 + 1,5/2,5/3,5 alt + KG olasılıklarına en iyi uyan Dixon-Coles çifti (ρ −0,06) |
| Tahmin | Favori ≥ %50 → kazanır; değilse kaybetmez |
| Skor | Tahminle aynı yöndeki en olası skor |
| Senaryolar | Ev farklı · ev tek fark · beraberlik · dep tek fark · dep farklı |
| Sinyal | Tüm pazarlar, oran ≥ 1,35. **Güçlü ≥ %66**, **Orta %56–66**. Grup başı tek; 2,5 üst + KG var tek hikâye. Kota yok |
| Değerli fiyat | İkinci kaynağın oranıyla olasılık × oran ≥ 1 |
| Cesur | Oran 2,00–3,60 arası tek sonuç ya da aynı maç ikilisi (matristen); kasaya girmez |
| Kupon | Günün Güçlü'lerinden maç başı tek ayak, en olası 2'li ve 3'lü |
| 1 TL | Her Güçlü'ye 1 TL; yanında beklenen kasa (Σ olasılık × oran − 1) |

## Geriye dönük test: 184 bitmiş maç (maç öncesi oranlarla)

| | Tuttu | Beklenen | 1 TL kasası | Beklenen kasa |
|---|---|---|---|---|
| Tahmin | 125/184 (%68) | %67 | | |
| **Güçlü** | **146/212 (%69)** | %69 | **−7,6 TL** | −8,5 TL |
| Orta | 183/327 (%56) | %60 | −40,1 TL | −16,6 TL |
| Cesur | 81/184 (%44) | %47 | | |
| Skor | 14/184 (%8) | %11 | | |

Kalibrasyon (tüm pazarlar): %70–80 denilen %72, %80–90 denilen %86 oldu. Oranlar dürüst.

## Kasa neden eksi kalıyor

- 1 TL kasası uzun vadede **büro kesintisi kadar** eksidir (tek kaynakta ≈ %4–7). Hangi seçim
  kuralı olursa olsun: 0,55–0,80 arasındaki tüm eşikler −%4 ile −%11 arasında çıktı.
- Düşük oranlı "garanti" kuponlar bunu düzeltmez; kombin kesintiyi çarpar (3'lü ≈ −%7).
- 1,35 oran kuralı olasılığın tavanını ≈ %70'e çeker; "%85 tutan Güçlü" bu kuralla mümkün değil.
- Pazar bazında artı görünenler (KG yok +%9, n = 112) gürültü: standart hata ≈ ±%8.
- Artıya giden tek gerçek yol **fiyat**: aynı seçimi iki kaynaktan en yüksek oranla almak ve oran
  düşmeden önce almak. Kapanış oranıyla en iyi fiyat alındığında Güçlü kasası −%3,6'dan −%2,9'a
  iniyor. İkinci kaynak (alternatif büro) her maçta çekilirse "değerli fiyat" işareti anlam kazanır.

## Kaç maç gerekir

- Takım başına son 10 resmî maç kanıt için yeterli (olasılığa girmiyor).
- Güçlü isabetini ±%5 doğrulukla görmek için ≈ 300 Güçlü sinyal (≈ 250 maç).
- Kasanın gerçekten artıda olduğunu kanıtlamak için ≈ 1500 sinyal: oran 1,40'ta 1 TL'lik bahsin
  sapması ≈ 0,6; +%3'ü şanstan ayırmak bunu ister. Tek günlük kasa hiçbir şey söylemez.

## Günlük akış

`analiz.py` (ya da `v0_analiz.py --b`) maç kaydını ve oranları kurar, ardından:

```
python3 model/okuma.py 2026-11-05      # o günün okuması + kupon + test özeti
python3 model/okuma.py --test          # yazmadan isabet ve kasa raporu
```

Sonuç işleme değişmedi (`isle.py`); site sinyalin tutup tutmadığını pazarın sonucundan okur.
