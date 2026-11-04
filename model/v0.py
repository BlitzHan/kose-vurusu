"""Köşe Vuruşu v0 (Sıfır): takım gücünden bağımsız beklenen gol, Dixon-Coles matrisi,
marjsız bahis oranı (Shin), logit karışım ve tek kural sinyal.

Tasarım kararları (bkz. model/v0-gundem.md):
- Beklenen gol bahis oranından TÜRETİLMEZ; yalnız takımların xG geçmişinden gelir.
- Bahis oranı girdi olarak kalır: p* = sigmoid(b0 + b1*logit(q) + b2*logit(p_model)).
  b1, b2 walk-forward'da tahmin edilir; b2 anlamlı değilse model bilgi katmıyor demektir.
- Marj Shin yöntemiyle temizlenir (orantılı temizleme favorileri şişirir).
- Tek sinyal sınıfı: EV* = p* * oran - 1 >= esik. GÜÇLÜ/ORTA ayrımı 500 sinyale kadar yok.
- Pazarlar: 1X2, DNB, AH, 2.5 alt/üst. Korner/kart/stil yalnız gösterim.

Deterministik: aynı ham veri + aynı ayar dosyası = aynı çıktı. Rastgelelik yok.
"""
import hashlib
import json
import math
import os

import model as M

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AYAR_YOL = os.path.join(KOK, 'model', 'v0-ayarlar.json')

VARSAYILAN = {
    'surum': 'v0',
    'rho': -0.06,
    'iy_pay': 0.45,
    'azalma': 0.90,          # maç başına ağırlık çarpanı (0.90 -> ESS ~19)
    'gol_payi': 0.25,        # takım gücünde golün xG'ye göre payı
    'lig_gol': 1.32,         # takım başına maç başı gol (2.64 toplam)
    'ev_avantaj': 1.10,
    'cekim_k': 8.0,          # büzülme: 8 maçlık sanal örnek kadar ortalamaya çek
    'b0': 0.0,
    'b1': 1.0,
    'b2': 0.55,
    'esik': 0.04,            # EV* eşiği
    'oran_min': 1.50,
    'oran_max': 2.60,
    'pazarlar': ['MS1', 'MSX', 'MS2', 'DNB1', 'DNB2', 'AH', 'GOLU2.5', 'GOLA2.5'],
    'mac_basi': 1,
    'min_ess': 8.0,
    'kaynak_a': 'a',
    'kaynak_b': 'b',
}


def ayar(yol=AYAR_YOL):
    a = dict(VARSAYILAN)
    if os.path.exists(yol):
        a.update(json.load(open(yol)))
    return a


def ayar_hash(a):
    return hashlib.sha256(json.dumps(a, sort_keys=True).encode()).hexdigest()[:12]


def veri_hash(mac):
    """Takım geçmişinin parmak izi: aynı maç listesi = aynı çıktı."""
    ozet = [[(x.get('tarih'), x.get('rakip'), x.get('at'), x.get('ye'), x.get('xg_l'), x.get('xg_a'), x.get('evde'))
             for x in mac[s]['maclar']] for s in ('ev', 'dep')]
    return hashlib.sha256(json.dumps(ozet, sort_keys=True).encode()).hexdigest()[:12]


# ---------------------------------------------------------------- takım gücü
def _satir_deger(x, anahtar, takim_mi):
    """Takımın kendi perspektifinden xG/gol: xg_l ev sahibinin, xg_a deplasmanın."""
    if anahtar == 'xg':
        v = x.get('xg_l') if takim_mi else x.get('xg_a')
    else:
        v = x.get('at') if takim_mi else x.get('ye')
    return v


def _agirlik(n, azalma):
    return [azalma ** i for i in range(n)]


