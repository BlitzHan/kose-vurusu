# Günlük akış

Repo kökünden; yerel sunucu `python3 model/sunucu.py 8643` (siteyi sunar, ham veriyi `ham/` altına yazar; `ham/` git'e girmez).

## Maç öncesi

1. Maç kimliklerini bul.
2. `http://localhost:8643` sayfasının konsolunda topla:
   ```js
   const t = await import('/model/topla.js?' + Date.now());
   await t.topla(MAC_ID, API_KOKU);
   ```
3. `python3 model/analiz.py MAC_ID [MAC_ID ...]` → `data/tahminler.json`'a ekler ya da günceller (v6). Başlık ve özet elle yazılır; güncellemede korunur.
4. Kesin 11 güncellemesi **yalnız kullanıcı isterse** yapılır; ajan kendiliğinden yapmaz, teklif de etmez. İstenirse kesin 11 açıklanınca (~1 saat önce) 2. ve 3. adımı tekrarla.

## Maç sonrası

1. `await t.sonuc(MAC_ID, API_KOKU)` → `ham/<id>-sonuc.json`
2. `python3 model/isle.py MAC_ID [MAC_ID ...]` → skor, istatistik, goller, pazarların `olan` değeri, önerilerin Tuttu/Tutmadı durumu. Tahminlere dokunmaz.
3. `python3 model/degerlendir.py` ve `python3 model/karsilastir.py`; bulgular `model/geri-bildirim-<tarih>.md`.

Kaynak adı repoda, sitede ve commit mesajlarında geçmez.
