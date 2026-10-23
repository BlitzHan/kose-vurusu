"""Ham veriden (ham/<id>.json) site kaydı üretir ve data/tahminler.json'a ekler ya da günceller.

Kullanım: python3 model/analiz.py <id> [<id> ...] [--surum v2] [--kuru]
Başlık ve özet metni elle yazılır: kayıt varsa korunur, yoksa boş kalır.
"""
import json, math, os, statistics as st, sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
import model
import sonuc as S

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSI = timezone(timedelta(hours=3))

TURNUVA = {
    'UEFA Champions League': 'Şampiyonlar Ligi', 'UEFA Europa League': 'Avrupa Ligi',
    'UEFA Conference League': 'Konferans Ligi', 'Trendyol Süper Lig': 'Süper Lig', 'Süper Lig': 'Süper Lig',
    'Türkiye Kupası': 'Türkiye Kupası', 'Scottish Premiership': 'İskoçya Ligi', 'Scottish League Cup': 'İskoçya Lig Kupası',
    'Scottish Cup': 'İskoçya Kupası', 'EFL Cup': 'Lig Kupası', 'FA Cup': 'FA Kupası', 'DFB Pokal': 'Almanya Kupası',
    'Coppa Italia': 'İtalya Kupası', 'Copa del Rey': 'İspanya Kupası', 'Premiership': 'İskoçya Ligi',
    'Premier League': 'Premier League', 'Ukrainian Premier League': 'Ukrayna Ligi',
}
AVRUPA_KISA = {'Şampiyonlar Ligi': 'ŞL', 'Avrupa Ligi': 'AL', 'Konferans Ligi': 'KL'}
LIG_MAC = {'Şampiyonlar Ligi': 8, 'Avrupa Ligi': 8, 'Konferans Ligi': 6}
AD = {'Beşiktaş JK': 'Beşiktaş', 'Heart of Midlothian': 'Hearts', 'Galatasaray A.Ş.': 'Galatasaray', 'Fenerbahçe SK': 'Fenerbahçe'}
MEVKI = {'G': 'G', 'D': 'D', 'M': 'M', 'F': 'F'}


def tr(ad):
    return TURNUVA.get(ad, ad)


def ondalik(fr):
    a, b = fr.split('/')
    return round(int(a) / int(b) + 1, 3)


# ---------------------------------------------------------------- son maçlar
def satir(m):
    biz, ra = (0, 1) if m['evde'] else (1, 0)
    ist = m['ist'] or {}
    v = lambda k, i: (ist.get(k) or [None, None])[i]
    kart = lambda i: None if v('sari', i) is None else v('sari', i) + (v('kirmizi', i) or 0)
    rey = [p['r'] for p in (m['kadro'] or {}).get('oyuncular', []) if not p['yedek'] and p['r']]
    rakip = m['dep'] if m['evde'] else m['ev']
    return {
        'tarih': datetime.fromtimestamp(m['ts'], TSI).strftime('%Y-%m-%d'),
        'rakip': AD.get(rakip['ad'], rakip['ad']), 'evde': m['evde'],
        'at': m['skor'][biz], 'ye': m['skor'][ra],
        'iy_at': m['iy'][biz] if m['iy'] else None, 'iy_ye': m['iy'][ra] if m['iy'] else None,
        'xg_l': v('xg', biz), 'xg_a': v('xg', ra), 'isabetli_l': v('isabetli', biz), 'isabetli_a': v('isabetli', ra),
        'buyuk_l': v('buyuk', biz), 'buyuk_a': v('buyuk', ra), 'ceza_l': v('ceza', biz), 'ceza_a': v('ceza', ra),
        'korner_l': v('korner', biz), 'korner_a': v('korner', ra), 'kart_l': kart(biz), 'kart_a': kart(ra),
        'topa_l': v('topa', biz), 'ilk11_reyting': round(st.mean(rey), 2) if rey else None,
        'turnuva': tr(m['ut_ad']),
        '_ilk_gol': {'biz': 'biz', 'rakip': 'rakip'}.get(m['ilk_gol'], m['ilk_gol']),
    }