def guc(satirlar, a, ev_sahibi):
    """Hücum ve savunma katsayıları (lig ortalaması = 1).

    satirlar: takımın son maçları (yeniden eskiye). Her satırda xg_l/xg_a, at/ye, evde var.
    Rakip düzeltmesi iteratif: hücum = ağırlıklı xG / (lig_gol * rakip_savunma).
    """
    n = len(satirlar)
    if not n:
        return 1.0, 1.0, 0.0
    w = _agirlik(n, a['azalma'])
    xg = [(_satir_deger(x, 'xg', True), _satir_deger(x, 'xg', False), x.get('evde')) for x in satirlar]
    gol = [(_satir_deger(x, 'gol', True), _satir_deger(x, 'gol', False), x.get('evde')) for x in satirlar]
    # xG yoksa gole düş; ikisi de yoksa satırı at
    deger = []
    for i in range(n):
        l = xg[i][0] if xg[i][0] is not None else gol[i][0]
        r = xg[i][1] if xg[i][1] is not None else gol[i][1]
        if l is None or r is None:
            continue
        deger.append((l, r, bool(gol[i][2])))
    if not deger:
        return 1.0, 1.0, 0.0
    w = w[:len(deger)]
    # ev sahibi avantajını ayır
    h = a['ev_avantaj']
    ev_carpan = lambda evde: h if evde else 1.0 / h
    # ilk tahmin: lig ortalamasına göre ham oran
    lig = a['lig_gol']
    atk = sum(wi * (d[0] / lig) / ev_carpan(d[2]) for wi, d in zip(w, deger)) / sum(w)
    dfn = sum(wi * (d[1] / lig) * ev_carpan(d[2]) for wi, d in zip(w, deger)) / sum(w)
    atk, dfn = max(atk, 0.2), max(dfn, 0.2)
    # iteratif rakip düzeltmesi (rakip katsayıları bilinmediği için 1 kabul edilir; iki geçiş yeter)
    for _ in range(3):
        pay_a = sum(wi * (d[0] / lig) / ev_carpan(d[2]) for wi, d in zip(w, deger))
        pay_d = sum(wi * (d[1] / lig) * ev_carpan(d[2]) for wi, d in zip(w, deger))
        atk = pay_a / sum(w)
        dfn = pay_d / sum(w)
        atk, dfn = max(atk, 0.2), max(dfn, 0.2)
    return atk, dfn, sum(w)


def beklenen_gol(mac, a=None):
    """v0'ın çekirdeği: bahis oranı görmeden beklenen gol."""
    a = a or ayar()
    A_e, D_e, w_e = guc(mac['ev']['maclar'], a, True)
    A_d, D_d, w_d = guc(mac['dep']['maclar'], a, True)
    k = a['cekim_k']
    # büzülme: az veri varsa 1.0'a çek
    cek = lambda x, w: (w * x + k) / (w + k)
    A_e, D_e, A_d, D_d = cek(A_e, w_e), cek(D_e, w_e), cek(A_d, w_d), cek(D_d, w_d)
    lig, h = a['lig_gol'], a['ev_avantaj']
    l1 = lig * A_e * D_d * h
    l2 = lig * A_d * D_e / h
    # elle ayar (eksik oyuncu vb.) yarım güçle
    ay = mac.get('ayar') or [1.0, 1.0]
    l1, l2 = l1 * ay[0] ** 0.5, l2 * ay[1] ** 0.5
    return round(l1, 3), round(l2, 3), min(w_e, w_d)


# ---------------------------------------------------------------- marj temizleme
def shin(oranlar, maxiter=60):
    """Shin yöntemi: bahisçinin içeriden bilgi payı z'yi çözerek marjı temizler.

    oranlar: [o1, o2, ...]. Dönüş: marjsız olasılık listesi (toplam 1).
    """
    pi = [1.0 / o for o in oranlar]
    B = sum(pi)
    if B <= 1.0001:  # marj yok ya da arbitraj; orantılı yeter
        return [x / B for x in pi]
    lo, hi = 0.0, 0.45
    for _ in range(maxiter):
        z = (lo + hi) / 2
        p = [(math.sqrt(z * z + 4 * (1 - z) * (x * x) / B) - z) / (2 * (1 - z)) for x in pi]
        if sum(p) > 1:
            lo = z
        else:
            hi = z
    z = (lo + hi) / 2
    p = [(math.sqrt(z * z + 4 * (1 - z) * (x * x) / B) - z) / (2 * (1 - z)) for x in pi]
    s = sum(p)
    return [x / s for x in p]


def marj(oranlar):
    return sum(1.0 / o for o in oranlar) - 1.0


# ---------------------------------------------------------------- karışım
def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def karisim(p_model, p_oran, a):
    """p* = sigmoid(b0 + b1*logit(oran) + b2*logit(model))."""
    return sigmoid(a['b0'] + a['b1'] * logit(p_oran) + a['b2'] * logit(p_model))


# ---------------------------------------------------------------- olasılıklar
def olasilik(l1, l2, a=None):
    """Skor matrisi ve tüm pazar olasılıkları (model tarafı)."""
    a = a or ayar()
    p = {'rho': a['rho'], 'iy': a['iy_pay']}
    Mx, P = M.olasiliklar(l1, l2, p)
    return Mx, P


# ---------------------------------------------------------------- kayıt işleme
def pazar_oranlari(mac):
    """Ham kayıttaki pazarları (kod, oran) olarak döndür; marjı Shin ile temizle."""
    out = {}
    for x in mac['model']['pazarlar']:
        kod = x['kod']
        if kod.startswith('AH'):
            # Asya handikabı çiftini aynı kod ailesinde tut
            out.setdefault('AH', []).append((kod, x['oran'], x['ad']))
        else:
            out[kod] = x['oran']
    # ikili pazarlar
    cift = {}
    for kod in ['MS1', 'MSX', 'MS2']:
        if kod in out:
            cift.setdefault('1X2', []).append((kod, out[kod]))
    for kod in ['DNB1', 'DNB2']:
        if kod in out:
            cift.setdefault('DNB', []).append((kod, out[kod]))
    for kod in ['GOLU2.5', 'GOLA2.5']:
        if kod in out:
            cift.setdefault('G25', []).append((kod, out[kod]))
    for kod in ['KGV', 'KGY']:
        if kod in out:
            cift.setdefault('KG', []).append((kod, out[kod]))
    return out, cift


