"""Köşe Vuruşu · Okuma 2: piyasayı yenmeye değil, maçı okumaya çalışır.

Bakış açısı (bkz. model/okuma-1.md, eşikler model/okuma-2.md):
- Oranlar binlerce kişinin ortak tahminidir ve 184 maçlık testte iyi kalibre çıktı
  (%70 dediği %74, %80 dediği %86 oldu). Takım verisinden kurulan hiçbir model bunu geçemedi.
  Bu yüzden olasılığın tabanı oranlardır; kesinti (marj) temizlenir, başka hiçbir şey eklenmez.
- Değerimiz olasılık uydurmak değil, okumak: her maça tam bir tahmin (kim kazanır, skor,
  gol, en güvenli seçim, cesur seçim, senaryolar) ve her seçimin arkasında son 10 maç kanıtı.
- Ölçü getiri değil isabet ve kalibrasyon: "%70" dediğimiz şeyler 10'da 7 tutmalı.

Kullanım:
  python3 model/okuma.py                 # tüm maçlar, data/tahminler.json'a yazar
  python3 model/okuma.py 2026-11-04      # yalnız o gün
  python3 model/okuma.py --test          # geriye dönük isabet testi (yazmaz)
"""
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOL = os.path.join(KOK, 'data', 'tahminler.json')
TSI = timezone(timedelta(hours=3))
SURUM = 'okuma-2'
N = 10            # skor matrisi boyu (0–9 gol)
RHO = -0.06       # Dixon-Coles: düşük skorlu beraberlik düzeltmesi
ORAN_MIN = 1.15   # okuma-2: 1,35 tabanı isabeti %70'e kilitliyordu (olasılık ≈ 0,96 / oran)
GUCLU = 0.75      # temizlenmiş olasılık eşiği; 193 maçta bu kuralla Güçlü ≈ %80 tuttu
ORTA = 0.66       # eski Güçlü bandı (%66–75) artık Orta


def _grup(kod):
    """Sinyal grubu; Asya handikabı ve 'beraberlik olmaz' bilgi taşımadığı için dışarıda."""
    for g, r in (('MS', r'(MS[12X]|CS1X|CSX2|DNB[12])$'), ('GOL', r'GOL[UA][\d.]+$'), ('KG', r'KG[VY]$'),
                 ('KOR', r'KOR[UA][\d.]+$'), ('KART', r'KART[UA][\d.]+$'), ('IY', r'IY[12X]$'), ('ILK', r'ILK[12]$')):
        if re.match(r, kod):
            return g
    return None


# ---------------------------------------------------------------- oranlardan adil olasılık
def kuvvet(oranlar):
    """Güç yöntemiyle marj temizleme: p_i = (1/o_i)^k, toplam 1. Favori-uzun oran yanlılığını
    orantılı yöntemden iyi düzeltir; Shin ile neredeyse aynı sonucu verir."""
    inv = [1 / o for o in oranlar]
    lo, hi = 1.0, 4.0
    for _ in range(60):
        k = (lo + hi) / 2
        if sum(x ** k for x in inv) > 1:
            lo = k
        else:
            hi = k
    return [x ** k for x in inv]


def adil(pazarlar):
    """Her pazar grubunu kendi içinde temizler. Dönen: {kod: olasılık}."""
    P = {p['kod']: p['oran'] for p in pazarlar if p.get('oran')}
    q = {}

    def grup(kodlar):
        if all(P.get(k) for k in kodlar):
            for k, v in zip(kodlar, kuvvet([P[k] for k in kodlar])):
                q[k] = v

    grup(['MS1', 'MSX', 'MS2'])
    grup(['IY1', 'IYX', 'IY2'])
    grup(['ILK1', 'ILKYOK', 'ILK2'])
    grup(['KGV', 'KGY'])
    for k in list(P):
        for on, karsi in (('GOLU', 'GOLA'), ('KORU', 'KORA'), ('KARTU', 'KARTA')):
            if k.startswith(on):
                grup([k, karsi + k[len(on):]])
    if 'MS1' in q:
        q['CS1X'] = q['MS1'] + q['MSX']
        q['CSX2'] = q['MS2'] + q['MSX']
        q['CS12'] = q['MS1'] + q['MS2']
        b = 1 - q['MSX']
        q['DNB1'] = q['MS1'] / b
        q['DNB2'] = q['MS2'] / b
    return q


# ---------------------------------------------------------------- skor matrisi
def _pois(k, l):
    return math.exp(-l) * l ** k / math.factorial(k)


