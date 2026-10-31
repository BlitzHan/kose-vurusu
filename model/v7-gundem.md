# v7 gündemi · Pazartesi 2 Kasım 2026

Karar 31 Ekim'de alındı. **30 Ekim, 31 Ekim ve 1 Kasım veri toplama günleri.** v7 Pazartesi, Yıldırım komut verince yapılır; o zamana kadar ajan kendiliğinden başlamaz.

## Hafta sonu kuralları

- Model dondurulmuş: v6. `model.py` ve eşikler değişmez.
- 31 Ekim (30 maç) ve 1 Kasım (23 maç) tahminleri v6 ile yapıldı; olduğu gibi kalır. Kesin 11 ya da oran yenilemesi yapılmaz (ölçüm temiz kalsın).
- Sonuçlar normal akışla işlenir (`isle.py`, `degerlendir.py`). Geri bildirim notu kısa tutulur; büyük yorum Pazartesi'ye kalır.
- Pazartesi elde olacak: yaklaşık **175 maç**, bunun 86'sı v6.

## Pazartesi akışı

1. 1 Kasım sonuçlarını işle, `git pull --ff-only`.
2. `degerlendir.py`: grup bazında Brier (model · piyasa), puan kovaları, seviye karnesi, gün bazında isabet ve piyasa beklentisi.
3. **Eğitim/test ayrımı:** değişiklikler 27 Ekim öncesi maçlarla (89 maç) seçilir, 27 Ekim ve sonrasıyla (86 maç) sınanır. Test setinde piyasayı geçmeyen değişiklik girmez. Parametreler teste bakmadan yazılı olarak sabitlenir.
4. Aday değişiklikleri `karsilastir.py` ile tek tek, sonra birlikte dene.
5. Sonuçları Yıldırım'a göster, karar onun; sonra `SURUM['v7']`.

## Gelişime açık noktalar

Kaynak: 30 Ekim geri bildirimi, Claude incelemesi, DeepSeek V4.1 incelemesi (31 Ekim). Satır numaraları 31 Ekim'deki `model.py`'ye göre.

### Teşhis

- 122 maçta öneriler 179/302, piyasanın beklentisi 182,4 (z = −0,4). Model piyasayla aynı seviyede, biraz geride; değer katmıyor.
- 30 Ekim 5/13 çoğunlukla şans: bu isabet oranıyla 13 öneride ≤5 ihtimali %7, 8 günde böyle bir gün görme ihtimali %44. Veri işleme doğru (13 öneri skorla tek tek kontrol edildi).
- Gol seviyesi: maç başı model 3,04, xG 3,02, gerçek gol 3,31. Modelin seviyesi xG ile uyumlu; fazlası bitiricilik şansı. **Lig bazlı gol çarpanı (1,05–1,08) önerilmiyor.**
- v4'ten beri `piyasa_agirlik=1.0`: beklenen gol tamamen piyasadan. Takım tabanı, lig gücü, xG hesabı ölü kod. Model = piyasa + ±%4 form/eksik çarpanı (`car**0.25`). Brier farkı bu gürültünün bedeli.
- Seçim yanlılığı: maç başı onlarca pazardan en yüksek puanlı 3'ü seçiliyor; 0,60 üstü puanlarda gerçek isabet 4–8 puan altta.

### Aday değişiklikler (öncelik sırası)

1. **Puandan son 10'u çıkar.** `son10_esik=False` ile seviyeden çıkarılmıştı ama puanın %25'i hâlâ o (`puan` ağırlıkları). Puan = piyasa ağırlıklı; model yalnız eleme yapsın (model piyasadan belirgin düşükse öneri düşer).
2. **Korner, kart, karşılıklı golde piyasa payı 1,0.** Üçünde de model geride; kart 4,5 alt gibi "model ayrıldı, kaybetti" vakaları kesilir.
3. **Beklenen golü tüm gol çizgilerine uydur.** `piyasa_lambda` yalnız 1X2 + 2,5 üst kullanıyor; 1,5 / 3,5 / 4,5 fiyatları elde. Izgarayı simetrik ve sık yap (ikisi de 0,10–4,00, adım 0,02). 3,5 alt sorununun kökü Poisson'un ince üst kuyruğu olabilir; 3,5 alt'ı kaldırmadan önce bu denensin.
4. **İlk yarıda piyasayı kullan.** `iy=0.48` sabit; IY1/IYX/IY2 oranları elde ama kullanılmıyor. `pazar_piyasa['İlk yarı']` ekle ya da oranı piyasadan çöz.
5. **Kalibrasyon.** Gösterilen yüzdeye tek parametreli düzeltme (eğitim setinde sabitlenir).
6. **Orta seviyesi.** Kaldırma kararı test setine kalsın; ara çözüm: bilet önerisi değil, "veri ne diyor" bilgisi.
7. **Kapanış oranı (CLV): toplanıyor (31 Ekim).** Maç bitince kaynak son oranları (kapanış) ve açılış oranlarını hâlâ veriyor. `topla.js` `sonuc()` artık oranları da çekiyor; `isle.py` her pazara ve öneriye `kapanis` yazıyor. 122 eski maç geriye dönük dolduruldu (`ham/<id>-kapanis.json`, `isle.py --kapanis`); pazar kapsaması 4403/4552. İlk tablo: Güçlü önerilerde oranımız kapanışa göre ortalama +%0,2 (47 düştü, 42 yükseldi), Orta −%0,3. Kapanışın marjsız olasılığıyla beklenen getiri Güçlü %−6,0, Orta %−7,4; gerçekleşen sanal getiri Güçlü %−4,3, Orta %−13,4. Yorum: model piyasayla aynı fiyattan seçiyor, kaybı marj kadar. v7'nin ana sınavı: önerilerin kapanışı yenmesi.
8. **Kesin 11.** 175 kaydın yalnız 5'inde kesin. Piyasanın henüz fiyatlamadığı tek bilgi; ölçmek için ayrı alan gerekir (tahmini ezmeden).