# ---------------------------------------------------------------- oyuncular
def oyuncular(ham_maclar, bugun, eksik_id):
    P = {}
    for m in ham_maclar:  # yeniden eskiye
        for p in (m['kadro'] or {}).get('oyuncular', []):
            if not p['r']:
                continue
            o = P.setdefault(p['id'], {'id': p['id'], 'ad': p['ad'], 'mevki': MEVKI.get(p['mevki'], ''), 'r': [], 'g': 0, 'a': 0})
            o['r'].append(p['r'])
            o['g'] += p['g']
            o['a'] += p['a']
    ilk = {p['id'] for p in bugun['oyuncular'] if not p['yedek']} if bugun else set()
    liste = []
    for o in P.values():
        son = o['r'][:5]
        w = [0.8 ** i for i in range(len(son))]
        liste.append({
            'ad': o['ad'], 'mevki': o['mevki'], 'son': son,
            'form': round(sum(a * b for a, b in zip(son, w)) / sum(w), 2), 'ort': round(st.mean(o['r']), 2),
            'mac': len(o['r']), 'gol': o['g'], 'asist': o['a'],
            'yok': o['id'] in eksik_id, 'ilk11': o['id'] in ilk, '_id': o['id'],
        })
    xi = sorted([o for o in liste if o['ilk11']], key=lambda o: -o['form'])
    yok = [o for o in liste if o['yok'] and not o['ilk11']]
    diger = sorted([o for o in liste if not o['ilk11'] and not o['yok'] and o['mac'] >= 3], key=lambda o: -o['mac'])[:max(0, 20 - len(xi) - len(yok))]
    diger = sorted(yok + diger, key=lambda o: -o['form'])
    bilinmeyen = len(ilk - {o['_id'] for o in xi})
    for o in xi + diger:
        o.pop('_id')
    return xi + diger, bilinmeyen


# ---------------------------------------------------------------- pazarlar
def pazarlar(oranlar, ev, dep):
    """Oranları kodlu pazarlara çevirir; piyasa olasılığı marjı orantılı atılarak bulunur."""
    out = []

    def ekle(grup, secenekler):  # [(kod, ad, oran)]
        top = sum(1 / o for _, _, o in secenekler)
        hedef = 2 if grup == 'CIFT' else 1
        for kod, ad, o in secenekler:
            out.append({'kod': kod, 'ad': ad, 'oran': o, 'piyasa': round((1 / o) / top * hedef, 3)})

    for p in oranlar or []:
        c = {n: ondalik(f) for n, f in p['secenekler']}
        ad, g = p['pazar'], p['grup']
        if ad == 'Full time':
            ekle('MS', [('MS1', f'{ev} kazanır', c['1']), ('MSX', 'Beraberlik', c['X']), ('MS2', f'{dep} kazanır', c['2'])])
        elif ad == 'Double chance':
            ekle('CIFT', [('CS1X', f'{ev} kaybetmez', c['1X']), ('CSX2', f'{dep} kaybetmez', c['X2']), ('CS12', 'Beraberlik olmaz', c['12'])])
        elif ad == '1st half':
            ekle('IY', [('IY1', f'İlk yarı {ev}', c['1']), ('IYX', 'İlk yarı beraberlik', c['X']), ('IY2', f'İlk yarı {dep}', c['2'])])
        elif ad == 'Draw no bet':
            ekle('DNB', [('DNB1', f'{ev} kazanır (iade)', c['1']), ('DNB2', f'{dep} kazanır (iade)', c['2'])])
        elif ad == 'Both teams to score':
            ekle('KG', [('KGV', 'Karşılıklı gol var', c['Yes']), ('KGY', 'Karşılıklı gol yok', c['No'])])
        elif ad == 'Match goals':
            t = str(g).replace('.', ',')
            ekle('G', [(f'GOLU{g}', f'{t} gol üst', c['Over']), (f'GOLA{g}', f'{t} gol alt', c['Under'])])
        elif ad == 'Asian handicap':
            (n1, o1), (n2, o2) = p['secenekler']
            h1 = float(n1.split(')')[0].strip('('))
            fmt = lambda h: ('+' if h > 0 else '') + (str(int(h)) if h == int(h) else str(h)).replace('.', ',')
            k = lambda h: ('+' if h > 0 else '') + (str(int(h)) if h == int(h) else str(h))
            ekle('AH', [(f'AH1{k(h1)}', f'{ev} {fmt(h1)} handikap', ondalik(o1)), (f'AH2{k(-h1)}', f'{dep} {fmt(-h1)} handikap', ondalik(o2))])
        elif ad == 'Cards in match':
            t = str(g).replace('.', ',')
            ekle('K', [(f'KARTU{g}', f'Kart {t} üst', c['Over']), (f'KARTA{g}', f'Kart {t} alt', c['Under'])])
        elif ad == 'Corners 2-Way':
            t = str(g).replace('.', ',')
            ekle('KR', [(f'KORU{g}', f'Korner {t} üst', c['Over']), (f'KORA{g}', f'Korner {t} alt', c['Under'])])
        elif ad == 'First team to score':
            n = [x for x, _ in p['secenekler']]
            evk = next(x for x in n if x not in ('No goal',) and x == n[0])
            ekle('ILK', [('ILK1', f'İlk golü {ev} atar', c[evk]), ('ILKYOK', 'Gol olmaz', c['No goal']), ('ILK2', f'İlk golü {dep} atar', c[n[-1]])])
    GRUP = {'MS': 'Maç sonucu', 'CS': 'Maç sonucu', 'DN': 'Maç sonucu', 'AH': 'Maç sonucu', 'IY': 'İlk yarı', 'KG': 'Karşılıklı gol',
            'GO': 'Toplam gol', 'KA': 'Kart', 'KO': 'Korner', 'IL': 'İlk gol'}
    for x in out:
        x['grup'] = GRUP[x['kod'][:2]]
    return out


