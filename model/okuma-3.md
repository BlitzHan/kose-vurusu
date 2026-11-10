# Okuma 3

10 Kasım 2026. Daha az Güçlü sinyalle daha yüksek isabet hedeflenir.

- Güçlü eşiği ham marjsız olasılıkta %80. Orta eşiği %66, oran tabanı 1,15.
- Beraberlikte iade seçenekleri sinyallerden çıkarılır. Böylece Güçlü yüzdesi doğrudan gerçekleşme olasılığı olarak yorumlanabilir.
- Pazar grubu başına en olası seçim ve mevcut gol/KG tekrar filtresi kullanılır.
- Olasılık hesabı mevcut güç yöntemi, skor hesabı mevcut Dixon–Coles modelidir.

## Geçmiş karşılaştırma

Aynı 193 maçın maç öncesi girdileri iki sürümle yeniden hesaplandı.

| Dönem | Okuma 2 Güçlü | Okuma 3 Güçlü |
|---|---|---|
| 31 Ekim öncesi, 122 maç | 132/164 (%80,5) | 73/81 (%90,1) |
| 31 Ekim ve sonrası, 71 maç | 63/76 (%82,9) | 32/37 (%86,5) |
| Toplam | 195/240 (%81,3) | 105/118 (%89,0) |

Güçlü sinyal çıkan maç sayısı 167'den 102'ye indi. Aynı maçın birden fazla sinyali ilişkili olabilir.
Eşik taramasında %75, %80, %82 ve %85 incelendi; iki tarih bölümünün sonuçları da görüldü.
Bu nedenle son bölüm keşif amaçlı tarih kontrolüdür. Bağımsız ileri dönem doğrulaması yeni maçlarla yapılmalıdır.
%89 gerçekleşen isabetin yanında modelin ortalama olasılığı %82,6'dır. Gelecek maçlarda %89 vaat edilmez.
Ölçümde iade olan eski seçimler isabet paydasından çıkarılır.

## Kullanım

Repo kökünden geçmiş karşılaştırmasını yazdırmak için

```sh
python -B -X utf8 model/okuma3.py
```

Maç verisi normal analiz akışıyla toplandıktan sonra, başlamamış maçlara uygulamak için

```sh
python -B -X utf8 model/okuma3.py 2026-11-11 --yaz
```

Tarih verilmezse tüm başlamamış maçlar işlenir. Türkiye saati kullanılır.
Eski okuma kaydı maçın okuma_gecmisi listesine alınır. Biten veya başlamış maçlar korunur.
Yeni maçların sonucu normal isle.py akışıyla işlenir. Geçmiş karşılaştırması yayımlanan kayıtları yazmaz.
Site mevcut okuma veri yapısını okuyabilir. Yayına alma sırasında açıklama metnindeki Güçlü eşiği sürüme göre güncellenmelidir.

## Kontrol

193 maçın tamamında iki sürüm çalıştırıldı. Eşik, iade elemesi, bitmiş kayıtların korunması,
gelecek maçın güncellenmesi, önceki tahminin arşivi ve girdinin değiştirilmemesi kontrolleri geçti.