### Küçük hatalar

- `analiz.py` 189–199: önem metni lig maçlarında Avrupa kupası şablonunu kullanıyor ("İlk 8'de… son 16"); `carpan=1.0` sabit, önem çarpanı ölü.
- `analiz.py` korner/kart ortalaması: veri yoksa `st.mean([])` çöker (`degerlendir.py`'de düzeltilen hatanın aynısı).
- `model.py` `ust()`: tam sayı çizgide (korner 9, 10) iade yok sayılıyor.
- `model.py` korelasyon filtresi harmanlanmamış matrisle çalışıyor, gösterilen olasılıkla tutarsız.
- `karsilastir.py` tarih ile eğitim/test ayrımı yapamıyor; Pazartesi önce bu eklenmeli.

DeepSeek'in iki iddiası kontrolde yanlış çıktı: `piyasa_lambda` hata teriminde beraberlik iki kez sayılmıyor; `deger = model × oran − 1` gerçek oranla beklenen getiri, hata değil.

## Yıldırım'ın kararları (31 Ekim)

1. **Amaç: değer.** Piyasanın gözden kaçırdığı, tutma ihtimali oranın söylediğinden yüksek seçenekleri bulmak. Geçmiş maçlar, oyuncu durumu, maçın anlamı, rakiple geçmiş ve ekstra hırs gibi bilgiler oranla kıyaslanır. Favoriyi göstermek amaç değil.
2. **Sinyalsiz gün kabul.** Sırf önermek için tutmayacak oran önerilmez.
3. **Orta kalır**, ama bilet önerisi olarak değil: "farklı bir bakış açısı" olarak gösterilir.
4. **Kesin 11 ertelendi.** Maçtan hemen önce çekilip tahmine işlenmeli, ama bilgisayar akşamları kapalı ve otomasyon (sunucu, API) maliyet demek. Proje belli bir noktaya gelince yeniden konuşulur.

## Bu kararların v7'ye etkisi

- **v6 bu amaca ters çalışıyor.** Güçlü şartı "model ≥%64 ve piyasa ≥%60, değer ≈ 0": piyasanın favorisini seçiyor. Ayrıca `piyasa_agirlik=1.0` yüzünden modelin bağımsız bilgisi yok; piyasadan farklı düşünemeyen model piyasanın hatasını bulamaz.
- **Yeni ölçüt: isabet değil, değer.** 2,80 oranlı ve %40 tutan bir seçim kârlıdır ama karnede "kötü" görünür. v7 karnesi: kapanış oranına göre kazanç (CLV), bir birimlik sanal getiri (ROI) ve kalibrasyon. İsabet oranı yan bilgi olur.
- **Örnek uyarısı:** getiri çok gürültülü; 175 maçta gerçek bir üstünlüğü getiriyle kanıtlamak mümkün değil. Bu yüzden kapanış oranı (madde 7) artık en öncelikli veri.
- **Sitede sanal getiri (31 Ekim):** karnede "Güçlü · 1 ₺" bloğu; günün Güçlü önerilerine 1 ₺ yatırılmış gibi kâr/zarar ve yüzde. Tüm dönem gösterilmez (Yıldırım: model sık değiştiği için yalnız gün bazında).
- **Gerçekçi beklenti:** büyük liglerde form, sakatlık ve motivasyon büyük ölçüde zaten fiyatta. Üstünlük daha çok şu yerlerde aranmalı: alt ligler ve kupalar, haberin oranlara henüz yansımadığı erken saatler, kesin 11, piyasanın az ilgilendiği pazarlar. Her yeni bilgi (rakiple geçmiş, hırs, maçın anlamı) teste girer, kanıtlanmazsa çıkar.
- Aday değişikliklerden 1. madde (puan = piyasa) bu amaçla çelişiyor. Seçim puanı değerden kurulur (model / piyasa − 1, marjı ayıklanmış). Piyasa yalnız tabanlık eder.
- Diğer düzeltmeler (2–5) yine gerekli: modelin bağımsız katmanı eklenmeden önce taban olasılığın doğru olması lazım. Değer, doğru tabanın üzerine eklenen bilgiden çıkar.