def matris(l1, l2, rho=RHO):
    M = [[_pois(i, l1) * _pois(j, l2) for j in range(N)] for i in range(N)]
    M[0][0] *= 1 - l1 * l2 * rho
    M[0][1] *= 1 + l1 * rho
    M[1][0] *= 1 + l2 * rho
    M[1][1] *= 1 - rho
    s = sum(map(sum, M))
    return [[x / s for x in r] for r in M]


def _ozet(M):
    p1 = px = 0.0
    alt = {c: 0.0 for c in (0.5, 1.5, 2.5, 3.5, 4.5)}
    kg = 0.0
    for i in range(N):
        for j in range(N):
            v = M[i][j]
            if i > j:
                p1 += v
            elif i == j:
                px += v
            for c in alt:
                if i + j < c:
                    alt[c] += v
            if i and j:
                kg += v
    return p1, px, 1 - p1 - px, alt, kg


def uydur(q):
    """Oranların 1X2, gol çizgileri ve KG olasılıklarına en iyi uyan beklenen gol çifti.
    Kaba ızgara + ince ızgara; deterministik."""
    hedef = []
    for k, w in (('MS1', 1.0), ('MSX', 1.0), ('MS2', 1.0), ('KGV', 0.5)):
        if k in q:
            hedef.append((k, q[k], w))
    for c in (1.5, 2.5, 3.5):
        k = f'GOLA{c}'
        if k in q:
            hedef.append((k, q[k], 1.0 if c == 2.5 else 0.6))

    def hata(l1, l2):
        p1, px, p2, alt, kg = _ozet(matris(l1, l2))
        d = {'MS1': p1, 'MSX': px, 'MS2': p2, 'KGV': kg, 'GOLA1.5': alt[1.5], 'GOLA2.5': alt[2.5], 'GOLA3.5': alt[3.5]}
        return sum(w * (d[k] - v) ** 2 for k, v, w in hedef)

    en = (9, 1.3, 1.1)
    for a in range(20, 420, 10):
        for b in range(10, 380, 10):
            e = hata(a / 100, b / 100)
            if e < en[0]:
                en = (e, a / 100, b / 100)
    _, l1, l2 = en
    for a in range(-10, 11):
        for b in range(-10, 11):
            x, y = l1 + a / 100, l2 + b / 100
            if x > 0.05 and y > 0.05:
                e = hata(x, y)
                if e < en[0]:
                    en = (e, x, y)
    return round(en[1], 2), round(en[2], 2)


# ---------------------------------------------------------------- seçimler
def _ad(kod, ev, dep):
    sabit = {
        'MS1': f'{ev} kazanır', 'MSX': 'Beraberlik', 'MS2': f'{dep} kazanır',
        'CS1X': f'{ev} kaybetmez', 'CSX2': f'{dep} kaybetmez', 'CS12': 'Beraberlik olmaz',
        'DNB1': f'{ev} kazanır (berabere iade)', 'DNB2': f'{dep} kazanır (berabere iade)',
        'KGV': 'Karşılıklı gol var', 'KGY': 'Karşılıklı gol yok',
        'IY1': f'İlk yarı {ev}', 'IYX': 'İlk yarı berabere', 'IY2': f'İlk yarı {dep}',
        'ILK1': f'İlk golü {ev} atar', 'ILK2': f'İlk golü {dep} atar', 'ILKYOK': 'Gol olmaz',
    }
    if kod in sabit:
        return sabit[kod]
    m = re.match(r'(GOL|KOR|KART)([UA])([\d.]+)$', kod)
    if m:
        ne = {'GOL': 'gol', 'KOR': 'korner', 'KART': 'kart'}[m.group(1)]
        return f"{m.group(3).replace('.', ',')} {ne} {'üst' if m.group(2) == 'U' else 'alt'}"
    return kod


