"""Günün önerilerinden 2'li ve 3'lü kombin kurar; data/tahminler.json'da kombinler[<gün>] olarak saklar.

Kullanım: python3 model/kombin.py <gün> [--kuru]   (ör. 2026-11-03)
Ayaklar yalnız Güçlü önerilerden ve farklı maçlardan; kaybetmeme olasılığı (model) en yüksek olanlar önce.
Maçlar bağımsız sayılır. Beraberlikte iade ayağı berabere biterse oranı 1 olur.
Sonuç ayrıca işlenmez: site ayakların durumunu maçların sonuc.isabet kaydından okur.
"""
import json, math, os, sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOYUT = (2, 3)


def ayak(m, o):
    """Ayağın tutma ve iade olasılığı, model ve piyasa için ayrı."""
    P = {x['kod']: x for x in m['model']['pazarlar']}
    out = {}
    for k in ('model', 'piyasa'):
        if o['kod'].startswith('DNB'):  # model/piyasa değeri beraberlik hariç; beraberlik iade
            x = P['MSX'][k]
            out[k] = (o[k] * (1 - x), x)
        else:
            out[k] = (o[k], 0.0)
    return {
        'id': m['id'], 'kod': o['kod'], 'ad': o['ad'], 'oran': o['oran'], 'saat': m['saat'],
        'mac': f"{m['ev']['ad']} – {m['dep']['ad']}", '_p': out,
    }


def kupon(ayaklar):
    k = {'ayaklar': [{a: v for a, v in x.items() if a != '_p'} for x in ayaklar],
         'oran': round(math.prod(x['oran'] for x in ayaklar), 2)}
    for t in ('model', 'piyasa'):
        p = [x['_p'][t] for x in ayaklar]
        k[t] = {
            'tam': round(math.prod(w for w, _ in p), 3),              # hepsi tutar, tam oran
            'kaybetmez': round(math.prod(w + i for w, i in p), 3),    # hiçbiri yatmaz (iade dahil)
            'getiri': round(math.prod(w * x['oran'] + i for (w, i), x in zip(p, ayaklar)) - 1, 3),
        }
    return k


def kur(maclar):
    adaylar = [ayak(m, o) for m in maclar for o in m['oneriler'] if o['seviye'] == 'Güçlü']
    adaylar.sort(key=lambda x: -sum(x['_p']['model']))
    return [dict(ad=f"{n}'{'li' if n == 2 else 'lü'}", **kupon(adaylar[:n])) for n in BOYUT if len(adaylar) >= n]


if __name__ == '__main__':
    gun = sys.argv[1]
    yol = os.path.join(KOK, 'data', 'tahminler.json')
    d = json.load(open(yol))
    kl = kur(sorted((m for m in d['maclar'] if m['tarih'] == gun), key=lambda m: m['saat']))
    for k in kl:
        print(f"{k['ad']} oran {k['oran']}  model {k['model']}  piyasa {k['piyasa']}")
        for a in k['ayaklar']:
            print(f"   {a['saat']} {a['mac']}: {a['ad']} @ {a['oran']}")
    if '--kuru' not in sys.argv:
        d.setdefault('kombinler', {})[gun] = kl
        open(yol, 'w').write(json.dumps(d, ensure_ascii=False, separators=(',', ':')))