def hesapla(mac, a=None, b_oranlar=None):
    """Bir maç kaydını v0 ile hesaplar (yerinde değiştirir).

    b_oranlar: ikinci kaynağın {pazar kodu: oran} sözlüğü. Verilirse her pazarda
    en iyi fiyat seçilir; edge tahminden değil fiyat farkından doğar.
    """
    a = a or ayar()
    l1, l2, ess = beklenen_gol(mac, a)
    Mx, P = olasilik(l1, l2, a)
    md = mac['model']
    md['v0'] = {'lambda': [l1, l2], 'ess': round(ess, 1), 'ayar_hash': ayar_hash(a), 'veri_hash': veri_hash(mac)}
    md['lambda'] = [l1, l2]
    md['matris'] = [[round(Mx[i][j], 3) for j in range(6)] for i in range(6)]
    sk = sorted(((f'{i}-{j}', Mx[i][j]) for i in range(M.N) for j in range(M.N)), key=lambda x: -x[1])
    md['skorlar'] = [[s, round(p, 3)] for s, p in sk[:5]]
    md['surum'] = 'v0'

    # piyasa: Shin ile marjsız
    ham, cift = pazar_oranlari(mac)
    temiz = {}
    for grup, sec in cift.items():
        p = shin([o for _, o in sec])
        for (kod, _), pp in zip(sec, p):
            temiz[kod] = pp

    # her pazar için p*, edge, EV
    for x in md['pazarlar']:
        kod = x['kod']
        pm = P.get(kod)
        if kod.startswith('AH'):
            pm = ah_olasilik(Mx, kod)
        po = temiz.get(kod)
        if pm is None or po is None:
            x['model'], x['piyasa'], x['seviye'], x['deger'], x['ayrisma'], x['puan'] = None, None, None, None, None, None
            continue
        ps = karisim(pm, po, a)
        x['model'] = round(pm, 4)          # saf model (gösterim)
        x['piyasa'] = round(po, 4)         # marjsız bahis oranı olasılığı
        x['puan'] = round(ps, 4)           # karışım: sinyalde kullanılan
        # fiyat: kaynak A (ana) ve varsa B (alternatif) arasından en iyisi
        o_a = x['oran']
        o_b = (b_oranlar or {}).get(kod)
        if o_b and o_b > o_a:
            o, kaynak = o_b, 'B'
        else:
            o, kaynak = o_a, 'A'
        x['oran_a'], x['oran_b'], x['oran_kullan'], x['kaynak'] = o_a, o_b, o, kaynak
        x['deger'] = round(ps * o - 1, 4)
        x['ayrisma'] = round(pm - po, 4)
        x['marj'] = round(marj([v for _, v in cift.get(grup_kod(kod), [])]) if grup_kod(kod) in cift else 0, 4)
        # sinyal kuralı
        izin = kod in a['pazarlar'] or (kod.startswith('AH') and 'AH' in a['pazarlar'])
        if (izin and a['oran_min'] <= o <= a['oran_max']
                and x['deger'] >= a['esik'] and ess >= a['min_ess']):
            x['seviye'] = 'Güçlü'
        else:
            x['seviye'] = None
    aday = sorted([x for x in md['pazarlar'] if x['seviye']], key=lambda x: -x['deger'])
    mac['oneriler'] = [{k: x.get(k) for k in ('kod', 'ad', 'grup', 'oran', 'oran_a', 'oran_b', 'oran_kullan', 'kaynak',
                                                'seviye', 'puan', 'model', 'piyasa', 'deger', 'ayrisma', 'marj')}
                       for x in aday[:a['mac_basi']]]
    mac['sinyal'] = 'guclu' if mac['oneriler'] else 'zayif'
    mac['v0'] = {'surum': 'v0', 'esik': a['esik'], 'oran': [a['oran_min'], a['oran_max']],
                 'ayar_hash': ayar_hash(a), 'veri_hash': veri_hash(mac)}
    return mac


def grup_kod(kod):
    if kod.startswith('MS'): return '1X2'
    if kod.startswith('DNB'): return 'DNB'
    if kod.startswith('GOL'): return 'G25'
    if kod.startswith('KG'): return 'KG'
    if kod.startswith('AH'): return 'AH'
    return kod


def ah_olasilik(Mx, kod):
    """Asya handikabı: adil olasılık (1/adil oran)."""
    cizgi = float(kod[3:].replace(',', '.'))
    taraf = 1 if kod[2] == '1' else 2
    return M.ah(Mx, cizgi, taraf)