def _kanit(kod, mac, pz):
    """Seçimin arkasındaki son 10 maç sayımı ya da form; tek satır, sayıyla."""
    ev, dep = mac['ev'], mac['dep']
    p = pz.get(kod)
    kisa = lambda ad: ad if len(ad) <= 12 else ad.split()[-1] if len(ad.split()[-1]) > 2 else ad.split()[0]
    if kod in ('MS1', 'MS2', 'CS1X', 'CSX2', 'DNB1', 'DNB2', 'IY1', 'IY2', 'ILK1', 'ILK2'):
        def form(t):
            s = t['maclar'][:10]
            g = sum(x['at'] > x['ye'] for x in s)
            b = sum(x['at'] == x['ye'] for x in s)
            xg = [x['xg_l'] - x['xg_a'] for x in s[:5] if x.get('xg_l') is not None and x.get('xg_a') is not None]
            xs = f", son 5 xG farkı {'+' if sum(xg) >= 0 else '−'}{abs(sum(xg) / len(xg)):.1f}".replace('.', ',') if xg else ''
            return f"{kisa(t['ad'])} son {len(s)}: {g}G {b}B {len(s) - g - b}M{xs}"
        return f"{form(ev)} · {form(dep)}"
    if p and p.get('gecmis_ev') and p.get('gecmis_dep'):
        (a, n), (b, m) = p['gecmis_ev'], p['gecmis_dep']
        if n and m:
            return f"Son 10 maçta bu sonuç: {kisa(ev['ad'])} {a:g}/{n}, {kisa(dep['ad'])} {b:g}/{m}"
    return ''


SENARYO = [
    # (ad, koşul(i, j))
    ('ev_rahat', lambda i, j: i - j >= 2),
    ('ev_az', lambda i, j: i - j == 1),
    ('beraber', lambda i, j: i == j),
    ('dep_az', lambda i, j: j - i == 1),
    ('dep_rahat', lambda i, j: j - i >= 2),
]


def senaryolar(M, ev, dep):
    ad = {'ev_rahat': f'{ev} farklı kazanır', 'ev_az': f'{ev} tek farkla', 'beraber': 'Beraberlik',
          'dep_az': f'{dep} tek farkla', 'dep_rahat': f'{dep} farklı kazanır'}
    cik = []
    for k, f in SENARYO:
        p = sum(M[i][j] for i in range(N) for j in range(N) if f(i, j))
        en = max(((i, j) for i in range(N) for j in range(N) if f(i, j)), key=lambda t: M[t[0]][t[1]])
        cik.append({'kod': k, 'ad': ad[k], 'p': round(p, 4), 'skor': f'{en[0]}-{en[1]}'})
    return cik


def birlesik(M, ev, dep):
    """Aynı maçtan iki sonuç birden: olasılık skor matrisinden, ilişki hesaba katılır."""
    kosul = {
        'MS1+U2.5': (f'{ev} kazanır ve 2,5 üst', lambda i, j: i > j and i + j >= 3),
        'MS2+U2.5': (f'{dep} kazanır ve 2,5 üst', lambda i, j: j > i and i + j >= 3),
        'MS1+KGV': (f'{ev} kazanır, iki takım da atar', lambda i, j: i > j and j > 0),
        'MS2+KGV': (f'{dep} kazanır, iki takım da atar', lambda i, j: j > i and i > 0),
        'MS1+KGY': (f'{ev} gol yemeden kazanır', lambda i, j: i > j and j == 0),
        'MS2+KGY': (f'{dep} gol yemeden kazanır', lambda i, j: j > i and i == 0),
        'MSX+A2.5': ('Az gollü beraberlik', lambda i, j: i == j and i + j <= 2),
        'CS1X+A3.5': (f'{ev} kaybetmez ve 3,5 alt', lambda i, j: i >= j and i + j <= 3),
        'CSX2+A3.5': (f'{dep} kaybetmez ve 3,5 alt', lambda i, j: j >= i and i + j <= 3),
        'CS1X+KGV': (f'{ev} kaybetmez, iki takım da atar', lambda i, j: i >= j and j > 0),
        'CSX2+KGV': (f'{dep} kaybetmez, iki takım da atar', lambda i, j: j >= i and i > 0),
    }
    return {k: (ad, sum(M[i][j] for i in range(N) for j in range(N) if f(i, j))) for k, (ad, f) in kosul.items()}


