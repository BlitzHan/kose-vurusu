# Geri bildirim · 2 Kasım 2026 · v7

31 Ekim (30 maç) ve 1 Kasım (23 maç) işlendi; toplam **175 maç**, hepsinde kapanış oranı var. Bu iki gün v6.5 ve v6.6 için ilk eğitim dışı sınav.

## Hafta sonu (yayındaki v6)

- 115 öneri, 68 tuttu. Güçlü 36/59, Orta 32/56.
- 1 birimlik sanal getiri %−12,5 (Güçlü %−14,4). Kapanışa göre oran farkı %−0,7: v6 piyasanın favorisini piyasayla aynı fiyattan seçiyor, kaybı marj kadar.
- 175 maçta v6: kapanış farkı ≈ 0 (üç dönemde de), kapanışa göre beklenen getiri %−6,6 ile %−7,3.

## Aynı 53 maçta üç sürüm (bugünkü oranlarla yeniden hesap)

| Sürüm | Öneri | Kapanış farkı | Kapanışa göre bek. getiri | Sanal getiri |
|---|---|---|---|---|
| v6 | 115 | %−0,7 ±0,4 | %−7,0 | %−12,5 |
| v6.5 | 11 | %+4,3 ±1,8 | %−3,4 | %+48 (gürültü) |
| v6.6 | 42 | **%+4,0 ±1,7** | %−2,6 | %−7,6 |

v6.6'nın sinyali (takım xG'si ile piyasanın yarı yarıya harmanı, ayrışma ≥%12) üç ayrı dönemde de kapanışı yendi: eğitim +%1,9, test +%1,4, yeni günler +%4,0. Tasarım 122 maçla yapılmıştı; bu 53 maç ona hiç gösterilmedi.

## Tarama (yalnız eğitim setiyle seçim)

- Piyasa ağırlığı 0,3–0,7 ve eşik %8–20 ızgarası: eğitimde kapanış farkı her yerde +%1,5 ile +%2,4, testte +%2 ile +%4. Yüzey düz; ince ayar gürültü olurdu. **Ağırlık 0,5 ve eşikler (%12 / %8) değişmedi.**
- Toplam gol grubunu eklemek bir şey katmadı.
- Gruplar (eğitim): maç sonucu kapanış +%2,3 / bek. getiri %−3,8; ilk yarı +%1,0 / %−6,5; ilk gol %−10 (marj yüksek, `iy=0.48` sabiti yapısal sapma da üretiyor). **v7 yalnız maç sonucu grubunda oynar.**

## v7

`SURUM['v7'] = v6.6 + gruplar=('Maç sonucu',), en_fazla=1`

| Dönem | Öneri | Kapanış farkı | Bek. getiri |
|---|---|---|---|
| Eğitim (<27 Eki) | 62 | %+2,3 ±1,1 | %−3,8 |
| Test (27–30 Eki) | 24 | %+1,9 ±2,5 | %−3,8 |
| 31 Eki–1 Kas | 28 | %+5,0 ±2,4 | %−1,1 |

- 1X2, çifte şans, beraberlikte iade; oran 1,60–3,50; maç başı tek seçenek.
- Orta (%8–12) sitede "Farklı bakış" etiketiyle, öneri değil (Yıldırım'ın 31 Ekim kararı).
- Karneye **Kapanış** kutusu eklendi: günün önerilerinde oranın kapanışa göre ortalama farkı. v7'nin ana ölçüsü bu; isabet yan bilgi.
- `analiz.py` varsayılanı v7.
- Küçük düzeltmeler: korner/kart verisi yoksa `st.mean([])` çökmesi (lig ortalamasına düşer); lig maçında Avrupa kupası önem metni yazılması.

## Açık söylenmesi gereken

- **Kapanışa göre beklenen getiri hâlâ eksi** (yaklaşık %−2 ile %−4). Sinyal gerçek görünüyor ama tek kaynaklı oranların marjını (%6–7) karşılamıyor. v6'ya göre kayıp yarıya iniyor, kâra dönmüyor.
- Artıya geçmenin yolu modelde değil fiyatta: aynı seçimi daha iyi orandan almak (çok kaynak, en iyi fiyat). Bu ayrı bir iş.
- Sanal getiri çok gürültülü (oran ortalaması 2,8; 100 öneride standart hata ≈ %15). Gün bazında artı ya da eksi görmek bir şey kanıtlamaz.

## Sonra izlenecek

- Seçim tipi (tüm 175 maç, eğitim içi değil, karar için kullanılmadı): beraberlikte iade kapanış +%5,0 / bek. getiri %−1,8; 1X2 +%3,0 / %−3,2; çifte şans +%1,2 / %−4,2. Yeni maçlarla çifte şansın kalıp kalmayacağına bakılır (v7.1 adayı).
- Kombin (aynı maçtan ilişkili ayaklar, skor matrisinden ortak olasılık) ve kesin 11 hâlâ beklemede.
