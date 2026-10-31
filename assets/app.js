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

  // Güvenilirlik: en iyi önerinin seviyesi (Güçlü > Orta > yok), sonra puanı; eşitlikte saat.
  const SEVIYE = { 'Güçlü': 2, 'Orta': 1 };
  const guven = (m) => Math.max(0, ...m.oneriler.map((o) => (SEVIYE[o.seviye] || 0) + o.puan));
  const SIRALA = {
    saat: (a, b) => a.saat.localeCompare(b.saat) || (b.manset - a.manset),
    guven: (a, b) => guven(b) - guven(a) || a.saat.localeCompare(b.saat),
  };

  // ---------------------------------------------------------------- karne
  // Seçili günün sinyal isabeti (toplam, Güçlü, Orta), Güçlü sanal getirisi ve skor isabeti. Yalnız gün bazında:
  // model sık güncellendiği için tüm dönemin oranı anlamlı değil.
  function sayim(maclar, seviye) {
    const biten = maclar.filter((m) => m.sonuc && m.sonuc.isabet);
    const sec = biten.flatMap((m) => {
      const sv = Object.fromEntries(m.oneriler.map((o) => [o.kod, o.seviye]));
      return (m.sonuc.isabet.oneriler || []).filter((o) => o.tuttu != null && (!seviye || sv[o.kod] === seviye));
    });
    return { mac: biten.length, sec: sec.length, tut: sec.filter((o) => o.tuttu).length, skor: biten.filter((m) => m.sonuc.isabet.skor).length };
  }
  const oran = (s) => (s.sec ? '%' + Math.round((s.tut / s.sec) * 100) : '–');
  // Sanal getiri: her öneriye 1 ₺, tutarsa oran − 1 kâr, tutmazsa 1 ₺ kayıp; iade sayılmaz.
  function getiri(maclar, seviye) {
    let say = 0, kar = 0;
    maclar.filter((m) => m.sonuc && m.sonuc.isabet).forEach((m) => {
      const on = Object.fromEntries(m.oneriler.map((o) => [o.kod, o]));
      (m.sonuc.isabet.oneriler || []).forEach((r) => {
        const o = on[r.kod];
        if (!o || o.seviye !== seviye || r.tuttu == null || r.iade) return;
        say += 1;
        kar += r.tuttu ? o.oran - 1 : -1;
      });
    });
    return { say, kar };
  }
  const isaretli = (v, h) => (v > 0 ? '+' : v < 0 ? '−' : '') + ondalik(Math.abs(v), h);
  const getiriYuzde = (g) => (g.say ? '%' + isaretli((g.kar / g.say) * 100, 0) : '–');
  const blok = (ad, tut, say, alt, sinif = '') =>
    `<span class="karne-blok ${sinif}"><small>${ad}</small><b>${tut}/${say}</b><small>${alt}</small></span>`;

  function karne(gun) {
    const gm = veri.maclar.filter((m) => m.tarih === gun);
    const g = sayim(gm);
    if (!g.mac) return '<span class="karne-blok"><small>Bu gün</small><b>bekleniyor</b></span>';
    const G = sayim(gm, 'Güçlü');
    const O = sayim(gm, 'Orta');
    const gg = getiri(gm, 'Güçlü');
    const kasa = gg.say
      ? `<span class="karne-blok karne-getiri ${gg.kar >= 0 ? 'arti' : 'eksi'}" title="Her Güçlü öneriye 1 ₺ yatırılmış gibi; gerçek para değil.">`
        + `<small>Güçlü · 1 ₺</small><b>${isaretli(gg.kar, 2)} ₺</b><small>${getiriYuzde(gg)}</small></span>`
      : '';
    return blok('Sinyal', g.tut, g.sec, oran(g))
      + blok('Güçlü', G.tut, G.sec, oran(G), 'guclu')
      + kasa
      + blok('Orta', O.tut, O.sec, oran(O))
      + blok('Skor', g.skor, g.mac, oran({ tut: g.skor, sec: g.mac }), 'karne-skor');
  }

  // ---------------------------------------------------------------- bilet gövdesi
  function formSeridi(t) {
    return `<div class="form-seridi" aria-label="Son 5 maç">${t.maclar.slice(0, 5).map((x) => {
      const h = x.at > x.ye ? 'G' : x.at === x.ye ? 'B' : 'M';
      return `<span class="fs ${h}" title="${esc(x.rakip)} ${x.at}-${x.ye}">${h}</span>`;
    }).join('')}</div>`;
  }

  function sinyaller(m) {
    const is = m.sonuc && m.sonuc.isabet ? Object.fromEntries(m.sonuc.isabet.oneriler.map((o) => [o.kod, o])) : null;
    const satir = (o, seviye) => {
      const r = is && is[o.kod];
      const durum = !r ? '' : r.iade ? 'iade' : r.tuttu == null ? '' : r.tuttu ? 'tuttu' : 'tutmadi';
      const [eo, en] = o.gecmis_ev || [], [dO, dn] = o.gecmis_dep || [];
      const gec = o.gecmis == null ? '' : ` · Son 10: <b>${esc(kisa(m.ev.ad))} ${sayiYaz(eo)}/${en}</b>, <b>${esc(kisa(m.dep.ad))} ${sayiYaz(dO)}/${dn}</b>`;
      const fark = o.ayrisma == null ? '' : ` · Fark <b>${o.ayrisma >= 0 ? '+' : '−'}%${Math.round(Math.abs(o.ayrisma) * 100)}</b>`;
      const sinif = { 'Güçlü': 'guclu', Orta: 'orta', Fikir: 'fikir' }[seviye];
      return `
        <div class="sinyal ${durum}${seviye === 'Fikir' ? ' fikir' : ''}">
          <div class="yuzde" style="--p:${Math.round(o.puan * 100)}"><sup>%</sup>${Math.round(o.puan * 100)}</div>
          <div class="ne"><span>${esc(o.ad)}</span>
            <span class="oran" title="Oran">${oranYaz(o.oran)}</span>
            <span class="etiket ${sinif}">${esc(seviye)}</span>
            ${durum ? `<span class="zimba ${durum}">${{ tuttu: 'Tuttu', tutmadi: 'Tutmadı', iade: 'İade' }[durum]}</span>` : ''}
          </div>
          <div class="kanit">Model <b>${yuzde(o.model)}</b> · Piyasa <b>${yuzde(o.piyasa)}</b>${fark}${gec}</div>
        </div>`;
    };
    if (!m.oneriler.length && ['v6.5', 'v6.6'].includes(m.model.surum)) {
      // Eşiği geçen yok: v6.5 kuralına uyan pazarlardan farkı en yüksek iki seçenek (farklı gruplardan) fikir olarak
      const uygun = m.model.pazarlar
        .filter((p) => p.ayrisma != null && p.oran >= 1.6 && p.oran <= 3.5 && !/^(AH|KOR|KART)/.test(p.kod))
        .sort((a, b) => b.ayrisma - a.ayrisma);
      const fikir = [], gr = new Set();
      for (const p of uygun) {
        if (gr.has(p.grup)) continue;
        gr.add(p.grup);
        fikir.push(p);
        if (fikir.length === 2) break;
      }
      return '<div class="sinyal-yok"><b>Değer sinyali yok.</b> Hiçbir seçenek eşiği geçmedi. Eşiğe en yakın seçenekler, yalnız fikir olarak:</div>'
        + fikir.map((p) => satir(p, 'Fikir')).join('');
    }
    if (!m.oneriler.length) {
      const yakin = m.model.pazarlar.filter((p) => !p.elendi).sort((a, b) => b.puan - a.puan)[0];
      return `<div class="sinyal-yok"><b>${oranYaz(m.oran_min)} üstü oranlarda sinyal yok.</b> Veri iki yöne de açık.${yakin ? ` En yakın: ${esc(yakin.ad)} @ ${oranYaz(yakin.oran)} (${yuzde(yakin.puan)}).` : ''}</div>`;
    }
    return m.oneriler.map((o) => satir(o, o.seviye)).join('');
  }

  function skorlar(m) {
    const olan = m.sonuc && m.sonuc.skor;
    return m.model.skorlar.slice(0, 3).map(([s, p], i) =>
      `<div class="skor${i === 0 ? ' ilk' : ''}${olan === s ? ' oldu' : ''}"><b>${esc(s.replace('-', '–'))}</b><span>${yuzde(p)}</span></div>`).join('');
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
    const [l0, l1] = m.model.lambda;
    return `<div class="mac-sonu">
      <h4 class="bolum-baslik">Maç sonu <span>İY ${esc((s.iy || '').replace('-', '–'))}</span></h4>
      <div class="ms-goller"><p>${olaylar('ev')}</p><p>${olaylar('dep')}</p></div>
      <table class="ms-tablo">${satirlar}</table>
      <p class="ms-bek">Bizim beklentimiz: gol <b>${ondalik(l0)} – ${ondalik(l1)}</b>${m.model.korner ? ` · korner <b>${ondalik(m.model.korner)}</b>` : ''}${m.model.kart ? ` · kart <b>${ondalik(m.model.kart)}</b>` : ''}</p>
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
    const secili = new Set(m.oneriler.map((o) => o.kod));
    const gruplar = [...new Set(m.model.pazarlar.map((x) => x.grup))].sort((a, b) => GRUP_SIRA.indexOf(a) - GRUP_SIRA.indexOf(b));
    const elenen = m.model.pazarlar.filter((x) => x.elendi).length;
    const bitti = !!(m.sonuc && m.sonuc.skor);
    // Olan: 1 tuttu, 0 yattı, 0.5 yarım, null iade
    const olanYaz = (v) => (v == null ? '<span class="olan iade">İade</span>' : v >= 0.75 ? '<span class="olan evet">✓</span>' : v > 0.25 ? '<span class="olan">½</span>' : '<span class="olan hayir">–</span>');
    const govde = gruplar.map((g) => {
      const satirlar = m.model.pazarlar.filter((x) => x.grup === g).sort((a, b) => a.elendi - b.elendi || b.puan - a.puan);
      return `<tr class="gr${satirlar.every((x) => x.elendi) ? ' elendi' : ''}"><td colspan="${bitti ? 6 : 5}">${esc(g)}</td></tr>` + satirlar.map((x) =>
        `<tr class="${secili.has(x.kod) ? 'secili' : ''}${x.elendi ? ' elendi' : ''}"><td>${esc(x.ad)}</td><td>${oranYaz(x.oran)}</td><td>${yuzde(x.model)}</td><td>${yuzde(x.gecmis)}</td><td><b>${yuzde(x.puan)}</b></td>${bitti ? `<td>${'olan' in x ? olanYaz(x.olan) : ''}</td>` : ''}</tr>`).join('');
    }).join('');
    const mt = m.model.matris, enb = Math.max(...mt.flat());
    const olan = m.sonuc && m.sonuc.skor;
    let h = '<div class="b"></div>' + mt[0].map((_, j) => `<div class="b">${j}</div>`).join('');
    mt.forEach((r, i) => {
      h += `<div class="b">${i}</div>` + r.map((v, j) => {
        const a = (v / enb) * 0.9;
        return `<div class="h${a > 0.55 ? ' koyu' : ''}${olan === `${i}-${j}` ? ' oldu' : ''}" style="--a:${a.toFixed(3)}" title="${i}-${j}: ${yuzde(v)}">${Math.round(v * 100)}</div>`;
      }).join('');
    });
    const [tb, l] = [m.model.taban, m.model.lambda];
    return `<div class="tablo-kap"><table class="pazar-tablo">
        <thead><tr><th>Seçenek</th><th>Oran</th><th>Model</th><th>Son 10</th><th>Puan</th>${bitti ? '<th title="Maçta gerçekleşti mi">Olan</th>' : ''}</tr></thead>
        <tbody>${govde}</tbody></table></div>
      ${elenen ? `<button type="button" class="elenen-ac" data-elenen aria-pressed="false">Oranı ${oranYaz(m.oran_min)} altı ve çok yüksek ${elenen} seçeneği göster</button>` : ''}
      <p class="bg">Beklenen gol: takım verisi <b>${ondalik(tb[0], 2)} – ${ondalik(tb[1], 2)}</b>, oyuncu formuyla <b>${ondalik(m.model.veri_l[0], 2)} – ${ondalik(m.model.veri_l[1], 2)}</b>${m.model.piyasa_l ? `, piyasa <b>${ondalik(m.model.piyasa_l[0], 2)} – ${ondalik(m.model.piyasa_l[1], 2)}</b>` : ''}. Kullanılan: <b>${ondalik(l[0], 2)} – ${ondalik(l[1], 2)}</b>${m.model.korner ? ` · beklenen korner <b>${ondalik(m.model.korner)}</b>, kart <b>${ondalik(m.model.kart)}</b>` : ''}.</p>
      <div class="matris" role="img" aria-label="Skor olasılıkları yüzde">${h}</div>
      <div class="matris-alt"><span>Satır: ${esc(kisa(m.ev.ad))} golü</span><span>Sütun: ${esc(kisa(m.dep.ad))} golü · %</span></div>
      <p class="not">${['v6.5', 'v6.6'].includes(m.model.surum) ? (m.model.surum === 'v6.6' ? 'Değer: beklenen gol yarı yarıya takımların son 10 maç xG verisinden ve oranlardan. Bu olasılık oranın ima ettiğinden en az %12 yüksekse Güçlü, %8–12 ise Orta. Oran 1,60–3,50; yalnız maç sonucu, ilk gol, ilk yarı ve karşılıklı gol; maç başı en fazla 2.' : 'Değer: model olasılığı oranın ima ettiğinden en az %8 yüksekse Güçlü, %5–8 ise Orta. Oran 1,60–3,50; korner, kart ve Asya handikabı hariç.') + ' Puan = %60 model, %25 son 10 maç, %15 piyasa. Yeşil satırlar seçilen sinyaller.' : `Puan = %60 model, %25 son 10 maç, %15 piyasa. Sinyal için oran ${oranYaz(m.oran_min)} ve üstü olmalı; ${['v1', 'v2', 'v3'].includes(m.model.surum) ? 'Güçlü için model piyasadan geride kalmamalı ama 12 puandan fazla da ayrışmamalı' : 'Güçlü için model en az %64, piyasa en az %60 olasılık vermeli'}${m.model.surum === 'v6' ? '; Orta için piyasa en az %55' : ''}. Yeşil satırlar seçilen sinyaller.`}</p>`;
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
          <div class="xg"><b>${ondalik(m.model.lambda[0])} – ${ondalik(m.model.lambda[1])}</b><small>Beklenen gol</small></div>
          <div class="takim dep"><span class="rol">Deplasman</span><div class="ad"><h3 class="${uzunluk(m.dep.ad)}">${esc(m.dep.ad)}</h3></div>${formSeridi(m.dep)}${siraSatiri(m, 'dep')}</div>
        </div>
        <div class="ozet"><h2>${esc(m.baslik)}</h2>${m.ozet ? `<p>${esc(m.ozet)}</p>` : ''}</div>
        <section class="sinyaller" aria-label="Veri ne diyor">
          <h4 class="bolum-baslik">Veri ne diyor <span>büyük rakam: 100 üzerinden puan</span></h4>
          ${sinyaller(m)}
        </section>
        <section class="skorlar" aria-label="Olası skorlar">
          <h4 class="bolum-baslik">Olası skorlar</h4>
          <div class="skor-satir">${skorlar(m)}</div>
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
    else panel = olasilikPaneli(m);
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
    const altYazi = sira === 'guven' ? 'en güvenilir sinyal önde' : 'saat sırasıyla';
    $('#gun-baslik').innerHTML = `${tarihYaz(gun, { day: 'numeric', month: 'long', weekday: 'long' })}<span>${maclar.length} maç · ${altYazi}, veriler koçanda</span>`;
    document.title = `Köşe Vuruşu · ${tarihYaz(gun, { day: 'numeric', month: 'long' })}`;
    $('#biletler').innerHTML = maclar.map(bilet).join('');
    sigdir();
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