def oku(mac):
    """Bir maç kaydından okuma bloğu. Girdi yalnız maç öncesi oranlar ve son maçlar."""
    pazarlar = mac['model']['pazarlar']
    pz = {p['kod']: p for p in pazarlar}
    q = adil(pazarlar)
    if not all(k in q for k in ('MS1', 'MSX', 'MS2')):
        return None
    ev, dep = mac['ev']['ad'], mac['dep']['ad']
    l1, l2 = uydur(q)
    M = matris(l1, l2)
    # Gol çizgileri ve KG için oranın kendisi matristen daha iyi (kuyruklar); matris yalnız eksikleri doldurur.
    p1, px, p2, alt, kg = _ozet(M)
    for c in (0.5, 1.5, 2.5, 3.5, 4.5):
        q.setdefault(f'GOLA{c}', alt[c])
        q.setdefault(f'GOLU{c}', 1 - alt[c])
    q.setdefault('KGV', kg)
    q.setdefault('KGY', 1 - kg)

    def secim(kod, p=None, tur=None):
        p = q[kod] if p is None else p
        o = pz.get(kod, {}).get('oran')
        return {'kod': kod, 'ad': _ad(kod, ev, dep), 'p': round(p, 4), 'oran': o,
                'kanit': _kanit(kod, mac, pz), **({'tur': tur} if tur else {})}

    # 1) Ana tahmin: kim kazanır. Favori %50'yi geçiyorsa düz, geçmiyorsa kaybetmez.
    fav = max(('MS1', 'MS2'), key=lambda k: q[k])
    if q[fav] >= 0.50:
        tahmin = secim(fav)
    elif q['MSX'] >= max(q['MS1'], q['MS2']):
        tahmin = secim('MSX')
    else:
        tahmin = secim('CS1X' if fav == 'MS1' else 'CSX2')
    guc = max(q['MS1'], q['MS2'])
    tahmin['guven'] = 'yüksek' if guc >= 0.65 else 'orta' if guc >= 0.48 else 'düşük'
    tahmin['surpriz'] = round(1 - q[fav], 4)   # favorinin kazanamama olasılığı

    # 2) Skor: tahminle aynı yöndeki en olası skor (beraberlikte en olası beraberlik)
    yon = {'MS1': lambda i, j: i > j, 'MS2': lambda i, j: j > i, 'MSX': lambda i, j: i == j,
           'CS1X': lambda i, j: i >= j, 'CSX2': lambda i, j: j >= i}[tahmin['kod']]
    hucre = sorted(((M[i][j], i, j) for i in range(N) for j in range(N)), reverse=True)
    sp, si, sj = next(h for h in hucre if yon(h[1], h[2]))
    skor = {'skor': f'{si}-{sj}', 'p': round(sp, 4)}
    skorlar = [[f'{i}-{j}', round(v, 4)] for v, i, j in hucre[:6]]

    # 3) Sinyaller: tüm pazarlar, oran ≥ 1,15, kota yok.
    #    Güçlü: oranlardan temizlenmiş olasılık ≥ %75 · Orta: %66–75. Her pazar grubundan en olası tek seçenek;
    #    aynı hikâyeyi anlatan ikili (2,5 üst + KG var, 2,5 alt + KG yok) tek sinyal sayılır.
    #    "Değerli fiyat": ikinci kaynağın oranıyla beklenen getiri artıdaysa (olasılık × en iyi oran ≥ 1).
    sinyaller, gorulen = [], set()
    adaylar = sorted(((q[k], k) for k in q if _grup(k) and pz.get(k, {}).get('oran', 0) >= ORAN_MIN), reverse=True)
    for p, k in adaylar:
        g = _grup(k)
        if g in gorulen or p < ORTA:
            continue
        if g == 'KG' and any(s['kod'] == {'KGV': 'GOLU2.5', 'KGY': 'GOLA2.5'}[k] for s in sinyaller):
            continue
        if g == 'GOL' and any(s['kod'] == {'GOLU2.5': 'KGV', 'GOLA2.5': 'KGY'}.get(k) for s in sinyaller):
            continue
        gorulen.add(g)
        s = secim(k)
        s['seviye'] = 'Güçlü' if p >= GUCLU else 'Orta'
        en_iyi = max(x for x in (pz[k].get('oran'), pz[k].get('oran_b')) if x)
        s['en_iyi'] = en_iyi
        s['deger'] = round(p * en_iyi - 1, 4)
        sinyaller.append(s)

    # 5) Cesur: oranı 2,00–3,60 arası tek sonuçlardan ve aynı maç ikililerinden en olası.
    #    İkililerin oranı yok; adil oran = 1 / olasılık olarak gösterilir.
    cesur_tek = re.compile(r'(MS[12X]|DNB[12]|GOL[UA][2-3]\.5|KG[VY]|IY[12X])$')
    cand = [(q[k], k, None) for k in q if cesur_tek.match(k) and 2.0 <= pz.get(k, {}).get('oran', 0) <= 3.6]
    for k, (ad, p) in birlesik(M, ev, dep).items():
        if 1 / 3.6 <= p <= 1 / 2.0:
            cand.append((p, k, ad))
    cesur = None
    if cand:
        p, k, ad = max(cand, key=lambda t: t[0])
        if ad is None:
            cesur = secim(k)
        else:
            cesur = {'kod': k, 'ad': ad, 'p': round(p, 4), 'oran': None, 'adil_oran': round(1 / p, 2), 'kanit': ''}

    return {
        'surum': SURUM,
        'lambda': [l1, l2],
        'olasilik': {k: round(v, 4) for k, v in sorted(q.items())},
        'tahmin': tahmin,
        'skor': skor,
        'skorlar': skorlar,
        'sinyaller': sinyaller,
        'cesur': cesur,
        'senaryolar': senaryolar(M, ev, dep),
        'matris': [[round(M[i][j], 4) for j in range(6)] for i in range(6)],
    }