def gecmis(kod, ev_satir, dep_satir):
    """Son maçlarda bu pazar kaç kez gerçekleşti: ev takımı ev sahibi, deplasman takımı deplasman gibi okunur."""
    def bak(satirlar, evmi):
        t = n = 0
        for x in satirlar:
            if kod.startswith('KOR') and x['korner_l'] is None or kod.startswith('KART') and x['kart_l'] is None:
                continue
            if kod.startswith('IY') and x['iy_at'] is None or kod.startswith('ILK') and x['_ilk_gol'] == '?':
                continue
            a, b = (x['at'], x['ye']) if evmi else (x['ye'], x['at'])
            ia, ib = (x['iy_at'], x['iy_ye']) if evmi else (x['iy_ye'], x['iy_at'])
            ilk = None if x['_ilk_gol'] is None else ('ev' if (x['_ilk_gol'] == 'biz') == evmi else 'dep')
            s = {'skor': [a, b], 'iy': [ia, ib], 'ilk_gol': ilk,
                 'ist': {'korner': [x['korner_l'] or 0, x['korner_a'] or 0], 'kart': [x['kart_l'] or 0, x['kart_a'] or 0]}}
            r = S.coz(kod, s)
            if r is None:
                continue
            n += 1
            t += r >= 0.5
        return [float(t), n]
    e, d = bak(ev_satir, True), bak(dep_satir, False)
    oran = [x[0] / x[1] for x in (e, d) if x[1]]
    return (round(sum(oran) / len(oran), 3) if oran else None), e, d


# ---------------------------------------------------------------- puan durumu
def tablo_satiri(tablolar, takim_id):
    for t in tablolar or []:
        for r in t['satirlar']:
            if r['id'] == takim_id:
                return r, t['satirlar']
    return None, None


