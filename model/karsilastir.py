"""Model sürümlerini biten maçlarda kıyaslar.

Kullanım: python3 model/karsilastir.py [data/tahminler.json] [v1 v2 ...]
Not: az maçla bu bir sağlık kontrolüdür, ayar kanıtı değil.
"""
import copy, json, math, os, sys

sys.path.insert(0, os.path.dirname(__file__))
import model

yol = sys.argv[1] if len(sys.argv) > 1 else 'data/tahminler.json'
surumler = sys.argv[2:] or ['v1', 'v2']
biten = [m for m in json.load(open(yol))['maclar'] if m.get('sonuc') and m['sonuc'].get('ist')]


def ll(p, y):
    p = min(max(p, 0.01), 0.99)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


for s in surumler:
    br = lg = n = 0.0
    grup = {}
    tut = say = 0
    bek = 0.0
    sec = []
    for m0 in biten:
        m = model.hesapla(copy.deepcopy(m0), s)
        olan = {x['kod']: x['olan'] for x in m0['model']['pazarlar']}
        for x in m['model']['pazarlar']:
            y = olan[x['kod']]
            if x['elendi'] or y not in (0, 1):
                continue
            br += (x['model'] - y) ** 2
            lg += ll(x['model'], y)
            n += 1
            g = grup.setdefault(x['grup'], [0.0, 0])
            g[0] += (x['model'] - y) ** 2
            g[1] += 1
        for o in m['oneriler']:
            y = olan[o['kod']]
            if y is None:
                continue
            say += 1
            tut += y >= 0.5
            bek += o['model']
            sec.append(f"{o['kod']}{'✓' if y >= 0.5 else '✗'}")
    print(f'{s}: Brier {br / n:.4f}  log {lg / n:.4f}  (n={int(n)})')
    print('    ' + '  '.join(f'{k} {v[0] / v[1]:.3f}' for k, v in grup.items()))
    print(f'    öneri {tut}/{say} (beklenen {bek:.1f}): ' + ' '.join(sec))