# ---------------------------------------------------------------- kupon
def kupon(maclar):
    """Günün Güçlü sinyallerinden (maç başı en olası tek ayak) en olası 2'li ve 3'lü.
    Maçlar bağımsız sayılır; tutma olasılığı ayakların çarpımı."""
    ay = []
    for m in maclar:
        g = [s for s in (m.get('okuma') or {}).get('sinyaller', []) if s['seviye'] == 'Güçlü' and s.get('oran')]
        if g:
            s = max(g, key=lambda x: x['p'])
            ay.append({'id': m['id'], 'mac': f"{m['ev']['ad']} – {m['dep']['ad']}", 'saat': m['saat'],
                       'kod': s['kod'], 'ad': s['ad'], 'oran': s['oran'], 'p': s['p']})
    ay.sort(key=lambda a: -a['p'])
    cik = []
    for n in (2, 3):
        if len(ay) >= n:
            s = ay[:n]
            cik.append({'ad': f"{n}'li", 'ayaklar': s, 'oran': round(math.prod(a['oran'] for a in s), 2),
                        'p': round(math.prod(a['p'] for a in s), 4)})
    return cik


# ---------------------------------------------------------------- isabet
def _olan(m, kod):
    """Sonuç kaydından seçimin tutup tutmadığı: 1, 0 ya da None (bilinmiyor / iade)."""
    s = m.get('sonuc') or {}
    if not s.get('skor'):
        return None
    i, j = map(int, s['skor'].split('-'))
    p = next((x for x in m['model']['pazarlar'] if x['kod'] == kod), None)
    if p is not None and p.get('olan') in (0, 1):
        return p['olan']
    kural = {
        'MS1': i > j, 'MSX': i == j, 'MS2': j > i, 'CS1X': i >= j, 'CSX2': j >= i, 'CS12': i != j,
        'DNB1': None if i == j else i > j, 'DNB2': None if i == j else j > i,
        'KGV': i > 0 and j > 0, 'KGY': not (i > 0 and j > 0),
    }
    if kod in kural:
        v = kural[kod]
        return None if v is None else int(v)
    g = re.match(r'GOL([UA])([\d.]+)$', kod)
    if g:
        c = float(g.group(2))
        return int(i + j > c) if g.group(1) == 'U' else int(i + j < c)
    for k, f in [(k, f) for k, f in [
        ('MS1+U2.5', i > j and i + j >= 3), ('MS2+U2.5', j > i and i + j >= 3),
        ('MS1+KGV', i > j and j > 0), ('MS2+KGV', j > i and i > 0),
        ('MS1+KGY', i > j and j == 0), ('MS2+KGY', j > i and i == 0),
        ('MSX+A2.5', i == j and i + j <= 2), ('CS1X+A3.5', i >= j and i + j <= 3),
        ('CSX2+A3.5', j >= i and i + j <= 3), ('CS1X+KGV', i >= j and j > 0), ('CSX2+KGV', j >= i and i > 0)]]:
        if kod == k:
            return int(f)
    return None


