# Köşe Vuruşu

Veriyle futbol, kalemle tahmin. Maç analizleri ve skor tahminleri, gazete köşesi düzeninde.

- `index.html`, `assets/`: statik sayfa (derleme adımı yok)
- `data/tahminler.json`: tüm maçlar, model çıktıları, köşe yazıları ve sonuçlar

Model: son 10 resmî maçın ağırlıklı gol beklentisi, lig gücü düzeltmesi, iç/dış saha ayrımı ve
Dixon-Coles düzeltmeli Poisson skor dağılımı. Tahminler eğlence amaçlıdır; bahis tavsiyesi değildir.