def onem(h, taraf, avrupa_ad):
    tid = h['mac'][taraf]['id']
    o = {}
    r, _ = tablo_satiri(h['puan']['avrupa'], tid)
    if r:
        o['avrupa'] = {'ad': AVRUPA_KISA.get(avrupa_ad, avrupa_ad), 'sira': r['sira'], 'puan': r['puan'], 'oynanan': r['oynanan']}
    lig = h['puan'][taraf]
    if lig:
        r2, satirlar = tablo_satiri(lig['tablolar'], tid)
        if r2:
            o['lig'] = {'ad': tr(lig['lig']['ad']), 'sira': r2['sira'], 'puan': r2['puan'], 'oynanan': r2['oynanan'],
                        'lider_fark': max(x['puan'] for x in satirlar) - r2['puan']}
    seviye, metin = 'normal', ''
    if r:
        if r['oynanan'] >= 2 and r['puan'] == 0:
            seviye, metin = 'yüksek', 'Puanı yok; kaybederse ilk 24 yolu daralır.'
        elif r['sira'] <= 8:
            metin = "İlk 8'de; kazanırsa son 16'ya doğrudan çıkma yolunda öne geçer."
        elif r['sira'] <= 24:
            metin = "Play-off bölgesinde; galibiyet ilk 8'e yaklaştırır."
        else:
            seviye, metin = 'yüksek', "İlk 24'ün dışında; puan kaybı riskli."
    o.update(metin=metin, seviye=seviye, carpan=1.0)
    return o


# ---------------------------------------------------------------- maç kaydı
def kayit(h, eski=None, surum='v3'):
    mac = h['mac']
    ev, dep = AD.get(mac['ev']['ad'], mac['ev']['ad']), AD.get(mac['dep']['ad'], mac['dep']['ad'])
    avrupa = tr(mac['ut_ad'])
    t = datetime.fromtimestamp(mac['ts'], TSI)
    kd = h['kadro'] or {}
    takim = {}
    for s in ('ev', 'dep'):
        bugun = kd.get(s)
        eksik_id = {x['id'] for x in (bugun or {}).get('eksik', []) if x['tur'] == 'missing'}
        satirlar = [satir(m) for m in h[s]]
        oy, bilinmeyen = oyuncular(h[s], bugun, eksik_id)
        lig = tr(h['puan'][s]['lig']['ad']) if h['puan'].get(s) else None
        takim[s] = dict(ad=ev if s == 'ev' else dep, satirlar=satirlar, oyuncular=oy, bilinmeyen=bilinmeyen, lig=lig,
                        eksik=[x['ad'] for x in (bugun or {}).get('eksik', []) if x['tur'] == 'missing'],
                        dizilis=(bugun or {}).get('dizilis'))
    # oyuncu formu
    form = {}
    for s, T in takim.items():
        rey = [x['ilk11_reyting'] for x in T['satirlar'] if x['ilk11_reyting']]
        tb = st.mean(rey) if rey else 6.9
        xi = [o['form'] for o in T['oyuncular'] if o['ilk11']]
        f = st.mean(xi + [tb] * T['bilinmeyen']) if xi else tb
        at = sum(x['at'] for x in T['satirlar'])
        ga = sum(o['gol'] + o['asist'] for o in T['oyuncular'] if o['yok'])
        form[s] = {'form': round(f, 2), 'taban': round(tb, 2), 'fark': round(f - tb, 2), 'eksik_payi': round(ga / at, 2) if at else 0}
    # pazarlar
    pz = pazarlar(h['oranlar'], ev, dep)
    for x in pz:
        g, ge, gd = gecmis(x['kod'], takim['ev']['satirlar'], takim['dep']['satirlar'])
        x.update(gecmis=g, gecmis_ev=ge, gecmis_dep=gd, elendi=x['oran'] < 1.35 or x['oran'] > 3.5, model=0, puan=0, deger=0, seviye=None)
    P = {x['kod']: x['piyasa'] for x in pz}
    piyasa_l = model.piyasa_lambda(P['MS1'], P['MSX'], P['MS2'], P['GOLU2.5']) if 'GOLU2.5' in P else None
    ort = lambda T, k: st.mean([x[k + '_l'] + x[k + '_a'] for x in T['satirlar'] if x[k + '_l'] is not None])
    ham = {k: round((ort(takim['ev'], k) + ort(takim['dep'], k)) / 2, 2) for k in ('korner', 'kart')}
    m = {
        'id': f"{t:%Y-%m-%d}-{slug(ev)}-{slug(dep)}", 'kaynak_id': mac['id'], 'tarih': f'{t:%Y-%m-%d}', 'saat': f'{t:%H:%M}',
        'turnuva': f"{avrupa} · {mac['tur']['round']}. hafta" if mac.get('tur') and mac['tur'].get('round') else avrupa,
        'stad': mac['stad'], 'yayin': None, 'manset': False, 'baslik': '', 'ozet': '', 'sinyal': None, 'oran_min': 1.35,
        'ev': {'ad': ev, 'maclar': [], 'oyuncular': takim['ev']['oyuncular']},
        'dep': {'ad': dep, 'maclar': [], 'oyuncular': takim['dep']['oyuncular']},
        'kadro': {'kesin': bool(kd.get('kesin')),
                  'ev': {'dizilis': takim['ev']['dizilis'], 'eksik': takim['ev']['eksik']},
                  'dep': {'dizilis': takim['dep']['dizilis'], 'eksik': takim['dep']['eksik']}},
        'model': {'lambda': None, 'taban': model.taban(takim['ev']['satirlar'], takim['ev']['lig'], takim['dep']['satirlar'], takim['dep']['lig']),
                  'veri_l': None, 'piyasa_l': piyasa_l, 'carpan': None, 'kart': ham['kart'], 'korner': ham['korner'],
                  'form': form, 'pazarlar': pz},
        'oneriler': [],
        'onem': {'tur': mac['tur']['round'] if mac.get('tur') else None, 'lig_mac': LIG_MAC.get(avrupa),
                 'ev': onem(h, 'ev', avrupa), 'dep': onem(h, 'dep', avrupa)},
        'veri_tarihi': datetime.fromisoformat(h['alindi'].replace('Z', '+00:00')).astimezone(TSI).strftime('%d.%m.%Y %H:%M'),
        'sonuc': None,
    }
    for s in ('ev', 'dep'):
        m[s]['maclar'] = [{k: v for k, v in x.items() if not k.startswith('_')} for x in takim[s]['satirlar']]
        m['model']['form'][s]['bilinmeyen'] = takim[s]['bilinmeyen']
    model.hesapla(m, surum, ham=ham)
    for s in ('ev', 'dep'):
        m['model']['form'][s].pop('bilinmeyen')
    if eski:
        for k in ('baslik', 'ozet', 'yayin', 'manset'):
            m[k] = eski.get(k, m[k])
    return m


