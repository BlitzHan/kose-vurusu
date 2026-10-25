"""Köşe Vuruşu modeli: beklenen gol, skor dağılımı, pazar olasılıkları, puan ve seviye.

v1: 21 Ekim 2026 maçlarında kullanılan sürüm (kayıtlı verilerden birebir geri çıkarıldı).
v2: 21 Ekim sonuçlarından sonraki düzeltmeler (bkz. model/geri-bildirim-2026-10-21.md).
v3: 22 Ekim sonuçlarından sonra (24 maç): piyasa payı, ilişkili öneri eleme, muhtemel 11'de form payı (bkz. geri-bildirim-2026-10-22.md).
v4: 23 Ekim sonuçlarından sonra (33 maç): beklenen gol piyasadan, gol çizgilerinde piyasa olasılığı, yeni Güçlü, son 10 eşiği kalktı, korner/kart ortalaması (bkz. geri-bildirim-2026-10-23.md).
v5: 24 Ekim sonuçlarından sonra (55 maç): kart ortalaması 4,4, kart olasılığının %75'i piyasadan (bkz. geri-bildirim-2026-10-24.md).
"""
import math

import sonuc as S

N = 11
SURUM = {
    'v1': dict(rho=-0.075, iy=0.48, piyasa_agirlik=0.5,
               korner_ort=None, korner_cekim=1.0, korner_r=None,
               kart_ort=None, kart_cekim=1.0, sayim_en_fazla='Güçlü'),
    'v2': dict(rho=-0.075, iy=0.48, piyasa_agirlik=0.6,
               korner_ort=9.7, korner_cekim=0.35, korner_r=14.0,
               kart_ort=3.8, kart_cekim=0.25, sayim_en_fazla='Orta'),
}
SURUM['v3'] = dict(SURUM['v2'], piyasa_agirlik=0.8, korelasyon=0.4, muhtemel_form=0.5)
SURUM['v4'] = dict(SURUM['v3'], piyasa_agirlik=1.0, carpan_payi=0.25, ayar_payi=0.5, son10_esik=False,
                   korner_ort=9.3, kart_ort=4.0, guclu=dict(model=0.64, piyasa=0.6, deger=(-0.08, 1.0)),
                   pazar_piyasa={'Toplam gol': 0.75, 'Karşılıklı gol': 0.75})
SURUM['v5'] = dict(SURUM['v4'], kart_ort=4.4, pazar_piyasa=dict(SURUM['v4']['pazar_piyasa'], Kart=0.75))
# Eski sürümler için varsayılanlar: puan formülü, ilişkili öneri eşiği (1 = eleme yok), kadro kesin değilken form payı,
# piyasa beklentisine uygulanan form/eksik çarpanı ve elle ayar payı (v4), son 10 maç eşiği, Güçlü eşikleri,
# gruba göre olasılığın piyasanın kendi olasılığıyla harmanlanma payı (v4)
VARSAYILAN = dict(puan=dict(model=0.6, gecmis=0.25, piyasa=0.15), korelasyon=1.0, muhtemel_form=1.0,
                  carpan_payi=0.0, ayar_payi=0.0, son10_esik=True,
                  guclu=dict(model=0.58, piyasa=0.5, deger=(-0.05, 0.15)), pazar_piyasa={})
for _p in SURUM.values():
    for _k, _v in VARSAYILAN.items():
        _p.setdefault(_k, _v)

# Lig gücü: takım verisindeki xG'yi Avrupa düzeyine çevirir (Premier League = 1).
LIG_GUCU = {
    'Premier League': 1.0, 'LaLiga': 0.95, 'Serie A': 0.93, 'Bundesliga': 0.93, 'Ligue 1': 0.86,
    'Primeira Liga': 0.85, 'Eredivisie': 0.82, 'Pro League': 0.8, 'Süper Lig': 0.78,
    'Ukrayna Ligi': 0.70, 'İskoçya Ligi': 0.68,
    'Şampiyonlar Ligi': 1.0, 'Avrupa Ligi': 0.88, 'Konferans Ligi': 0.78,
}
# Takım verisinden beklenen gol (taban): 21 Ekim kayıtlarındaki değerlere ~0,1 hatayla oturtuldu.
TABAN = dict(azalma=0.85, gol_payi=0.3, ev=1.1, cekim=0.4, ort=1.3)


