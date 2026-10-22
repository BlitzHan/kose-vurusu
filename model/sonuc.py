"""Biten maçın pazarlarını çöz: her pazar için 1 (tuttu), 0 (yattı), 0.5 (yarım), None (iade)."""


def _ah(fark, cizgi):
    # fark: seçilen tarafın gol farkı. Tam çizgide beraberlik iade (None);
    # çeyrek çizgi iki yarıma bölünür: kazanç 1, iade 0.5, kayıp 0, ortalaması alınır.
    if abs(cizgi * 4) % 2 == 1:
        return sum(1 if fark + c > 0 else (0.5 if fark + c == 0 else 0) for c in (cizgi - 0.25, cizgi + 0.25)) / 2
    x = fark + cizgi
    return 1 if x > 0 else (None if x == 0 else 0)


def coz(kod, s):
    """s: {'skor': [ev, dep], 'iy': [ev, dep], 'ist': {'korner': [..], 'kart': [..]}, 'ilk_gol': 'ev'|'dep'|None}"""
    e, d = s['skor']
    ie, idp = s['iy']
    top = e + d
    if kod == 'MS1': return int(e > d)
    if kod == 'MSX': return int(e == d)
    if kod == 'MS2': return int(e < d)
    if kod == 'CS1X': return int(e >= d)
    if kod == 'CSX2': return int(e <= d)
    if kod == 'CS12': return int(e != d)
    if kod == 'IY1': return int(ie > idp)
    if kod == 'IYX': return int(ie == idp)
    if kod == 'IY2': return int(ie < idp)
    if kod == 'DNB1': return None if e == d else int(e > d)
    if kod == 'DNB2': return None if e == d else int(e < d)
    if kod == 'KGV': return int(e > 0 and d > 0)
    if kod == 'KGY': return int(not (e > 0 and d > 0))
    if kod.startswith('GOLU'): return int(top > float(kod[4:]))
    if kod.startswith('GOLA'): return int(top < float(kod[4:]))
    if kod.startswith('KORU'): return int(sum(s['ist']['korner']) > float(kod[4:]))
    if kod.startswith('KORA'): return int(sum(s['ist']['korner']) < float(kod[4:]))
    if kod.startswith('KARTU'): return int(sum(s['ist']['kart']) > float(kod[5:]))
    if kod.startswith('KARTA'): return int(sum(s['ist']['kart']) < float(kod[5:]))
    if kod == 'ILK1': return int(s['ilk_gol'] == 'ev')
    if kod == 'ILK2': return int(s['ilk_gol'] == 'dep')
    if kod == 'ILKYOK': return int(s['ilk_gol'] is None)
    if kod.startswith('AH'):
        fark = e - d if kod[2] == '1' else d - e
        return _ah(fark, float(kod[3:]))
    raise KeyError(kod)
