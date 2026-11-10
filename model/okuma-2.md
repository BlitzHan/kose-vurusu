# Okuma 2 · isabet

Tarih: 10 Kasım 2026. Okuma 1'in üstüne tek değişiklik: sinyal eşikleri. Olasılık hesabı aynı
(oranlardan marjsız olasılık, başka bir şey eklenmez); ayrıntı `okuma-1.md`.

## Neden

İstek: Güçlü sinyaller daha sık tutsun (okuma-1'de %69).

%69'u belirleyen model değil, 1,35 oran tabanıydı. Oranlar bu veride dürüst: bir seçimin tutma
olasılığı ≈ 0,96 / oran. 1,35 oranda tavan ≈ %70. Taban inmeden isabet çıkamaz.

## Kural

| | okuma-1 | okuma-2 |
|---|---|---|
| Oran tabanı | 1,35 | **1,15** |
| Güçlü | ≥ %66 | **≥ %75** |
| Orta | %56–66 | **%66–75** |

Gerisi aynı: grup başı en olası tek seçenek, 2,5 üst + KG var tek hikâye, kota yok.

## Geriye dönük test: 193 bitmiş maç

| | Tuttu | Beklenen | 1 TL kasası | Beklenen kasa |
|---|---|---|---|---|
| **Güçlü** | **195/240 (%81)** | %80 | −4,1 TL | −6,9 TL |
| Orta | 143/200 (%72) | %71 | −6,5 TL | −8,4 TL |

İki dönemde aynı (27 Ekim öncesi %81, sonrası %82). Eşik taraması:

| Taban | Eşik | Sinyal | Tuttu | Beklenen | Ort. oran |
|---|---|---|---|---|---|
| 1,35 | %66 | 231 | %68 | %69 | 1,40 |
| 1,30 | %70 | 161 | %73 | %73 | 1,33 |
| 1,20 | %75 | 208 | %76 | %79 | 1,24 |
| 1,15 | %75 | 241 | %81 | %80 | 1,21 |
| 1,15 | %80 | 128 | %88 | %83 | 1,18 |
| 1,10 | %80 | 254 | %87 | %86 | 1,14 |

%88'lik satırın beklenen değeri %83; fark şans payının içinde.

## Kupon ve kasa

Maç başı en olası Güçlü ayakla, aynı günün tüm kombinasyonları:

| Ayak | Tutma (beklenen) | Beklenen getiri |
|---|---|---|
| 1 | %81 | −%2,7 |
| 2 | %65 | −%5,4 |
| 3 | %52 | −%8,0 |
| 4 | %42 | −%10,7 |
| 5 | %34 | −%13,2 |

- Her ayak büro kesintisini bir kez daha öder. Kupon sayısını artırmak beklenen getiriyi
  değiştirmez; ayak sayısını artırmak kötüleştirir.
- Yayındaki günlük kupon (en olası 2 ve 3 ayak) 12 günde 2'li 11/12, 3'lü 9/11 tuttu. Beklenen
  yaklaşık 8/12 ve 6/11; fazlası şans, 12 gün bir şey kanıtlamaz.
- Kasayı artıya taşıyabilecek tek şey hâlâ fiyat: aynı ayağı birkaç bürodan en yüksek oranla
  almak. İkinci kaynak oranı şu an yalnız 9 maçta var.

## Denenip girmeyenler

- Son 10 maç kanıtı: kanıtı güçlü ve zayıf sinyaller oranın söylediği kadar tuttu. Seçime girmez.
- "Karşılıklı gol var": 41 sinyalde %56 (beklenen %68). Örnek küçük; %75 eşiğinde zaten nadiren
  Güçlü oluyor, ayrıca kural eklenmedi. 400 maçta yeniden bakılır.
