// Köşe Vuruşu · biletler. Tek veri kaynağı: data/tahminler.json
(() => {
  'use strict';

  const $ = (s, k = document) => k.querySelector(s);
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const yuzde = (p) => (p == null ? '–' : '%' + Math.round(p * 100));
  const ondalik = (v, h = 1) => (v == null ? '–' : Number(v).toLocaleString('tr-TR', { minimumFractionDigits: h, maximumFractionDigits: h }));
  const tarihYaz = (t, s) => new Intl.DateTimeFormat('tr-TR', s).format(new Date(t + 'T12:00:00'));
  const uzunluk = (ad) => { const k = Math.max(...ad.split(' ').map((w) => w.length)); return k > 12 ? 'cok-uzun' : k > 8 ? 'uzun' : ''; };
  const sayiYaz = (v) => (Number.isInteger(v) ? v : String(v).replace('.', ','));
  const kisa = (ad) => (ad.length <= 11 ? ad : ad.split(' ').filter((w) => w.length > 2).pop());

  const GRUP_SIRA = ['Maç sonucu', 'Toplam gol', 'Karşılıklı gol', 'İlk yarı', 'İlk gol', 'Korner', 'Kart'];
  const oranYaz = (o) => Number(o).toFixed(2);

  let veri = null;
  let gunler = [];
  let sira = 'saat';
  try { if (localStorage.getItem('sira') === 'guven') sira = 'guven'; } catch (e) { /* depolama kapalı */ }

  // Güvenilirlik: en olası Güçlü sinyal önde, sonra Orta; eşitlikte saat.
  const SEVIYE = { 'Güçlü': 2, 'Orta': 1 };
  const sinyalleri = (m) => (m.okuma && m.okuma.sinyaller) || [];
  const guven = (m) => Math.max(0, ...sinyalleri(m).map((o) => (SEVIYE[o.seviye] || 0) + o.p));
  const SIRALA = {
    saat: (a, b) => a.saat.localeCompare(b.saat) || (b.manset - a.manset),
    guven: (a, b) => guven(b) - guven(a) || a.saat.localeCompare(b.saat),
  };

  // Seçimin maçta olup olmadığı: 1 tuttu, 0 tutmadı, 'iade', null bilinmiyor.
  // Önce pazarın işlenmiş sonucu, yoksa skordan.
  function olan(m, kod) {
    const s = m.sonuc;
    if (!s || !s.skor) return null;
    const p = m.model.pazarlar.find((x) => x.kod === kod);
    if (p && 'olan' in p) return p.olan === 1 ? 1 : p.olan === 0 ? 0 : 'iade';
    const [i, j] = s.skor.split('-').map(Number);
    const g = /^GOL([UA])([\d.]+)$/.exec(kod);
    if (g) return +(g[1] === 'U' ? i + j > +g[2] : i + j < +g[2]);
    const k = {
      MS1: i > j, MSX: i === j, MS2: j > i, CS1X: i >= j, CSX2: j >= i, KGV: i > 0 && j > 0, KGY: !(i > 0 && j > 0),
      'MS1+U2.5': i > j && i + j >= 3, 'MS2+U2.5': j > i && i + j >= 3, 'MS1+KGV': i > j && j > 0, 'MS2+KGV': j > i && i > 0,
      'MS1+KGY': i > j && j === 0, 'MS2+KGY': j > i && i === 0, 'MSX+A2.5': i === j && i + j <= 2,
      'CS1X+A3.5': i >= j && i + j <= 3, 'CSX2+A3.5': j >= i && i + j <= 3, 'CS1X+KGV': i >= j && j > 0, 'CSX2+KGV': j >= i && i > 0,
    };
    if (kod in k) return +k[kod];
    if (/^DNB[12]$/.test(kod)) return i === j ? 'iade' : +(kod === 'DNB1' ? i > j : j > i);
    return null;
  }
  const durumAd = (r) => (r === 1 ? 'tuttu' : r === 0 ? 'tutmadi' : r === 'iade' ? 'iade' : '');
  const ZIMBA = { tuttu: 'Tuttu', tutmadi: 'Tutmadı', iade: 'İade' };

  // ---------------------------------------------------------------- karne
  // Seçili günün Güçlü isabeti ve 1 TL kasası (her Güçlü sinyale 1 TL), yanında oranların ima ettiği beklenen kasa.
  // Gerçek ile beklenen arasındaki fark şanstır: bir günün kötü geçmesi modelin bozulduğu anlamına gelmez.
  function sayim(maclar, seviye) {
    let say = 0, tut = 0, kar = 0, bek = 0;
    maclar.forEach((m) => sinyalleri(m).filter((s) => s.seviye === seviye).forEach((s) => {
      const r = olan(m, s.kod);
      if (r === null || r === 'iade') return;
      say += 1; tut += r;
      kar += r ? s.oran - 1 : -1;
      bek += s.p * s.oran - 1;
    }));
    return { say, tut, kar, bek };
  }
  const isaretli = (v, h) => (v > 0 ? '+' : v < 0 ? '−' : '') + ondalik(Math.abs(v), h);
  const yuzdeOran = (t, s) => (s ? '%' + Math.round((t / s) * 100) : '–');
  const blok = (ad, tut, say, alt, sinif = '') =>
    `<span class="karne-blok ${sinif}"><small>${ad}</small><b>${tut}/${say}</b><small>${alt}</small></span>`;

  function karne(gun) {
    const gm = veri.maclar.filter((m) => m.tarih === gun && m.okuma);
    const biten = gm.filter((m) => m.sonuc && m.sonuc.skor);
    if (!biten.length) return '<span class="karne-blok"><small>Bu gün</small><b>bekleniyor</b></span>';
    const G = sayim(gm, 'Güçlü'), O = sayim(gm, 'Orta');
    const tah = biten.map((m) => olan(m, m.okuma.tahmin.kod)).filter((r) => r === 0 || r === 1);
    const skor = biten.filter((m) => m.sonuc.skor === m.okuma.skor.skor).length;
    const kasa = G.say
      ? `<span class="karne-blok karne-getiri ${G.kar >= 0 ? 'arti' : 'eksi'}" title="Her Güçlü sinyale 1 TL yatırılmış gibi; gerçek para değil. Beklenen: oranlara göre bu sinyallerden ortalamada çıkması gereken.">`
        + `<small>Güçlü · 1 TL</small><b>${isaretli(G.kar, 2)} TL</b><small>beklenen ${isaretli(G.bek, 2)}</small></span>`
      : '';
    return blok('Güçlü', G.tut, G.say, yuzdeOran(G.tut, G.say), 'guclu')
      + kasa
      + blok('Orta', O.tut, O.say, yuzdeOran(O.tut, O.say))
      + blok('Tahmin', tah.filter(Boolean).length, tah.length, yuzdeOran(tah.filter(Boolean).length, tah.length))
      + blok('Skor', skor, biten.length, yuzdeOran(skor, biten.length), 'karne-skor');
  }

  // ---------------------------------------------------------------- kupon
  // Günün Güçlü sinyallerinden maç başı tek ayak, en olası 2'li ve 3'lü (model/okuma.py). Ayak durumu skordan.
  function kuponKarti(k) {
    const dur = k.ayaklar.map((a) => { const m = veri.maclar.find((x) => x.id === a.id); return m ? durumAd(olan(m, a.kod)) : ''; });
    const yatti = dur.includes('tutmadi');
    const bitti = !yatti && dur.every(Boolean);
    const gercek = k.ayaklar.reduce((x, a, i) => x * (dur[i] === 'tuttu' ? a.oran : 1), 1);
    const sonuc = yatti ? '<span class="zimba tutmadi">Yattı</span>' : bitti ? `<span class="zimba tuttu">Tuttu · ${oranYaz(gercek)}</span>` : '';
    const ayak = (a, i) => `
      <li class="ayak ${dur[i]}">
        <span class="ayak-mac">${esc(a.saat)} · ${esc(a.mac)}</span>
        <span class="ayak-sec"><b>${esc(a.ad)}</b><span class="oran">${oranYaz(a.oran)}</span><span class="ayak-p">${yuzde(a.p)}</span>${dur[i] ? `<span class="zimba ${dur[i]}">${ZIMBA[dur[i]]}</span>` : ''}</span>
      </li>`;
    return `<article class="kombin">
      <header class="kombin-bas"><div><b>${esc(k.ad)} kupon</b><small>deney · bahis tavsiyesi değil</small></div>
        <div class="kombin-oran">${oranYaz(k.oran)}<small>toplam oran</small></div></header>
      <ol class="ayaklar">${k.ayaklar.map(ayak).join('')}</ol>
      <div class="kombin-alt">${sonuc}
        <span>Tutma olasılığı <b>${yuzde(k.p)}</b> · 10 kuponun yaklaşık ${Math.round(k.p * 10)}${["'u", "'i", "'si", "'ü", "'ü", "'i", "'sı", "'si", "'i", "'u", "'u"][Math.round(k.p * 10)]}</span>
        <span>Beklenen getiri <b>%${isaretli((k.p * k.oran - 1) * 100, 0)}</b></span>
      </div>
    </article>`;
  }

  function kuponlar(gun) {
    const kl = (veri.kupon || {})[gun] || [];
    if (!kl.length) return '';
    return `<section class="kombin-alan" aria-label="Kupon">
      <h2 class="kombin-baslik">Günün kuponu <span>Güçlü sinyallerden, maç başı en olası tek ayak. Ayak sayısı arttıkça tutma olasılığı çarpılarak düşer.</span></h2>
      <div class="kombin-kartlar">${kl.map(kuponKarti).join('')}</div>
    </section>`;
  }

  // ---------------------------------------------------------------- bilet gövdesi
  function formSeridi(t) {
    return `<div class="form-seridi" aria-label="Son 5 maç">${t.maclar.slice(0, 5).map((x) => {
      const h = x.at > x.ye ? 'G' : x.at === x.ye ? 'B' : 'M';
      return `<span class="fs ${h}" title="${esc(x.rakip)} ${x.at}-${x.ye}">${h}</span>`;
    }).join('')}</div>`;
  }

  // ---------------------------------------------------------------- okuma
  function okumaBlok(m) {
    const o = m.okuma;
    if (!o) return '<div class="sinyal-yok">Bu maçta oran yok, okuma yapılamadı.</div>';
    const t = o.tahmin;
    const td = durumAd(olan(m, t.kod));
    const guvenAd = { 'yüksek': 'net favori', orta: 'hafif favori', 'düşük': 'açık maç' }[t.guven];
    const satir = (s) => {
      const d = durumAd(olan(m, s.kod));
      const sinif = s.seviye === 'Güçlü' ? 'guclu' : 'orta';
      const deger = s.deger != null && s.deger >= 0 && s.en_iyi > s.oran
        ? ` · <b class="deger">değerli fiyat ${oranYaz(s.en_iyi)}</b>` : '';
      return `
        <div class="sinyal ${d}">
          <div class="yuzde" style="--p:${Math.round(s.p * 100)}"><sup>%</sup>${Math.round(s.p * 100)}</div>
          <div class="ne"><span>${esc(s.ad)}</span>
            <span class="oran" title="Oran">${oranYaz(s.oran)}</span>
            <span class="etiket ${sinif}">${s.seviye}</span>
            ${d ? `<span class="zimba ${d}">${ZIMBA[d]}</span>` : ''}
          </div>
          <div class="kanit">${s.kanit ? esc(s.kanit) : 'Oranlardan temizlenmiş olasılık'}${deger}</div>
        </div>`;
    };
    const sg = o.sinyaller.length ? o.sinyaller.map(satir).join('')
      : `<div class="sinyal-yok"><b>Sinyal yok.</b> 1,35 ve üstü oranlarda hiçbir seçenek %56 olasılığa ulaşmıyor; maç her yöne açık.</div>`;
    const sn = o.senaryolar;
    const bar = sn.map((x) => `<span class="sn sn-${x.kod}" style="flex:${Math.max(x.p, 0.02)}" title="${esc(x.ad)} ${yuzde(x.p)}">${x.p >= 0.12 ? yuzde(x.p) : ''}</span>`).join('');
    const enIyi = [...sn].sort((a, b) => b.p - a.p).slice(0, 3);
    const c = o.cesur;
    const cd = c ? durumAd(olan(m, c.kod)) : '';
    return `
      <div class="tahmin ${td}">
        <div class="tahmin-ana"><small>Tahmin · ${guvenAd}</small><b>${esc(t.ad)}</b><span>${yuzde(t.p)}</span>${td ? `<span class="zimba ${td}">${ZIMBA[td]}</span>` : ''}</div>
        <div class="tahmin-skor${m.sonuc && m.sonuc.skor === o.skor.skor ? ' oldu' : ''}"><small>Skor</small><b>${esc(o.skor.skor.replace('-', '–'))}</b></div>
      </div>
      <div class="senaryo" aria-label="Senaryolar"><div class="sn-bar">${bar}</div>
        <ul class="sn-liste">${enIyi.map((x) => `<li><i class="sn-${x.kod}"></i>${esc(x.ad)} <b>${yuzde(x.p)}</b> <small>en olası ${esc(x.skor.replace('-', '–'))}</small></li>`).join('')}</ul>
      </div>
      <h4 class="bolum-baslik">Sinyaller <span>büyük rakam: olasılık · 1 TL yalnız Güçlü'ye</span></h4>
      ${sg}
      ${c ? `<div class="cesur ${cd}"><small>Cesur</small><b>${esc(c.ad)}</b><span>${yuzde(c.p)} · ${c.oran ? 'oran ' + oranYaz(c.oran) : 'adil oran ' + oranYaz(c.adil_oran)}</span>${cd ? `<span class="zimba ${cd}">${ZIMBA[cd]}</span>` : ''}</div>` : ''}`;
  }

  function skorlar(m) {
    const olanSkor = m.sonuc && m.sonuc.skor;
    return m.okuma.skorlar.slice(0, 3).map(([s, p], i) =>
      `<div class="skor${i === 0 ? ' ilk' : ''}${olanSkor === s ? ' oldu' : ''}"><b>${esc(s.replace('-', '–'))}</b><span>${yuzde(p)}</span></div>`).join('');
  }

  // ---------------------------------------------------------------- maç sonu
  // Satırlar: [başlık, alan, ondalık, önek]
  const MAC_SONU = [
    ['xG', 'xg', 2, ''],
    ['Şut', 'sut', 0, ''],
    ['İsabetli şut', 'isabetli', 0, ''],
    ['Net fırsat', 'buyuk', 0, ''],
    ['Ceza sahasında top', 'ceza', 0, ''],
    ['Korner', 'korner', 0, ''],
    ['Kart', 'kart', 0, ''],
    ['Topla oynama', 'topa', 0, '%'],
  ];

  function macSonu(m) {
    const s = m.sonuc, ist = s.ist || {};
    const soyad = (ad) => ad.replace(/^[A-ZÇĞİÖŞÜ]\.\s/, '');
    const olaylar = (t) => [
      ...(s.goller || []).filter((g) => g.taraf === t).map((g) => `${g.dk}' ${esc(soyad(g.oyuncu))}`),
      ...(s.kirmizi || []).filter((g) => g.taraf === t).map((g) => `<em>${g.dk}' ${esc(soyad(g.oyuncu))} kırmızı</em>`),
    ].join(', ') || '–';
    const satirlar = MAC_SONU.filter(([, k]) => ist[k]).map(([ad, k, n, on]) => {
      const [a, b] = ist[k];
      return `<tr><td class="${a > b ? 'fazla' : ''}">${on}${ondalik(a, n)}</td><th scope="row">${ad}</th><td class="${b > a ? 'fazla' : ''}">${on}${ondalik(b, n)}</td></tr>`;
    }).join('');
    const [l0, l1] = m.okuma ? m.okuma.lambda : m.model.lambda;
    return `<div class="mac-sonu">
      <h4 class="bolum-baslik">Maç sonu <span>İY ${esc((s.iy || '').replace('-', '–'))}</span></h4>
      <div class="ms-goller"><p>${olaylar('ev')}</p><p>${olaylar('dep')}</p></div>
      <table class="ms-tablo">${satirlar}</table>
      <p class="ms-bek">Oranların beklentisi: gol <b>${ondalik(l0)} – ${ondalik(l1)}</b>${m.model.korner ? ` · korner <b>${ondalik(m.model.korner)}</b>` : ''}${m.model.kart ? ` · kart <b>${ondalik(m.model.kart)}</b>` : ''}</p>
    </div>`;
  }

  // ---------------------------------------------------------------- koçan panelleri
  // Sütunlar: [başlık, açıklama, alan, ondalık]
  const SUTUNLAR = [
    ['xG', 'Gol beklentisi: pozisyonların gol olma ihtimali toplamı', 'xg', 2],
    ['İsabetli şut', 'Kaleyi bulan şut', 'isabetli', 1],
    ['Net fırsat', 'Gol olması beklenen büyük pozisyon', 'buyuk', 1],
    ['Ceza sahasında top', 'Ceza sahası içinde topla buluşma sayısı', 'ceza', 0],
    ['Korner', 'Kullanılan korner', 'korner', 1],
    ['Kart', 'Sarı + kırmızı kart', 'kart', 1],
  ];
  const cift = (a, b, n) => `<b>${a == null ? '–' : ondalik(a, n)}</b><i>–</i><small>${b == null ? '–' : ondalik(b, n)}</small>`;

  function macTablosu(t) {
    const satir = (x) => {
      const h = x.at > x.ye ? 'G' : x.at === x.ye ? 'B' : 'M';
      return `<tr>
        <td><span class="rakip">${esc(x.rakip)}</span><span class="tr">${esc(x.turnuva)} · ${x.evde ? 'iç saha' : 'dep.'} · ${esc(x.tarih.slice(8, 10) + '.' + x.tarih.slice(5, 7))}</span></td>
        <td><span class="sk ${h}">${x.at}-${x.ye}</span>${x.iy_at != null ? `<span class="tr">İY ${x.iy_at}-${x.iy_ye}</span>` : ''}</td>
        ${SUTUNLAR.map(([, , k, n]) => `<td class="cift">${cift(x[k + '_l'], x[k + '_a'], k === 'xg' ? 2 : 0)}</td>`).join('')}
        <td>${x.topa_l != null ? '%' + Math.round(x.topa_l) : '–'}</td>
        <td>${ondalik(x.ilk11_reyting, 2)}</td>
      </tr>`;
    };
    const ort = (ms, k) => { const v = ms.map((x) => x[k]).filter((v) => v != null); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; };
    const ozet = (n) => {
      const ms = t.maclar.slice(0, n);
      return `<tr><td>Son ${n} maç ort.</td><td>${ondalik(ort(ms, 'at'))}-${ondalik(ort(ms, 'ye'))}</td>
        ${SUTUNLAR.map(([, , k, d]) => `<td class="cift">${cift(ort(ms, k + '_l'), ort(ms, k + '_a'), d)}</td>`).join('')}
        <td>%${Math.round(ort(ms, 'topa_l'))}</td><td>${ondalik(ort(ms, 'ilk11_reyting'), 2)}</td></tr>`;
    };
    const turlar = [...new Set(t.maclar.map((x) => x.turnuva))].join(', ');
    return `<p class="okuma">Her hücre <b>${esc(t.ad)}</b> – <small>rakip</small>. Örnek: korner <b>5</b>–<small>11</small> → ${esc(t.ad)} 5, rakibi 11 korner kullandı.</p>
    <div class="tablo-kap"><table class="mac-tablo">
      <thead><tr><th>Rakip</th><th>Skor</th>${SUTUNLAR.map(([ad, ac]) => `<th title="${esc(ac)}">${ad}</th>`).join('')}<th title="Topa sahip olma yüzdesi">Topla oynama</th><th title="İlk 11'in maç reyting ortalaması (10 üzerinden)">İlk 11 reytingi</th></tr></thead>
      <tbody>${t.maclar.map(satir).join('')}</tbody>
      <tfoot>${ozet(5)}${ozet(10)}</tfoot>
    </table></div>
    <dl class="sozluk">${SUTUNLAR.slice(0, 4).map(([ad, ac]) => `<div><dt>${ad}</dt><dd>${ac}</dd></div>`).join('')}<div><dt>İlk 11 reytingi</dt><dd>İlk 11'in maç notu ortalaması (10 üzerinden)</dd></div></dl>
    <p class="not">Son ${t.maclar.length} resmî maç, tüm turnuvalar (${esc(turlar)}); hazırlık maçları hariç.</p>`;
  }

  function oyuncuPaneli(t, form, eksik) {
    const renk = (r) => Math.max(0.08, Math.min(0.95, (r - 6) / 2.2));
    const satir = (o) => {
      const son = [...o.son].reverse();
      while (son.length < 5) son.unshift(null);
      return `<div class="oyuncu${o.yok ? ' yok' : ''}">
        <div class="isim"><span>${esc(o.ad)}</span><small>${o.yok ? 'yok' : esc(o.mevki || '')}</small></div>
        <div class="seri5" aria-label="Son 5 maç reytingi">${son.map((r) => (r == null ? '<span class="r bosr"></span>' :
          `<span class="r${renk(r) > 0.55 ? ' koyu' : ''}" style="--a:${renk(r).toFixed(2)}">${ondalik(r)}</span>`)).join('')}</div>
        <div class="fo">${ondalik(o.form, 2)}</div>
        <div class="ga">${o.gol}+${o.asist}</div>
      </div>`;
    };
    const ilk = t.oyuncular.filter((o) => o.ilk11);
    const diger = t.oyuncular.filter((o) => !o.ilk11).slice(0, 8);
    return `<div class="form-ozet">
        <span>Muhtemel 11 formu <b>${ondalik(form.form, 2)}</b></span>
        <span>Olağan 11 <b>${ondalik(form.taban, 2)}</b></span>
        ${eksik.length ? `<span>Eksik: ${eksik.map(esc).join(', ')}</span>` : ''}
      </div>
      <div class="oyuncu-bas"><span>Oyuncu</span><span>Son 5 maç →</span><span>Form</span><span>G+A</span></div>
      ${ilk.map(satir).join('')}
      ${diger.length ? `<p class="grup-ara">Diğerleri</p>${diger.map(satir).join('')}` : ''}
      <p class="not">Form: son 5 maç reytingi, yeni maç daha ağır. G+A: son 10 maçta gol ve asist.</p>`;
  }

  function olasilikPaneli(m) {
    const o = m.okuma;
    const secili = new Set(o.sinyaller.map((x) => x.kod));
    const bitti = !!(m.sonuc && m.sonuc.skor);
    const gruplar = [...new Set(m.model.pazarlar.map((x) => x.grup))].sort((a, b) => GRUP_SIRA.indexOf(a) - GRUP_SIRA.indexOf(b));
    const olanYaz = (r) => (r === 'iade' ? '<span class="olan iade">İade</span>' : r === 1 ? '<span class="olan evet">✓</span>' : r === 0 ? '<span class="olan hayir">–</span>' : '');
    const govde = gruplar.map((g) => {
      const satirlar = m.model.pazarlar.filter((x) => x.grup === g && o.olasilik[x.kod] != null && !/^AH/.test(x.kod))
        .sort((a, b) => o.olasilik[b.kod] - o.olasilik[a.kod]);
      if (!satirlar.length) return '';
      return `<tr class="gr"><td colspan="${bitti ? 5 : 4}">${esc(g)}</td></tr>` + satirlar.map((x) =>
        `<tr class="${secili.has(x.kod) ? 'secili' : ''}${x.oran < 1.35 ? ' elendi' : ''}"><td>${esc(x.ad)}</td><td>${oranYaz(x.oran)}</td><td><b>${yuzde(o.olasilik[x.kod])}</b></td><td>${yuzde(x.gecmis)}</td>${bitti ? `<td>${olanYaz(olan(m, x.kod))}</td>` : ''}</tr>`).join('');
    }).join('');
    const mt = o.matris, enb = Math.max(...mt.flat());
    const olanSkor = m.sonuc && m.sonuc.skor;
    let h = '<div class="b"></div>' + mt[0].map((_, j) => `<div class="b">${j}</div>`).join('');
    mt.forEach((r, i) => {
      h += `<div class="b">${i}</div>` + r.map((v, j) => {
        const a = (v / enb) * 0.9;
        return `<div class="h${a > 0.55 ? ' koyu' : ''}${olanSkor === `${i}-${j}` ? ' oldu' : ''}" style="--a:${a.toFixed(3)}" title="${i}-${j}: ${yuzde(v)}">${Math.round(v * 100)}</div>`;
      }).join('');
    });
    return `<div class="tablo-kap"><table class="pazar-tablo tum">
        <thead><tr><th>Seçenek</th><th>Oran</th><th title="Oranlardan kesinti temizlenmiş olasılık">Olasılık</th><th title="İki takımın son 10 maçında bu sonucun sıklığı">Son 10</th>${bitti ? '<th title="Maçta gerçekleşti mi">Olan</th>' : ''}</tr></thead>
        <tbody>${govde}</tbody></table></div>
      <p class="bg">Oranların beklediği gol: <b>${ondalik(o.lambda[0], 2)} – ${ondalik(o.lambda[1], 2)}</b>. Soluk satırlar 1,35 altı: sinyal olamaz.</p>
      <div class="matris" role="img" aria-label="Skor olasılıkları yüzde">${h}</div>
      <div class="matris-alt"><span>Satır: ${esc(kisa(m.ev.ad))} golü</span><span>Sütun: ${esc(kisa(m.dep.ad))} golü · %</span></div>
      <p class="not">Olasılık: her pazarın oranlarından büro kesintisi temizlenir (güç yöntemi). Skor matrisi bu olasılıklara en iyi uyan beklenen golle kurulur. Yeşil satırlar sinyal.</p>`;
  }

  // ---------------------------------------------------------------- bilet
  function siraSatiri(m, t) {
    const o = m.onem && m.onem[t];
    if (!o) return '';
    const p = [o.avrupa && `${esc(o.avrupa.ad)} ${o.avrupa.sira}. · ${o.avrupa.puan} P`, o.lig && `${esc(o.lig.ad)} ${o.lig.sira}.`].filter(Boolean);
    return `<span class="sira-satir">${p.join('<br>')}${o.seviye === 'düşük' ? '<br><em>önemi az</em>' : ''}</span>`;
  }

  function durumPaneli(m) {
    const o = m.onem;
    if (!o) return '<p class="not">Bu maç için puan durumu yok.</p>';
    const kart = (t) => {
      const x = o[t], a = x.avrupa, l = x.lig;
      return `<div class="durum-kart">
        <h5>${esc(m[t].ad)}</h5>
        <dl>
          ${a ? `<div><dt>${esc(a.ad)}</dt><dd><b>${a.sira}.</b> sıra · ${a.puan} puan · ${a.oynanan} maç</dd></div>` : ''}
          ${l ? `<div><dt>${esc(l.ad)}</dt><dd><b>${l.sira}.</b> sıra · ${l.puan} puan · ${l.oynanan} maç${l.lider_fark > 0 ? ` · lidere ${l.lider_fark} puan` : ' · lider'}</dd></div>` : ''}
        </dl>
        ${x.metin ? `<p>${esc(x.metin)}</p>` : ''}
        <p class="mot ${x.seviye === 'düşük' ? 'dusuk' : ''}">Önem: <b>${esc(x.seviye)}</b>${x.carpan !== 1 ? ` · beklenen gol ×${ondalik(x.carpan, 2)}` : ' · modele etkisi yok'}</p>
      </div>`;
    };
    return `<div class="durum">${kart('ev')}${kart('dep')}</div>
      <p class="not">Lig aşaması ${o.lig_mac || LIG_MAC} maç: ilk 8 son 16'ya doğrudan, 9–24 arası play-off. Turu garantileyen ya da şansı kalmayan takımın beklenen golü biraz düşürülür.${o.tur ? ` Bu maç ${o.tur}. hafta.` : ''}</p>`;
  }
  const LIG_MAC = 8;

  function bilet(m) {
    const bitti = m.sonuc && m.sonuc.skor;
    const yer = [m.stad, m.yayin].filter(Boolean).map(esc).join(' · ');
    return `
    <article class="bilet" id="${esc(m.id)}" data-id="${esc(m.id)}" data-sekme="maclar" data-takim="ev">
      <div class="govde">
        <header class="bant${bitti ? ' bitti' : ''}">
          <div><span class="tur">${esc(m.turnuva)}</span><span class="yer">${yer}</span></div>
          <div class="saat">${bitti ? esc(m.sonuc.skor.replace('-', '–')) : esc(m.saat)}<small>${bitti ? 'Maç bitti' : tarihYaz(m.tarih, { day: 'numeric', month: 'long' })}</small></div>
        </header>
        <div class="takimlar">
          <div class="takim ev"><span class="rol">Ev</span><div class="ad"><h3 class="${uzunluk(m.ev.ad)}">${esc(m.ev.ad)}</h3></div>${formSeridi(m.ev)}${siraSatiri(m, 'ev')}</div>
          <div class="xg"><b>${m.okuma ? `${ondalik(m.okuma.lambda[0])} – ${ondalik(m.okuma.lambda[1])}` : '–'}</b><small>Beklenen gol</small></div>
          <div class="takim dep"><span class="rol">Deplasman</span><div class="ad"><h3 class="${uzunluk(m.dep.ad)}">${esc(m.dep.ad)}</h3></div>${formSeridi(m.dep)}${siraSatiri(m, 'dep')}</div>
        </div>
        <div class="ozet"><h2>${esc(m.baslik)}</h2>${m.ozet ? `<p>${esc(m.ozet)}</p>` : ''}</div>
        <section class="sinyaller" aria-label="Okuma">
          ${m.okuma && m.okuma.geriye ? '<p class="geriye">Geriye dönük: bu okuma maçtan sonra, maç öncesi oranlarla hesaplandı.</p>' : ''}
          ${okumaBlok(m)}
        </section>
        <section class="skorlar" aria-label="Olası skorlar">
          <h4 class="bolum-baslik">Olası skorlar</h4>
          <div class="skor-satir">${m.okuma ? skorlar(m) : ''}</div>
          ${bitti ? macSonu(m) : ''}
        </section>
      </div>
      <div class="kocan">
        <button class="kocan-ac" type="button" aria-expanded="false" aria-controls="c-${esc(m.id)}">
          <span class="yazi"><b>Verileri incele</b><span>Son 10 maç · oyuncu formu · puan durumu · olasılıklar</span></span>
          <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="10" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6.5 9l4.5 4.5L15.5 9" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <div class="cekmece" id="c-${esc(m.id)}"><div><div class="cekmece-ic"></div></div></div>
      </div>
    </article>`;
  }

  function cekmeceCiz(el) {
    const m = veri.maclar.find((x) => x.id === el.dataset.id);
    const sekme = el.dataset.sekme, taraf = el.dataset.takim;
    const sek = [['maclar', 'Son maçlar'], ['oyuncular', 'Oyuncular'], ['durum', 'Durum'], ['olasilik', 'Olasılık']];
    const takimSec = sekme === 'olasilik' || sekme === 'durum' ? '' :
      `<div class="takim-sec" role="group" aria-label="Takım">${['ev', 'dep'].map((t) =>
        `<button type="button" data-takim-sec="${t}" aria-pressed="${t === taraf}">${esc(m[t].ad)}</button>`).join('')}</div>`;
    let panel;
    if (sekme === 'maclar') panel = macTablosu(m[taraf]);
    else if (sekme === 'oyuncular') panel = oyuncuPaneli(m[taraf], m.model.form[taraf], m.kadro[taraf].eksik);
    else if (sekme === 'durum') panel = durumPaneli(m);
    else panel = m.okuma ? olasilikPaneli(m) : '<p class="not">Oran yok.</p>';
    $('.cekmece-ic', el).innerHTML = `
      <div class="sekmeler" role="tablist">${sek.map(([k, ad]) =>
        `<button type="button" class="sekme" role="tab" data-sekme-sec="${k}" aria-selected="${k === sekme}">${ad}</button>`).join('')}</div>
      ${takimSec}
      <div class="panel" role="tabpanel">${panel}</div>
      <p class="not">Veri çekildi: ${esc(m.veri_tarihi)} (TSİ) · ${m.kadro.kesin ? 'kesin 11' : 'muhtemel 11'}</p>`;
  }

  // ---------------------------------------------------------------- sayfa
  // İlk açılış: bugünün maçları; bugün maç yoksa en yakın gelecek gün, o da yoksa en son gün.
  function varsayilanGun() {
    const bugun = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Istanbul' }).format(new Date());
    if (gunler.includes(bugun)) return bugun;
    return [...gunler].reverse().find((g) => g > bugun) || gunler[0];
  }

  function ciz() {
    const istenen = decodeURIComponent(location.hash.slice(1));
    const gun = gunler.includes(istenen) ? istenen : varsayilanGun();
    const maclar = veri.maclar.filter((m) => m.tarih === gun)
      .sort(SIRALA[sira]);
    $('#gun-sec').value = gun;
    $('#karne').innerHTML = karne(gun);
    document.querySelectorAll('[data-sira]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.sira === sira));
    const altYazi = sira === 'guven' ? 'en güçlü sinyal önde' : 'saat sırasıyla';
    $('#gun-baslik').innerHTML = `${tarihYaz(gun, { day: 'numeric', month: 'long', weekday: 'long' })}<span>${maclar.length} maç · ${altYazi}, veriler koçanda</span>`;
    document.title = `Köşe Vuruşu · ${tarihYaz(gun, { day: 'numeric', month: 'long' })}`;
    $('#kombin').innerHTML = kuponlar(gun);
    $('#test').innerHTML = testOzet();
    $('#biletler').innerHTML = maclar.map(bilet).join('');
    sigdir();
  }

  // Geriye dönük test: tüm bitmiş maçlarda Güçlü sinyallerin isabeti ve 1 TL kasası (model/okuma.py --test).
  function testOzet() {
    const t = veri.okuma_test;
    if (!t || !t.secim || !t.secim['Güçlü']) return '';
    const g = t.secim['Güçlü'], o = t.secim['Orta'];
    return `<p class="test-ozet"><b>Okuma, ${t.mac} bitmiş maçta:</b> Güçlü ${g.tuttu}/${g.n} (%${Math.round((g.tuttu / g.n) * 100)}), 1 TL kasası <b>${isaretli(g.kasa, 1)} TL</b> (oranların beklediği ${isaretli(g.beklenen_kasa, 1)}).`
      + `${o ? ` Orta ${o.tuttu}/${o.n} (%${Math.round((o.tuttu / o.n) * 100)}).` : ''} Kasa uzun vadede kesinti kadar eksidedir; artıya geçmenin yolu daha iyi fiyat.</p>`;
  }

  // Takım adı en fazla iki satıra ve sütuna sığana kadar yazıyı küçült; kelime ortadan bölünmesin.
  function sigdir() {
    document.querySelectorAll('.takim h3').forEach((h) => {
      h.style.fontSize = '';
      let boy = parseFloat(getComputedStyle(h).fontSize);
      const kutu = h.parentElement.clientHeight;
      while ((h.scrollWidth > h.clientWidth + 1 || h.offsetHeight > kutu + 1) && boy > 14) {
        boy -= 1;
        h.style.fontSize = boy + 'px';
      }
    });
  }
  let sigdirZaman;
  window.addEventListener('resize', () => { clearTimeout(sigdirZaman); sigdirZaman = setTimeout(sigdir, 120); });
  if (document.fonts) document.fonts.ready.then(() => sigdir());

  document.addEventListener('click', (e) => {
    const sb = e.target.closest('[data-sira]');
    if (sb) {
      if (sb.dataset.sira === sira) return;
      sira = sb.dataset.sira;
      try { localStorage.setItem('sira', sira); } catch (err) { /* depolama kapalı */ }
      ciz();
      return;
    }
    const el = e.target.closest('.bilet');
    if (!el) return;
    if (e.target.closest('.kocan-ac')) {
      const acik = el.classList.toggle('acik');
      e.target.closest('.kocan-ac').setAttribute('aria-expanded', acik);
      if (acik && !$('.cekmece-ic', el).children.length) cekmeceCiz(el);
      return;
    }
    const el2 = e.target.closest('[data-elenen]');
    if (el2) {
      const tablo = el.querySelector('.pazar-tablo');
      const acik = tablo.classList.toggle('tum');
      el2.setAttribute('aria-pressed', acik);
      el2.textContent = acik ? 'Elenenleri gizle' : el2.textContent.replace('gizle', 'göster');
      return;
    }
    const s = e.target.closest('[data-sekme-sec]');
    if (s) { el.dataset.sekme = s.dataset.sekmeSec; cekmeceCiz(el); $(`[data-sekme-sec="${el.dataset.sekme}"]`, el).focus(); return; }
    const t = e.target.closest('[data-takim-sec]');
    if (t) { el.dataset.takim = t.dataset.takimSec; cekmeceCiz(el); $(`[data-takim-sec="${el.dataset.takim}"]`, el).focus(); }
  });

  async function basla() {
    try {
      const r = await fetch('data/tahminler.json?v=' + Date.now());
      if (!r.ok) throw new Error(r.status);
      veri = await r.json();
    } catch (e) {
      $('#biletler').innerHTML = '<p class="bos">Biletler yüklenemedi. Sayfayı yenileyip tekrar dene.</p>';
      return;
    }
    if (!veri.maclar || !veri.maclar.length) {
      $('#biletler').innerHTML = '<p class="bos">Henüz maç yok.</p>';
      return;
    }
    gunler = [...new Set(veri.maclar.map((m) => m.tarih))].sort().reverse();
    $('#gun-sec').innerHTML = gunler.map((g) => `<option value="${g}">${tarihYaz(g, { day: 'numeric', month: 'long' })}</option>`).join('');
    $('#gun-sec').addEventListener('change', (e) => { location.hash = e.target.value; });
    window.addEventListener('hashchange', ciz);
    ciz();
  }

  basla();
})();
