"""v0 analiz aracı: ham/<id>.json -> v0 sinyalleri -> data/tahminler.json.

Kullanım:
  python3 model/v0_analiz.py <id> [<id> ...] [--ayar-ev 0.97 --ayar-dep 1.0] [--kuru]

Kayıt şeması siteyle uyumlu kalır (analiz.kayit iskeleti), yalnız model ve öneriler
v0 ile yeniden hesaplanır. Aynı ham veri + aynı v0-ayarlar.json = aynı çıktı.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analiz
import v0

KOK = analiz.KOK
TSI = timezone(timedelta(hours=3))
YOL = os.path.join(KOK, 'data', 'tahminler.json')


def yaz(mac, a, eski=None, b_oranlar=None):
    """analiz.kayit iskeletini kur, v0 ile yeniden hesapla."""
    if eski is None:
        eski = mac
    kayit = analiz.kayit(mac, eski=eski)
    # v0 ayarı: eksik oyuncu çarpanı yarım güçle
    kayit['ayar'] = [a.get('_ayar_ev', 1.0), a.get('_ayar_dep', 1.0)]
    v0.hesapla(kayit, a, b_oranlar)
    return kayit


def main(argv):
    a = v0.ayar()
    kuru = '--kuru' in argv
    ayar_ev = ayar_dep = 1.0
    if '--ayar-ev' in argv:
        ayar_ev = float(argv[argv.index('--ayar-ev') + 1])
    if '--ayar-dep' in argv:
        ayar_dep = float(argv[argv.index('--ayar-dep') + 1])
    a['_ayar_ev'], a['_ayar_dep'] = ayar_ev, ayar_dep
    b_oranlar = None
    if '--b' in argv:
        b_oranlar = json.load(open(argv[argv.index('--b') + 1]))
    # basit ve sağlam: yalnız rakam olan argümanlar maç kimliği
    idler = [x for x in argv if x.isdigit()]

    d = json.load(open(YOL)) if os.path.exists(YOL) else {'maclar': []}
    for i in idler:
        h = json.load(open(os.path.join(KOK, 'ham', f'{i}.json')))
        eski = next((x for x in d['maclar'] if x.get('kaynak_id') == int(i)), None)
        m = yaz(h, a, eski, b_oranlar)
        if eski:
            d['maclar'][d['maclar'].index(eski)] = m
        else:
            d['maclar'].append(m)
        md = m['model']
        print(f"== {m['id']}  {m['tarih']} {m['saat']}  ({'kesin 11' if m['kadro']['kesin'] else 'muhtemel 11'})")
        print(f"   beklenen gol {md['lambda']}   ESS {md['v0']['ess']:.1f}   hash {md['v0']['ayar_hash']}/{md['v0']['veri_hash']}")
        print(f"   skorlar {md['skorlar'][:4]}")
        print(f"   SINYAL {[(o['kod'], o['oran'], round(o['puan'] * 100, 1), round(o['deger'] * 100, 1)) for o in m['oneriler']]}")
        # öne çıkan 5 pazar
        en = sorted([x for x in md['pazarlar'] if x.get('puan') is not None],
                    key=lambda x: -(x['puan'] * x['oran'] - 1))[:5]
        for x in en:
            print(f"     {x['kod']:10s} oran {x['oran_kullan']:.2f} ({x['kaynak']})  model %{100 * x['model']:.1f}  "
                  f"oran %{100 * x['piyasa']:.1f}  karışım %{100 * x['puan']:.1f}  EV %{100 * x['deger']:+.1f}  marj %{100 * x.get('marj', 0):.1f}")
    d['guncelleme'] = datetime.now(TSI).strftime('%Y-%m-%d %H:%M')
    d['surum'] = 'v0'
    if not kuru:
        open(YOL, 'w').write(json.dumps(d, ensure_ascii=False, separators=(',', ':')))
        print(f"yazıldı: {YOL} ({len(idler)} maç)")


if __name__ == '__main__':
    main(sys.argv)
