"""v0 walk-forward testi: geçmiş maçlarda model bahis oranını geçiyor mu?

Kullanım: python3 model/v0_test.py [--egitim 0.6]

Her bitmiş maç için takım gücü YALNIZ o maçtan önceki veriden hesaplanır.
Ölçütler:
- log-loss ve Brier: saf model / marjsız oran / karışım
- b2 taraması: model ağırlığı eğitim setinde seçilir, test setinde sınanır
- EV kuralı: eşik taraması, 1 TL başına getiri (ROI), isabet, CLV
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M
import v0

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOL = os.path.join(KOK, 'data', 'tahminler.json')
PAZARLAR = ['MS1', 'MSX', 'MS2', 'DNB1', 'DNB2', 'GOLU2.5', 'GOLA2.5', 'KGV', 'KGY']


def guvenli(x):
    return min(max(x, 1e-6), 1 - 1e-6)


def logloss(p, y):
    p = guvenli(p)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def brier(p, y):
    return (p - y) ** 2


def pazar_secenekleri(m):
    """Pazardan (kod, oran, olan, kapanis) sözlüğü."""
    out = {}
    for x in m['model']['pazarlar']:
        if x.get('olan') is None or x.get('oran') is None:
            continue
        out[x['kod']] = x
    return out


def oran_olasilik(P, kod):
    """Shin ile marjsız olasılık; ilgili pazarın tüm seçenekleri birlikte temizlenir."""
    grup = {'MS': ['MS1', 'MSX', 'MS2'], 'DNB': ['DNB1', 'DNB2'],
            'G25': ['GOLU2.5', 'GOLA2.5'], 'KG': ['KGV', 'KGY']}
    for ad, kodlar in grup.items():
        if kod in kodlar:
            var = [k for k in kodlar if k in P and P[k].get('oran')]
            if kod not in var or len(var) < 2:
                return None
            p = v0.shin([P[k]['oran'] for k in var])
            return dict(zip(var, p))
    return None


def hesapla_mac(m, a):
    """Maçın v0 olasılıkları ve oranları."""
    l1, l2, ess = v0.beklenen_gol(m, a)
    Mx, P = v0.olasilik(l1, l2, a)
    P_ham = pazar_secenekleri(m)
    out = {'ess': ess, 'lambda': (l1, l2), 'satirlar': []}
    temiz = {}
    for kod in PAZARLAR:
        if kod in P_ham:
            o = oran_olasilik(P_ham, kod)
            if o:
                temiz.update(o)
    for kod in PAZARLAR:
        x = P_ham.get(kod)
        if not x or kod not in P or kod not in temiz:
            continue
        pm = P[kod]
        po = temiz[kod]
        out['satirlar'].append({'kod': kod, 'oran': x['oran'], 'kapanis': x.get('kapanis'), 'olan': x['olan'],
                                'model': pm, 'oran_p': po, 'grup': x.get('grup')})
    return out


def karisim_deger(pm, po, b0, b1, b2):
    return v0.sigmoid(b0 + b1 * v0.logit(po) + b2 * v0.logit(pm))


def main(argv):
    egitim_pay = 0.6
    if '--egitim' in argv:
        egitim_pay = float(argv[argv.index('--egitim') + 1])
    a = v0.ayar()
    d = json.load(open(YOL))
    maclar = sorted([m for m in d['maclar'] if m.get('sonuc') and m.get('model', {}).get('pazarlar')],
                    key=lambda m: (m['tarih'], m.get('saat') or ''))
    print(f"bitmiş maç: {len(maclar)}")
    hepsi = []
    for m in maclar:
        try:
            h = hesapla_mac(m, a)
        except Exception as e:
            print('atla', m.get('id'), e)
            continue
        if not h['satirlar']:
            continue
        h['id'], h['tarih'] = m['id'], m['tarih']
        hepsi.append(h)
    print(f"hesaplanan: {len(hepsi)}  pazar satırı: {sum(len(x['satirlar']) for x in hepsi)}")
    if len(hepsi) < 30:
        print('yetersiz örnek'); return

    n_eg = int(len(hepsi) * egitim_pay)
    egitim, test = hepsi[:n_eg], hepsi[n_eg:]
    print(f"eğitim {len(egitim)} maç ({egitim[0]['tarih']}–{egitim[-1]['tarih']})  "
          f"test {len(test)} maç ({test[0]['tarih']}–{test[-1]['tarih']})")

    # --- 1. b2 taraması
    print("\n== model ağırlığı (b2) taraması: eğitimde seç, testte gör")
    print(" b2   eğitim log-loss   test log-loss   test Brier")
    en_iyi = None
    for b2 in [x / 20 for x in range(0, 21)]:
        ll_e = sum(logloss(karisim_deger(s['model'], s['oran_p'], 0, 1, b2), s['olan'])
                   for h in egitim for s in h['satirlar']) / max(1, sum(len(h['satirlar']) for h in egitim))
        ll_t = sum(logloss(karisim_deger(s['model'], s['oran_p'], 0, 1, b2), s['olan'])
                   for h in test for s in h['satirlar']) / max(1, sum(len(h['satirlar']) for h in test))
        br_t = sum(brier(karisim_deger(s['model'], s['oran_p'], 0, 1, b2), s['olan'])
                   for h in test for s in h['satirlar']) / max(1, sum(len(h['satirlar']) for h in test))
        if en_iyi is None or ll_e < en_iyi[1]:
            en_iyi = (b2, ll_e, ll_t, br_t)
        if b2 in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
            print(f" {b2:.2f}   {ll_e:.4f}          {ll_t:.4f}         {br_t:.4f}")
    print(f" -> eğitimde en iyi b2 = {en_iyi[0]:.2f} (test log-loss {en_iyi[2]:.4f}, Brier {en_iyi[3]:.4f})")

    # --- 2. saf model vs oran
    print("\n== saf model vs marjsız oran (tüm maçlar)")
    for ad, f in [('model', lambda s: s['model']), ('oran', lambda s: s['oran_p']),
                  ('karışım', lambda s: karisim_deger(s['model'], s['oran_p'], 0, 1, en_iyi[0]))]:
        ll = sum(logloss(f(s), s['olan']) for h in hepsi for s in h['satirlar']) / sum(len(h['satirlar']) for h in hepsi)
        br = sum(brier(f(s), s['olan']) for h in hepsi for s in h['satirlar']) / sum(len(h['satirlar']) for h in hepsi)
        print(f"  {ad:8s} log-loss {ll:.4f}   Brier {br:.4f}")

    # --- 3. EV kuralı: ROI ve CLV
    print("\n== EV kuralı (eşik taraması, maç başı tek seçim, oran 1.50–2.60)")
    print(" eşik   maç   isabet   ROI      CLV      kazanç(1 TL)")
    for esik in [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15]:
        secim = []
        for h in test:
            aday = [s for s in h['satirlar'] if s['kod'] in a['pazarlar'] or s['kod'].startswith('AH')]
            aday = [s for s in aday if a['oran_min'] <= s['oran'] <= a['oran_max']]
            for s in aday:
                s['ev'] = karisim_deger(s['model'], s['oran_p'], 0, 1, en_iyi[0]) * s['oran'] - 1
            aday = [s for s in aday if s['ev'] >= esik]
            if aday:
                secim.append(max(aday, key=lambda s: s['ev']))
        if not secim:
            print(f" {esik:.2f}    0      —        —        —        —")
            continue
        kazanc = sum((s['oran'] - 1) if s['olan'] == 1 else -1 for s in secim)
        isabet = sum(s['olan'] for s in secim)
        clv = [s['kapanis'] / s['oran'] - 1 for s in secim if s.get('kapanis')]
        print(f" {esik:.2f}   {len(secim):4d}   %{100 * isabet / len(secim):5.1f}   "
              f"%{100 * kazanc / len(secim):+6.1f}   %{100 * sum(clv) / len(clv) if clv else 0:+6.1f}   {kazanc:+.2f}")

    # --- 4. piyasa marjı
    marjlar = []
    for h in hepsi:
        for s in h['satirlar']:
            pass
    print("\nnot: CLV = kapanış oranı / alınan oran - 1; pozitifse kapanışta daha kısa fiyatlanmışız (iyi).")


if __name__ == '__main__':
    main(sys.argv)
