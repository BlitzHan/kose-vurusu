"""Biten maçlarda tahmin ile gerçeği kıyaslar.

Kullanım: python3 model/degerlendir.py [data/tahminler.json]
Her yeni sonuç işlendikten sonra çalıştır; örnek büyüdükçe ayar önerileri anlam kazanır.
"""
import json, math, sys
from collections import defaultdict

yol = sys.argv[1] if len(sys.argv) > 1 else 'data/tahminler.json'
d = json.load(open(yol))
biten = [m for m in d['maclar'] if m.get('sonuc') and m['sonuc'].get('ist')]
print(f'Biten maç: {len(biten)}\n')


def brier(p, y):
    return (p - y) ** 2


def logloss(p, y):
    p = min(max(p, 0.01), 0.99)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


# 1) Öneriler: beklenen isabet (model olasılıkları toplamı) ile gerçek
print('ÖNERİLER')
sev = defaultdict(lambda: [0, 0, 0.0])
grp = defaultdict(lambda: [0, 0, 0.0])
for m in biten:
    olan = {p['kod']: p['olan'] for p in m['model']['pazarlar']}
    for o in m['oneriler']:
        y = olan[o['kod']]
        if y is None:
            continue
        for tablo, k in ((sev, o['seviye']), (grp, o['grup'])):
            tablo[k][0] += y >= 0.5
            tablo[k][1] += 1
            tablo[k][2] += o['model']
for ad, tablo in (('seviye', sev), ('grup', grp)):
    for k, (t, n, b) in sorted(tablo.items()):
        print(f'  {ad:7} {k:15} tuttu {t}/{n}  beklenen {b:.1f}')
print(f"  skor (1. sıradaki skor) {sum(m['sonuc']['isabet']['skor'] for m in biten)}/{len(biten)}\n")

# 2) Tüm ikili pazarlar: model, piyasa, son 10, puan hangisi daha isabetli?
print('TÜM PAZARLAR (elenmeyenler, iadeler hariç): düşük = iyi')
acc = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0]))
for m in biten:
    for p in m['model']['pazarlar']:
        y = p['olan']
        if p['elendi'] or y is None or p['kod'].startswith('AH') and y not in (0, 1):
            continue
        for kaynak in ('model', 'piyasa', 'gecmis', 'puan'):
            v = p[kaynak]
            if v is None:
                continue
            for g in ('Tümü', p['grup']):
                a = acc[g][kaynak]
                a[0] += brier(v, y)
                a[1] += logloss(v, y)
                a[2] += 1
for g, ks in acc.items():
    satir = '  '.join(f'{k} {a[0] / a[2]:.3f}' for k, a in ks.items())
    print(f'  {g:15} n={ks["model"][2]:3}  Brier: {satir}')
print()

# 3) Beklenen gol: veri / piyasa / kullanılan, gerçek gol ve xG ile
print('BEKLENEN GOL (takım başına)')
hata = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
xgli = [m for m in biten if 'xg' in m['sonuc']['ist']]  # alt liglerde xG yok
for m in xgli:
    s, md = m['sonuc'], m['model']
    gol = [int(x) for x in s['skor'].split('-')]
    xg = s['ist']['xg']
    print(f"  {m['ev']['ad'][:14]:14} {s['skor']:>4}  xG {xg[0]:.2f}-{xg[1]:.2f}  veri {md['veri_l'][0]:.2f}-{md['veri_l'][1]:.2f}"
          f"  piyasa {md['piyasa_l'][0]:.2f}-{md['piyasa_l'][1]:.2f}  kullanılan {md['lambda'][0]:.2f}-{md['lambda'][1]:.2f}")
    for k in ('veri_l', 'piyasa_l', 'lambda', 'taban'):
        for i in range(2):
            h = hata[k]
            h[0] += abs(md[k][i] - xg[i])
            h[1] += md[k][i] - xg[i]
            h[2] += abs(md[k][i] - gol[i])
            h[3] += md[k][i] - gol[i]
n = 2 * len(xgli)
for k, h in hata.items():
    print(f'  {k:9} xG\'ye göre ort. hata {h[0] / n:.2f} (yön {h[1] / n:+.2f})   gole göre {h[2] / n:.2f} (yön {h[3] / n:+.2f})')
tg = sum(sum(int(x) for x in m['sonuc']['skor'].split('-')) for m in xgli)
txg = sum(sum(m['sonuc']['ist']['xg']) for m in xgli)
tl = sum(sum(m['model']['lambda']) for m in xgli)
print(f'  toplam: gol {tg}, xG {txg:.1f}, beklenen {tl:.1f}\n')

# 4) Korner ve kart
print('KORNER / KART: beklenen - olan')
for k in ('korner', 'kart'):
    fark = [m['model'][k] - sum(m['sonuc']['ist'][k]) for m in biten]
    print(f"  {k:6} " + '  '.join(f'{x:+.1f}' for x in fark) + f'   ortalama {sum(fark) / len(fark):+.2f}')
print()

# 5) Muhtemel 11 isabeti
print('İLK 11: tahmindeki oyunculardan kaçı başladı (listede verisi olmayan oyuncu sayılmaz)')
for m in biten:
    s = m['sonuc']['ilk11']
    out = []
    for t in ('ev', 'dep'):
        tahmin = {p['ad'] for p in m[t]['oyuncular'] if p['ilk11']}
        gercek = {a for a, _ in s[t]}
        out.append(f"{m[t]['ad'][:12]} {len(tahmin & gercek)}/{len(tahmin)}")
    print(f"  {'kesin' if m['kadro']['kesin'] else 'muhtemel':8} " + '  '.join(out))
