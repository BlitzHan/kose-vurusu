# Futbol tahmin modeli: sıfırdan bakış istiyoruz

Sen deneyimli bir spor bahsi kantitatif analistisin. Aşağıdaki sistemi eleştir ve sıfırdan daha iyi bir yaklaşım öner. Dosya okuma, araç kullanma, kod çalıştırma YOK; yalnız bu metne dayanarak cevap ver. Türkçe yaz.

## Amaç
Maç öncesi oranlarla kendi olasılığımızı kıyaslayıp, bahis sitesinin düşük fiyatladığı (tutma ihtimali oranın ima ettiğinden yüksek) seçimleri bulmak. Ürün: günlük maç sayfası, maç başına 0-3 öneri. Kullanıcı ayrıca "düşük oranlı, tutma ihtimali yüksek 4-5 seçimi kombin yapıp tek kuponla yüksek orana ulaşmak" fikrini seviyor.

## Elimizdeki veri (her maç için)
- Tahmin anındaki oranlar (tek kaynak, ortalama piyasa; marj ~%5-6): 1X2, çifte şans, beraberlikte iade, Asya handikabı, KG var/yok, toplam gol 0,5-5,5 çizgileri, ilk yarı 1X2, ilk golü kim atar, kart ve korner çizgileri.
- Aynı pazarların açılış oranı ve kapanış oranı (maç başlarkenki son oran).
- İki takımın son 10 resmî maçı: skor, ilk yarı, xG, şut, isabetli şut, büyük fırsat, korner, kart, topa sahip olma, ilk 11 reytingi, turnuva.
- Muhtemel/kesin 11, eksik oyuncular (sakat/cezalı), oyuncuların son 5 maç reytingi, gol+asist payı.
- Puan durumu (lig ve Avrupa kupası), maçın önemi.
- Maç sonrası: skor, ilk yarı, xG, korner, kart.
- Örnek: 122 biten maç (Süper Lig, 5 büyük lig, Eredivisie, Championship, Ligue 2, İspanya ve Almanya kupası alt tur maçları). 53 maç daha bu hafta sonu.

## Mevcut model (v6 → v6.5)
1. Beklenen gol (λ ev, λ dep) yalnız 1X2 ve 2,5 üst oranlarına Dixon-Coles Poisson uydurularak bulunuyor (ρ=-0,075). Takım verisinin λ'da payı 0.
2. Bu λ, oyuncu formu/eksik oyuncu çarpanının 0,25 kuvvetiyle oynatılıyor (yaklaşık ±%4).
3. Tüm pazar olasılıkları bu skor matrisinden; toplam gol, KG, korner ve kartta %75 piyasa olasılığıyla harmanlanıyor. İlk yarı = λ × 0,48 sabit.
4. v6 seçim: model ≥%64 ve piyasa ≥%60 olan seçenek "Güçlü" (yani piyasanın favorisi), puan = %60 model + %25 son 10 maç sıklığı + %15 piyasa. Maç başı en fazla 3, korelasyonlu olanlar elenir, oran ≥1,35.
5. v6.5 seçim (bugün yayına girdi): ayrışma = model/piyasa − 1. ≥%8 Güçlü, %5-8 Orta; oran 1,60-3,50; korner, kart, Asya handikabı hariç.

## Ölçülen sonuçlar (122 maç)
- Brier tüm pazarlar: model 0,238, piyasa 0,236. Model piyasanın biraz gerisinde.
- v6 öneriler: 179/302 tuttu, piyasa beklentisi 182,4. Güçlü 97/145 (%67) ama ortalama oran 1,45 → başabaş %69; 1 TL sanal getiri %−4,3. Orta %−13,4.
- Kapanış oranına göre (CLV = tahmin oranı / kapanış oranı − 1): tüm pazarlar ortalaması +%0,2. Model piyasadan ≥%5 yüksek gördüğünde +%2,4 (±0,65), ≥%8 → +%3,5 (±0,9); model ≥%5 düşük gördüğünde −%0,9. Gruplara göre (≥%5): maç sonucu +%3,7, ilk gol +%3,3, KG +%3,8, ilk yarı +%2,3, toplam gol +%1,0, Asya handikabı +%0,2.
- Kapanışın marjsız olasılığına göre beklenen getiri: tüm pazarlar %−6,4; ayrışma ≥%8 seçimleri %−2,8.
- Gol: maç başı gerçek 3,31, xG 3,02, model 3,04.
- Günlük 4'lü kupon (en olası 4 öneri): 8 günde 1 tuttu; kapanışa göre beklenen getiri %−19.

## Sorular
1. Bu yaklaşımın temel hatası ne? Sıfırdan kursan mimari ne olurdu? (Kısa, somut.)
2. Elimizdeki veriyle piyasanın gözden kaçırabileceği en umut verici 3-5 sinyal hangisi? Her biri için: nasıl hesaplanır (formül düzeyinde), neden piyasa kaçırabilir, kapanış oranıyla nasıl test edilir.
3. Açılış → tahmin anı → kapanış oran hareketini sinyal olarak nasıl kullanırsın?
4. Pazarlar arası tutarsızlık (ör. 1X2, çifte şans, beraberlikte iade, handikap ve gol çizgilerinin ima ettiği olasılıkların birbiriyle çelişmesi) bir değer kaynağı olabilir mi? Nasıl ölçülür?
5. Kombin (4-5 düşük oranlı seçim) fikri hakkında dürüst görüşün; hangi koşulda mantıklı olur?
6. Bu küçük örnekle (122 + 53 maç) aşırı uydurmadan nasıl karar veririz?
7. Hemen bugün uygulanabilecek, düşük riskli en iyi 3 değişiklik (öncelik sırasıyla).

En fazla ~70 satır. Madde madde, net. Genel geçer laf yerine bu sisteme özel öneriler.