def test(maclar):
    """Isabet, 1 TL kasası ve kalibrasyon. Beklenen kasa: her sinyalde olasılık × oran − 1;
    gerçek kasa bunun etrafında dalgalanır. İkisi arasındaki fark şanstır, model değil."""
    biten = [m for m in maclar if (m.get('sonuc') or {}).get('skor') and m.get('okuma')]
    sat = {}
    kal = {b: [0, 0] for b in range(10)}

    def ekle(tur, p, r, oran=None):
        x = sat.setdefault(tur, {'n': 0, 'tuttu': 0, 'beklenen': 0.0, 'kasa': 0.0, 'beklenen_kasa': 0.0})
        x['n'] += 1
        x['tuttu'] += r
        x['beklenen'] += p
        if oran:
            x['kasa'] += oran - 1 if r else -1
            x['beklenen_kasa'] += p * oran - 1

    for m in biten:
        o = m['okuma']
        r = _olan(m, o['tahmin']['kod'])
        if r is not None:
            ekle('tahmin', o['tahmin']['p'], r)
        ekle('skor', o['skor']['p'], int(m['sonuc']['skor'] == o['skor']['skor']))
        for s in o.get('sinyaller', []):
            r = _olan(m, s['kod'])
            if r is not None:
                ekle(s['seviye'], s['p'], r, s['oran'])
        if o.get('cesur'):
            r = _olan(m, o['cesur']['kod'])
            if r is not None:
                ekle('cesur', o['cesur']['p'], r)
        for k, p in o['olasilik'].items():
            r = _olan(m, k)
            if r is not None and not k.startswith(('CS', 'DNB')):
                b = min(int(p * 10), 9)
                kal[b][0] += 1
                kal[b][1] += r
    for x in sat.values():
        x['beklenen'] = round(x['beklenen'] / x['n'], 4)
        x['kasa'] = round(x['kasa'], 2)
        x['beklenen_kasa'] = round(x['beklenen_kasa'], 2)
    return {
        'mac': len(biten),
        'secim': sat,
        'kalibrasyon': [{'aralik': f'{b * 10}-{b * 10 + 10}', 'n': n, 'isabet': round(h / n, 4) if n else None}
                        for b, (n, h) in kal.items()],
    }


# ---------------------------------------------------------------- komut satırı
def main(argv):
    d = json.load(open(YOL))
    gun = next((a for a in argv if re.match(r'\d{4}-\d{2}-\d{2}$', a)), None)
    bugun = datetime.now(TSI).strftime('%Y-%m-%d')
    for m in d['maclar']:
        if gun and m['tarih'] != gun:
            continue
        o = oku(m)
        if o is None:
            continue
        # Maçtan sonra hesaplanan okuma "geriye dönük" işaretlenir (oranlar yine maç öncesi).
        eski = m.get('okuma') or {}
        o['geriye'] = eski.get('geriye', bool(m.get('sonuc')) or m['tarih'] < bugun)
        o['hesap'] = eski.get('hesap') if eski.get('geriye') is False and eski.get('lambda') == o['lambda'] else datetime.now(TSI).strftime('%Y-%m-%d %H:%M')
        m['okuma'] = o
    gunler = sorted({m['tarih'] for m in d['maclar']})
    d['kupon'] = {g: kupon([m for m in d['maclar'] if m['tarih'] == g]) for g in gunler}
    t = test(d['maclar'])
    if '--test' in argv:
        for k, v in t['secim'].items():
            print(f"{k:7s} {v['tuttu']}/{v['n']} (%{round(100 * v['tuttu'] / v['n'])}) beklenen %{round(100 * v['beklenen'])}"
                  f"  kasa {v['kasa']:+.2f} TL (beklenen {v['beklenen_kasa']:+.2f})")
        print('kalibrasyon', [(x['aralik'], x['n'], x['isabet']) for x in t['kalibrasyon']])
        for m in d['maclar']:
            if m['tarih'] == (gun or bugun) and m.get('okuma'):
                o = m['okuma']
                f = lambda s: f"{s['ad']} %{round(s['p'] * 100)}" if s else '–'
                sg = ', '.join(f"{s['seviye'][0]} {s['ad']} @{s['oran']} %{round(s['p'] * 100)}" for s in o['sinyaller'])
                print(f"{m['ev']['ad']} – {m['dep']['ad']}: {f(o['tahmin'])} · skor {o['skor']['skor']} · "
                      f"sinyal [{sg}] · cesur {f(o['cesur'])}")
        return
    d['okuma_test'] = t
    d['surum'] = SURUM
    d['guncelleme'] = datetime.now(TSI).strftime('%Y-%m-%d %H:%M')
    open(YOL, 'w').write(json.dumps(d, ensure_ascii=False, separators=(',', ':')))
    print(f"yazıldı: {sum(1 for m in d['maclar'] if m.get('okuma'))} maç okundu · test {t['mac']} maç")
    for k, v in t['secim'].items():
        print(f"  {k:7s} {v['tuttu']}/{v['n']} (%{round(100 * v['tuttu'] / v['n'])})  beklenen %{round(100 * v['beklenen'])}"
              f"  kasa {v['kasa']:+.2f} (beklenen {v['beklenen_kasa']:+.2f})")


if __name__ == '__main__':
    main(sys.argv[1:])
