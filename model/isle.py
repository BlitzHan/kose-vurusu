"""Biten maçın ham sonucunu (ham/<id>-sonuc.json) data/tahminler.json kaydına işler.

Kullanım: python3 model/isle.py <id> [<id> ...]
         python3 model/isle.py --kapanis [<id> ...]   (yalnız ham/<id>-kapanis.json'daki kapanış oranlarını yazar; id yoksa hepsi)
Tahminlere dokunmaz; yalnız `sonuc` alanını, pazarların `olan` değerini ve kapanış oranını (`kapanis`) yazar.
Kart: gösterilen kart sayısı (sarı + kırmızı; ikinci sarıdan kırmızı ayrıca sayılır).
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(__file__))
import sonuc as S
from analiz import pazarlar

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALAN = ('xg', 'sut', 'isabetli', 'buyuk', 'ceza', 'korner', 'topa')


def ist(r):
    i = r['ist']
    o = {k: i[k] for k in ALAN if k in i}
    o['kart'] = [(i.get('sari') or [0, 0])[t] + (i.get('kirmizi') or [0, 0])[t] for t in range(2)]
    return o


def kapanis(m, oranlar):
    """Maç bitince çekilen son oranlar kapanış sayılır; pazarlara ve önerilere yazılır (çizgi kaydıysa None)."""
    kap = {}
    for pz in oranlar:  # bitmiş maçta bazı seçenekler eksik dönebilir; o pazar atlanır
        try:
            kap.update({x['kod']: x['oran'] for x in pazarlar([pz], '', '')})
        except (KeyError, ValueError, ZeroDivisionError, StopIteration):
            pass
    for p in m['model']['pazarlar']:
        p['kapanis'] = kap.get(p['kod'])
    if m.get('sonuc'):
        for o in m['sonuc']['isabet']['oneriler']:
            o['kapanis'] = kap.get(o['kod'])
    return m


def isle(m, r):
    taraf = lambda o: 'ev' if o['ev'] else 'dep'
    olay = sorted([o for o in r['olaylar'] if o['dk'] is not None and o['dk'] >= 0], key=lambda o: o['dk'])
    goller = [o for o in olay if o['tur'] == 'goal']
    kirmizi = [o for o in olay if o['tur'] == 'card' and o['sinif'] in ('red', 'yellowRed')]
    s = {'skor': r['mac']['skor'], 'iy': r['mac']['iy'], 'ist': ist(r), 'ilk_gol': taraf(goller[0]) if goller else None}
    for p in m['model']['pazarlar']:
        p['olan'] = S.coz(p['kod'], s)
    olan = {p['kod']: p['olan'] for p in m['model']['pazarlar']}
    skor = '-'.join(map(str, s['skor']))
    ad = lambda o: o['oyuncu'] + (' (pen.)' if o['sinif'] == 'penalty' else ' (k.k.)' if o['sinif'] == 'ownGoal' else '')
    m['sonuc'] = {
        'skor': skor, 'iy': '-'.join(map(str, s['iy'])), 'ist': s['ist'],
        'goller': [{'dk': o['dk'], 'taraf': taraf(o), 'oyuncu': ad(o)} for o in goller],
        'kirmizi': [{'dk': o['dk'], 'taraf': taraf(o), 'oyuncu': o['oyuncu']} for o in kirmizi],
        'ilk11': {t: [[p['ad'], p['r']] for p in r['kadro'][t]['oyuncular'] if not p['yedek']] for t in ('ev', 'dep')},
        'isabet': {
            'oneriler': [{'kod': o['kod'], 'tuttu': None if olan[o['kod']] is None else olan[o['kod']] >= 0.5,
                          'iade': olan[o['kod']] is None} for o in m['oneriler']],
            'skor': m['model']['skorlar'][0][0] == skor,
        },
    }
    if r.get('oranlar'):
        kapanis(m, r['oranlar'])
    return m


if __name__ == '__main__':
    yol = os.path.join(KOK, 'data', 'tahminler.json')
    d = json.load(open(yol))
    if sys.argv[1:2] == ['--kapanis']:
        ham = os.path.join(KOK, 'ham')
        ids = sys.argv[2:] or [f.split('-')[0] for f in sorted(os.listdir(ham)) if f.endswith('-kapanis.json')]
        for i in ids:
            m = next(x for x in d['maclar'] if x['kaynak_id'] == int(i))
            kapanis(m, json.load(open(os.path.join(ham, f'{i}-kapanis.json')))['oranlar'])
            print(m['id'], [(o['kod'], o['oran'], o.get('kapanis')) for o in m['oneriler']])
        open(yol, 'w').write(json.dumps(d, ensure_ascii=False, separators=(',', ':')))
        sys.exit()
    for i in sys.argv[1:]:
        r = json.load(open(os.path.join(KOK, 'ham', f'{i}-sonuc.json')))
        if r['mac']['durum'] != 'finished':
            sys.exit(f'{i}: maç bitmemiş ({r["mac"]["durum"]})')
        m = next(x for x in d['maclar'] if x['kaynak_id'] == int(i))
        isle(m, r)
        print(m['id'], m['sonuc']['skor'], [(o['kod'], 'iade' if o['iade'] else o['tuttu']) for o in m['sonuc']['isabet']['oneriler']])
    open(yol, 'w').write(json.dumps(d, ensure_ascii=False, separators=(',', ':')))
