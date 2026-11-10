"""Okuma 3: daha seçici Güçlü sinyaller; ileri tarihli maçlara uygulanır."""
import argparse
import copy
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
import okuma

SURUM = 'okuma-3'
GUCLU = 0.80
AYRIM = '2026-10-31'


def oku(mac):
    return okuma.oku(mac, guclu=GUCLU, iadeli=False, surum=SURUM)


def acik(mac, simdi):
    """Başlamış ve sonuçlanmış maçların yayımlanan okumasını koru."""
    if mac.get('sonuc'):
        return False
    baslama = datetime.strptime(mac['tarih'] + ' ' + mac['saat'], '%Y-%m-%d %H:%M')
    return baslama.replace(tzinfo=okuma.TSI) > simdi


def uygula(veri, simdi, gun=None):
    d = copy.deepcopy(veri)
    degisen = set()
    for m in d['maclar']:
        if (gun and m['tarih'] != gun) or not acik(m, simdi):
            continue
        yeni = oku(m)
        if yeni is None:
            continue
        eski = m.get('okuma')
        if eski:
            arsiv = m.setdefault('okuma_gecmisi', [])
            if not arsiv or arsiv[-1] != eski:
                arsiv.append(copy.deepcopy(eski))
        yeni['geriye'] = False
        yeni['hesap'] = simdi.strftime('%Y-%m-%d %H:%M')
        m['okuma'] = yeni
        degisen.add(m['tarih'])
    if degisen:
        for gun in degisen:
            d.setdefault('kupon', {})[gun] = okuma.kupon(
                [m for m in d['maclar'] if m['tarih'] == gun and acik(m, simdi)])
        d['surum'] = SURUM
        d['guncelleme'] = simdi.strftime('%Y-%m-%d %H:%M')
    return d


def rapor(veri):
    """Aynı maç öncesi girdilerle yeniden hesaplanan, tarih ayrımlı karşılaştırma."""
    eski, yeni = [], []
    for mac in veri['maclar']:
        if not (mac.get('sonuc') or {}).get('skor'):
            continue
        m = copy.deepcopy(mac)
        m['okuma'] = okuma.oku(mac)
        eski.append(m)
        n = copy.deepcopy(mac)
        n['okuma'] = oku(mac)
        yeni.append(n)
    cikti = {}
    for ad, maclar in (('okuma-2', eski), (SURUM, yeni)):
        cikti[ad] = {}
        for donem, secilen in (
            ('erken', [m for m in maclar if m['tarih'] < AYRIM]),
            ('son', [m for m in maclar if m['tarih'] >= AYRIM]),
            ('toplam', maclar),
        ):
            t = okuma.test(secilen)
            cikti[ad][donem] = {
                'mac': t['mac'], 'guclu': t['secim'].get('Güçlü'),
                'guclu_mac': sum(any(s['seviye'] == 'Güçlü'
                                   for s in (m['okuma'] or {}).get('sinyaller', []))
                                 for m in secilen),
            }
    return cikti


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('gun', nargs='?')
    p.add_argument('--yaz', action='store_true', help='Yalnız başlamamış maçları güncelle')
    args = p.parse_args()
    yol = Path(okuma.YOL)
    veri = json.loads(yol.read_text(encoding='utf-8'))
    if not args.yaz:
        print(json.dumps(rapor(veri), ensure_ascii=False, indent=2))
        return
    d = uygula(veri, datetime.now(okuma.TSI), args.gun)
    if d == veri:
        print('Güncellenecek başlamamış maç yok.')
        return
    # Aynı dizinde atomik değiştirme; yarım JSON bırakma.
    fd, tmp = tempfile.mkstemp(dir=yol.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, separators=(',', ':'))
        os.replace(tmp, yol)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print('Başlamamış maçlar Okuma 3 ile güncellendi.')


if __name__ == '__main__':
    main()
