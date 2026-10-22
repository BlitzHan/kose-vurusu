# Köşe Vuruşu

Veriyle futbol, kalemle tahmin. Maç analizleri ve skor tahminleri, gazete köşesi düzeninde.

- `index.html`, `assets/`: statik sayfa (derleme adımı yok)
- `data/tahminler.json`: tüm maçlar, model çıktıları, köşe yazıları ve sonuçlar
- `model/`: model kodu (`model.py`, sürüm v1/v2), biten maçları değerlendirme (`degerlendir.py`, `karsilastir.py`) ve geri bildirim notları

Model: son 10 resmî maçın ağırlıklı gol beklentisi, lig gücü düzeltmesi, iç/dış saha ayrımı ve
Dixon-Coles düzeltmeli Poisson skor dağılımı. Tahminler eğlence amaçlıdır; bahis tavsiyesi değildir.
