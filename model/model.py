"""Köşe Vuruşu modeli: beklenen gol, skor dağılımı, pazar olasılıkları, puan ve seviye.

v1: 21 Ekim 2026 maçlarında kullanılan sürüm (kayıtlı verilerden birebir geri çıkarıldı).
v2: 21 Ekim sonuçlarından sonraki düzeltmeler (bkz. model/geri-bildirim-2026-10-21.md).
"""
import math

N = 11
SURUM = {
    'v1': dict(rho=-0.075, iy=0.48, piyasa_agirlik=0.5,
               korner_ort=None, korner_cekim=1.0, korner_r=None,
               kart_ort=None, kart_cekim=1.0, sayim_en_fazla='Güçlü'),
    'v2': dict(rho=-0.075, iy=0.48, piyasa_agirlik=0.6,
               korner_ort=9.7, korner_cekim=0.35, korner_r=14.0,
               kart_ort=3.8, kart_cekim=0.25, sayim_en_fazla='Orta'),
}
PUAN = dict(model=0.6, gecmis=0.25, piyasa=0.15)


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
def carpan(f, f_rakip, onem):
    """Oyuncu formu ve eksiklerle hücum çarpanı."""
    c = math.exp(0.5 * f['fark'] - 0.3 * f_rakip['fark'] - 0.31 * f['eksik_payi']) * onem
    return min(max(c, 0.85), 1.15)


def beklenen_gol(md, onem, p):
    car = [carpan(md['form']['ev'], md['form']['dep'], onem['ev']['carpan']),
           carpan(md['form']['dep'], md['form']['ev'], onem['dep']['carpan'])]
    veri = [md['taban'][i] * car[i] for i in range(2)]
    w = p['piyasa_agirlik']
    lam = [veri[i] ** (1 - w) * md['piyasa_l'][i] ** w for i in range(2)]
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


def seviye(x, en_fazla):
    if x['elendi']:
        return None
    m, g, pi, dg = x['model'], x['gecmis'], x['piyasa'], x['deger']
    s = None
    if m >= 0.58 and g >= 0.55 and pi >= 0.5 and -0.05 <= dg <= 0.15:
        s = 'Güçlü'
    elif m >= 0.54 and g >= 0.5 and -0.08 <= dg <= 0.3:
        s = 'Orta'
    if s == 'Güçlü' and en_fazla == 'Orta':
        s = 'Orta'
    return s


def hesapla(m, surum='v2', ham=None):
    """Bir maçın model bloğunu ve önerilerini yeniden hesaplar (m yerinde değişir).

    ham: korner/kart için takım ortalamasından gelen ham beklenti; verilmezse m['model']['ham'] ya da mevcut değer.
    """
    p = SURUM[surum]
    md = m['model']
    car, veri, lam = beklenen_gol(md, m['onem'], p)
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
        x['model'] = round(v, 3)
        x['puan'] = round(sum(PUAN[a] * x[a] for a in PUAN), 3)
        x['deger'] = round(x['model'] * x['oran'] - 1, 3)
        x['seviye'] = seviye(x, p['sayim_en_fazla'] if k.startswith(('KOR', 'KART')) else 'Güçlü')
    aday = sorted([x for x in md['pazarlar'] if x['seviye']], key=lambda x: (x['seviye'] != 'Güçlü', -x['puan']))
    sec, gruplar = [], set()
    for x in aday:
        if x['grup'] not in gruplar:
            gruplar.add(x['grup'])
            sec.append(x)
        if len(sec) == 3:
            break
    alan = ['kod', 'ad', 'grup', 'oran', 'seviye', 'puan', 'model', 'gecmis', 'gecmis_ev', 'gecmis_dep', 'piyasa', 'deger']
    m['oneriler'] = [{a: x[a] for a in alan} for x in sec]
    m['sinyal'] = 'guclu' if any(x['seviye'] == 'Güçlü' for x in sec) else ('orta' if sec else 'zayif')
    md['surum'] = surum
    return m