def slug(ad):
    t = str.maketrans('çğıöşüÇĞİÖŞÜâéáíóú', 'cgiosuCGIOSUaeaiou')
    return '-'.join(''.join(c for c in w if c.isalnum()) for w in ad.translate(t).lower().split())


if __name__ == '__main__':
    argv = [a for a in sys.argv[1:] if not a.startswith('--')]
    surum = sys.argv[sys.argv.index('--surum') + 1] if '--surum' in sys.argv else 'v3'
    argv = [a for a in argv if a != surum]
    yol = os.path.join(KOK, 'data', 'tahminler.json')
    d = json.load(open(yol))
    for i in argv:
        h = json.load(open(os.path.join(KOK, 'ham', f'{i}.json')))
        eski = next((x for x in d['maclar'] if x['kaynak_id'] == int(i)), None)
        m = kayit(h, eski, surum)
        if eski:
            d['maclar'][d['maclar'].index(eski)] = m
        else:
            d['maclar'].append(m)
        md = m['model']
        print(f"== {m['id']} {m['saat']}  kadro {'kesin' if m['kadro']['kesin'] else 'muhtemel'}")
        print(f"   taban {md['taban']}  veri {md['veri_l']}  piyasa {md['piyasa_l']}  kullanılan {md['lambda']}  korner {md['korner']} kart {md['kart']}")
        print(f"   form {md['form']}")
        print(f"   öneriler {[(o['kod'], o['seviye'], o['oran'], o['model'], o['gecmis'], o['piyasa'], o['puan']) for o in m['oneriler']]}")
        print(f"   skorlar {md['skorlar'][:3]}")
    d['guncelleme'] = datetime.now(TSI).strftime('%Y-%m-%d %H:%M')
    if '--kuru' not in sys.argv:
        open(yol, 'w').write(json.dumps(d, ensure_ascii=False, separators=(',', ':')))