def _guc(maclar, lig):
    A = D = W = 0.0
    for i, x in enumerate(maclar):
        if x.get('xg_l') is None:
            continue
        w = TABAN['azalma'] ** i
        L = LIG_GUCU.get(x['turnuva'], LIG_GUCU.get(lig, 0.8))
        g = TABAN['gol_payi']
        A += w * ((1 - g) * x['xg_l'] + g * x['at']) * L
        D += w * ((1 - g) * x['xg_a'] + g * x['ye']) / L
        W += w
    return (A / W, D / W) if W else (TABAN['ort'], TABAN['ort'])


def taban(ev_maclar, ev_lig, dep_maclar, dep_lig):
    (Ae, De), (Ad, Dd) = _guc(ev_maclar, ev_lig), _guc(dep_maclar, dep_lig)
    mu, k, H = TABAN['ort'], TABAN['cekim'], TABAN['ev']
    c = lambda x: mu + k * (x - mu)
    return [round(c(Ae) * c(Dd) / mu * H, 2), round(c(Ad) * c(De) / mu / H, 2)]


def piyasa_lambda(ms1, msx, ms2, ust25, rho=-0.075):
    """Piyasanın maç sonucu ve 2,5 üst olasılıklarına en iyi uyan beklenen gol çifti."""
    en = None
    for a in range(30, 400, 5):
        for b in range(20, 350, 5):
            l1, l2 = a / 100, b / 100
            M = matris(l1, l2, rho)
            p1 = sum(M[i][j] for i in range(N) for j in range(N) if i > j)
            px = sum(M[i][i] for i in range(N))
            pu = sum(M[i][j] for i in range(N) for j in range(N) if i + j > 2.5)
            e = (p1 - ms1) ** 2 + (px - msx) ** 2 + (1 - p1 - px - ms2) ** 2 + (pu - ust25) ** 2
            if en is None or e < en[0]:
                en = (e, l1, l2)
    return [en[1], en[2]]


# ---------------------------------------------------------------- dağılımlar
def pois(k, l):
    return math.exp(-l) * l ** k / math.factorial(k)


def negbin(k, mu, r):
    """Negatif binom: ortalama mu, varyans mu + mu²/r (korner Poisson'dan daha dağınık)."""
    p = r / (r + mu)
    return math.exp(math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1) + r * math.log(p) + k * math.log(1 - p))


def ust(cizgi, mu, r=None):
    """P(toplam > cizgi)."""
    f = (lambda k: negbin(k, mu, r)) if r else (lambda k: pois(k, mu))
    return 1 - sum(f(k) for k in range(int(math.floor(cizgi)) + 1))


def matris(l1, l2, rho):
    M = [[pois(i, l1) * pois(j, l2) for j in range(N)] for i in range(N)]
    M[0][0] *= 1 - l1 * l2 * rho
    M[0][1] *= 1 + l1 * rho
    M[1][0] *= 1 + l2 * rho
    M[1][1] *= 1 - rho
    s = sum(map(sum, M))
    return [[x / s for x in r] for r in M]


def ah(M, cizgi, taraf):
    """Asya handikapı, 1 / adil oran olarak: çeyrek çizgi ikiye bölünür, iade bahsi geri verir."""
    yarim = [cizgi - 0.25, cizgi + 0.25] if abs(cizgi * 4) % 2 == 1 else [cizgi, cizgi]
    A = B = 0.0  # beklenen dönüş = A * oran + B
    for i in range(N):
        for j in range(N):
            fark = (i - j) if taraf == 1 else (j - i)
            for h in yarim:
                if fark + h > 0:
                    A += 0.5 * M[i][j]
                elif fark + h == 0:
                    B += 0.5 * M[i][j]
    return A / (1 - B)


# ---------------------------------------------------------------- beklenen gol
def carpan(f, f_rakip, onem, pay=1.0):
    """Oyuncu formu ve eksiklerle hücum çarpanı. pay: 11 kesin değilken form farkına verilen pay."""
    c = math.exp(pay * (0.5 * f['fark'] - 0.3 * f_rakip['fark']) - 0.31 * f['eksik_payi']) * onem
    return min(max(c, 0.85), 1.15)


def beklenen_gol(md, onem, p, kesin=True):
    pay = 1.0 if kesin else p['muhtemel_form']
    car = [carpan(md['form']['ev'], md['form']['dep'], onem['ev']['carpan'], pay),
           carpan(md['form']['dep'], md['form']['ev'], onem['dep']['carpan'], pay)]
    veri = [md['taban'][i] * car[i] for i in range(2)]
    w = p['piyasa_agirlik']
    lam = [veri[i] ** (1 - w) * md['piyasa_l'][i] ** w for i in range(2)]
    # v4: piyasa beklentisi esas; oyuncu formu, eksikler ve elle ayar onu yalnız biraz oynatır
    ayar = md.get('ayar') or [1.0, 1.0]
    lam = [lam[i] * car[i] ** p['carpan_payi'] * ayar[i] ** p['ayar_payi'] for i in range(2)]
    return car, veri, lam


def sayim(beklenen, ort, cekim):
    """Takım ortalamasına dayalı korner/kart beklentisini lig ortalamasına doğru çek."""
    return beklenen if ort is None else ort + cekim * (beklenen - ort)


# ---------------------------------------------------------------- olasılıklar
def olasiliklar(l1, l2, p):
    M = matris(l1, l2, p['rho'])
    H = matris(l1 * p['iy'], l2 * p['iy'], p['rho'])
    ara = lambda X, f: sum(X[i][j] for i in range(N) for j in range(N) if f(i, j))
    P = {}
    P['MS1'], P['MSX'] = ara(M, lambda i, j: i > j), ara(M, lambda i, j: i == j)
    P['MS2'] = 1 - P['MS1'] - P['MSX']
    P['CS1X'], P['CSX2'], P['CS12'] = P['MS1'] + P['MSX'], P['MS2'] + P['MSX'], P['MS1'] + P['MS2']
    P['IY1'], P['IYX'] = ara(H, lambda i, j: i > j), ara(H, lambda i, j: i == j)
    P['IY2'] = 1 - P['IY1'] - P['IYX']
    P['DNB1'] = P['MS1'] / (P['MS1'] + P['MS2'])
    P['DNB2'] = 1 - P['DNB1']
    P['KGV'] = ara(M, lambda i, j: i > 0 and j > 0)
    P['KGY'] = 1 - P['KGV']
    for t in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]:
        P[f'GOLU{t}'] = ara(M, lambda i, j: i + j > t)
        P[f'GOLA{t}'] = 1 - P[f'GOLU{t}']
    P['ILKYOK'] = M[0][0]
    P['ILK1'] = (1 - M[0][0]) * l1 / (l1 + l2)
    P['ILK2'] = (1 - M[0][0]) * l2 / (l1 + l2)
    return M, P


# ---------------------------------------------------------------- ilişkili öneriler
def _skorla(kod, i, j):
    """Skor i-j iken pazarın değeri; skordan çözülemeyen pazar (ilk yarı, korner, kart) için None."""
    if kod.startswith(('IY', 'KOR', 'KART')):
        return None
    if kod in ('ILK1', 'ILK2'):
        a = i if kod == 'ILK1' else j
        return a / (i + j) if i + j else 0
    v = S.coz(kod, {'skor': [i, j], 'iy': [0, 0], 'ist': {'korner': [0, 0], 'kart': [0, 0]}, 'ilk_gol': None})
    return 0.5 if v is None else v


def korelasyon(a, b, M):
    """İki pazarın skor matrisine göre korelasyonu. KG var ile 2,5 üst gibi aynı hikâyeye dayanan öneriler ~0,5 çıkar."""
    ex = ey = exy = ex2 = ey2 = 0.0
    for i in range(N):
        for j in range(N):
            x, y = _skorla(a, i, j), _skorla(b, i, j)
            if x is None or y is None:
                return 0.0
            p = M[i][j]
            ex, ey, exy, ex2, ey2 = ex + p * x, ey + p * y, exy + p * x * y, ex2 + p * x * x, ey2 + p * y * y
    v = (ex2 - ex * ex) * (ey2 - ey * ey)
    return (exy - ex * ey) / math.sqrt(v) if v > 0 else 0.0


def seviye(x, en_fazla, p):
    if x['elendi'] or x['gecmis'] is None:  # son maçlarda sayılamayan pazar öneri olmaz
        return None
    m, g, pi, dg = x['model'], x['gecmis'], x['piyasa'], x['deger']
    if not p['son10_esik']:  # v4: son 10 sıklığı isabeti öngörmedi; yalnız puanda ve bilette kalır
        g = 1.0
    G = p['guclu']  # v4: Güçlü = model ve piyasa birlikte yüksek olasılık veriyor (değer aranmaz)
    s = None
    if m >= G['model'] and g >= 0.55 and pi >= G['piyasa'] and G['deger'][0] <= dg <= G['deger'][1]:
        s = 'Güçlü'
    elif m >= 0.54 and g >= 0.5 and -0.08 <= dg <= 0.3:
        s = 'Orta'
    if s == 'Güçlü' and en_fazla == 'Orta':
        s = 'Orta'
    return s


def hesapla(m, surum='v5', ham=None):
    """Bir maçın model bloğunu ve önerilerini yeniden hesaplar (m yerinde değişir).

    ham: korner/kart için takım ortalamasından gelen ham beklenti; verilmezse m['model']['ham'] ya da mevcut değer.
    """
    p = SURUM[surum]
    md = m['model']
    car, veri, lam = beklenen_gol(md, m['onem'], p, m['kadro'].get('kesin', True))
    md['carpan'] = [round(c, 3) for c in car]
    md['veri_l'] = [round(v, 2) for v in veri]
    md['lambda'] = [round(v, 2) for v in lam]
    ham = ham or md.get('ham') or {'korner': md['korner'], 'kart': md['kart']}
    md['ham'] = ham
    md['korner'] = round(sayim(ham['korner'], p['korner_ort'], p['korner_cekim']), 1)
    md['kart'] = round(sayim(ham['kart'], p['kart_ort'], p['kart_cekim']), 1)
    M, P = olasiliklar(lam[0], lam[1], p)
    md['matris'] = [[round(M[i][j], 3) for j in range(6)] for i in range(6)]
    sk = sorted(((f'{i}-{j}', M[i][j]) for i in range(N) for j in range(N)), key=lambda x: -x[1])[:5]
    md['skorlar'] = [[a, round(b, 3)] for a, b in sk]
    for x in md['pazarlar']:
        k = x['kod']
        if k.startswith('AH'):
            v = ah(M, float(k[3:]), 1 if k[2] == '1' else 2)
        elif k.startswith('KOR'):
            u = ust(float(k[4:]), md['korner'], p['korner_r'])
            v = u if k[3] == 'U' else 1 - u
        elif k.startswith('KART'):
            u = ust(float(k[5:]), md['kart'])
            v = u if k[4] == 'U' else 1 - u
        else:
            v = P[k]
        w = p['pazar_piyasa'].get(x['grup'])  # v4: gol çizgilerinin kuyruğunu piyasa iki parametreli Poisson'dan iyi biliyor; v5: kartta da
        if w and x['piyasa'] is not None:
            v = (1 - w) * v + w * x['piyasa']
        x['model'] = round(v, 3)
        var = [a for a in p['puan'] if x[a] is not None]  # geçmiş yoksa kalan ağırlıklarla
        x['puan'] = round(sum(p['puan'][a] * x[a] for a in var) / sum(p['puan'][a] for a in var), 3)
        x['deger'] = round(x['model'] * x['oran'] - 1, 3)
        x['seviye'] = seviye(x, p['sayim_en_fazla'] if k.startswith(('KOR', 'KART')) else 'Güçlü', p)
    aday = sorted([x for x in md['pazarlar'] if x['seviye']], key=lambda x: (x['seviye'] != 'Güçlü', -x['puan']))
    sec, gruplar = [], set()
    for x in aday:
        if x['grup'] in gruplar or any(korelasyon(x['kod'], y['kod'], M) > p['korelasyon'] for y in sec):
            continue
        gruplar.add(x['grup'])
        sec.append(x)
        if len(sec) == 3:
            break
    alan = ['kod', 'ad', 'grup', 'oran', 'seviye', 'puan', 'model', 'gecmis', 'gecmis_ev', 'gecmis_dep', 'piyasa', 'deger']
    m['oneriler'] = [{a: x[a] for a in alan} for x in sec]
    m['sinyal'] = 'guclu' if any(x['seviye'] == 'Güçlü' for x in sec) else ('orta' if sec else 'zayif')
    md['surum'] = surum
    return m
