// Ham veri toplayıcı. Yerel sunucudaki sayfada (localhost) çalıştır:
//   const t = await import('/model/topla.js?' + Date.now());
//   await t.topla(MAC_ID, API_KOKU)          → ham/<MAC_ID>.json
//   await t.sonuc(MAC_ID, API_KOKU)          → ham/<MAC_ID>-sonuc.json
// API_KOKU repoda tutulmaz (kaynak adı repoda geçmez).

const sira = async (isler, n = 6) => {
  const out = new Array(isler.length);
  let i = 0;
  await Promise.all(Array.from({ length: n }, async () => {
    while (i < isler.length) { const k = i++; out[k] = await isler[k](); }
  }));
  return out;
};

function api(kok) {
  return async (yol) => {
    for (let deneme = 0; deneme < 3; deneme++) {
      const r = await fetch(kok + yol);
      if (r.ok) return r.json();
      if (r.status === 404) return null;
      await new Promise((ok) => setTimeout(ok, 600));
    }
    return null;
  };
}

const ISTAT = {
  expectedGoals: 'xg', shotsOnGoal: 'isabetli', totalShotsOnGoal: 'sut', bigChanceCreated: 'buyuk',
  touchesInOppBox: 'ceza', cornerKicks: 'korner', yellowCards: 'sari', redCards: 'kirmizi', ballPossession: 'topa',
};

function istatistik(j) {
  const t = j && (j.statistics || []).find((x) => x.period === 'ALL');
  if (!t) return null;
  const o = {};
  for (const g of t.groups) for (const it of g.statisticsItems) {
    if (ISTAT[it.key]) o[ISTAT[it.key]] = [it.homeValue, it.awayValue];
  }
  return o;
}

function kadro(t) {
  if (!t) return null;
  return {
    dizilis: t.formation || null,
    oyuncular: (t.players || []).map((p) => ({
      id: p.player.id, ad: p.player.shortName || p.player.name, mevki: p.player.position || p.position || '',
      yedek: !!p.substitute, r: p.statistics && p.statistics.rating || null,
      g: p.statistics && p.statistics.goals || 0, a: p.statistics && p.statistics.goalAssist || 0,
      dk: p.statistics && p.statistics.minutesPlayed || 0,
    })),
    eksik: (t.missingPlayers || []).map((m) => ({ id: m.player.id, ad: m.player.shortName || m.player.name, tur: m.type, neden: m.reason ?? null, aciklama: m.description || null })),
  };
}

function olayOzet(e) {
  return {
    id: e.id, ts: e.startTimestamp, turnuva: e.tournament.name,
    ut: e.tournament.uniqueTournament && e.tournament.uniqueTournament.id,
    ut_ad: e.tournament.uniqueTournament && e.tournament.uniqueTournament.name,
    kategori: e.tournament.category && e.tournament.category.name,
    sezon: e.season && e.season.id, tur: e.roundInfo || null,
    ev: { id: e.homeTeam.id, ad: e.homeTeam.name }, dep: { id: e.awayTeam.id, ad: e.awayTeam.name },
    skor: e.homeScore && e.homeScore.current != null ? [e.homeScore.current, e.awayScore.current] : null,
    iy: e.homeScore && e.homeScore.period1 != null ? [e.homeScore.period1, e.awayScore.period1] : null,
    durum: e.status && e.status.type, stad: e.venue && e.venue.name || null,
  };
}

async function sonMaclar(get, takim, once, n = 10) {
  let liste = [];
  for (let s = 0; s < 3 && liste.length < n + 4; s++) {
    const j = await get(`/team/${takim}/events/last/${s}`);
    if (!j) break;
    liste = liste.concat(j.events);
    if (!j.hasNextPage) break;
  }
  liste = liste.filter((e) => e.status && e.status.type === 'finished' && e.startTimestamp < once
    && !/friendl/i.test((e.tournament.uniqueTournament && e.tournament.uniqueTournament.name) || e.tournament.name))
    .sort((a, b) => b.startTimestamp - a.startTimestamp).slice(0, n);
  return sira(liste.map((e) => async () => {
    const [st, lu, inc] = await Promise.all([get(`/event/${e.id}/statistics`), get(`/event/${e.id}/lineups`), get(`/event/${e.id}/incidents`)]);
    const evde = e.homeTeam.id === takim;
    const goller = inc ? inc.incidents.filter((i) => i.incidentType === 'goal').sort((a, b) => a.time - b.time) : null;
    return {
      ...olayOzet(e), evde,
      ist: istatistik(st),
      kadro: lu ? kadro(evde ? lu.home : lu.away) : null,
      ilk_gol: goller == null ? '?' : goller.length ? (goller[0].isHome === evde ? 'biz' : 'rakip') : null,
    };
  }));
}

async function puanDurumu(get, ut, sezon) {
  const j = await get(`/unique-tournament/${ut}/season/${sezon}/standings/total`);
  if (!j || !j.standings) return null;
  return j.standings.map((s) => ({
    ad: s.name || s.tournament && s.tournament.name,
    satirlar: s.rows.map((r) => ({ id: r.team.id, ad: r.team.name, sira: r.position, puan: r.points, oynanan: r.matches })),
  }));
}

function oranlar(j) {
  if (!j || !j.markets) return null;
  return j.markets.map((m) => ({
    pazar: m.marketName, grup: m.choiceGroup ?? null,
    secenekler: m.choices.map((c) => [c.name, c.fractionalValue]),
  }));
}

function ligBul(maclar) {
  // takımın iç ligi: son maçlarında en sık görülen, kupa ve Avrupa olmayan turnuva
  const say = {};
  for (const m of maclar) {
    if (/UEFA|Cup|Kupa|Pokal|Coppa|Copa|Coupe|Trophy|Shield|Super Cup/i.test(m.ut_ad || '')) continue;
    const k = `${m.ut}|${m.sezon}|${m.ut_ad}`;
    say[k] = (say[k] || 0) + 1;
  }
  const en = Object.entries(say).sort((a, b) => b[1] - a[1])[0];
  return en ? { ut: +en[0].split('|')[0], sezon: +en[0].split('|')[1], ad: en[0].split('|')[2] } : null;
}

async function kaydet(ad, veri) {
  const r = await fetch(`/ham/${ad}.json`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(veri) });
  return r.text();
}

export async function topla(id, kok) {
  const get = api(kok);
  const ej = await get(`/event/${id}`);
  const e = ej.event;
  const [lu, od, evM, depM] = await Promise.all([
    get(`/event/${id}/lineups`), get(`/event/${id}/odds/1/all`),
    sonMaclar(get, e.homeTeam.id, e.startTimestamp), sonMaclar(get, e.awayTeam.id, e.startTimestamp),
  ]);
  const evLig = ligBul(evM), depLig = ligBul(depM);
  const [avrupa, evLigTablo, depLigTablo] = await Promise.all([
    puanDurumu(get, e.tournament.uniqueTournament.id, e.season.id),
    evLig ? puanDurumu(get, evLig.ut, evLig.sezon) : null,
    depLig ? puanDurumu(get, depLig.ut, depLig.sezon) : null,
  ]);
  const veri = {
    alindi: new Date().toISOString(), mac: olayOzet(e),
    kadro: lu ? { kesin: !!lu.confirmed, ev: kadro(lu.home), dep: kadro(lu.away) } : null,
    oranlar: oranlar(od),
    puan: { avrupa, ev: evLigTablo && { lig: evLig, tablolar: evLigTablo }, dep: depLigTablo && { lig: depLig, tablolar: depLigTablo } },
    ev: evM, dep: depM,
  };
  return kaydet(String(id), veri);
}

export async function sonuc(id, kok) {
  const get = api(kok);
  const [ej, st, lu, inc, od] = await Promise.all([get(`/event/${id}`), get(`/event/${id}/statistics`), get(`/event/${id}/lineups`), get(`/event/${id}/incidents`), get(`/event/${id}/odds/1/all`)]);
  const veri = {
    alindi: new Date().toISOString(), mac: olayOzet(ej.event), ist: istatistik(st),
    kadro: lu ? { ev: kadro(lu.home), dep: kadro(lu.away) } : null,
    oranlar: oranlar(od), // maç bitince dönen son oranlar = kapanış
    olaylar: inc ? inc.incidents.filter((i) => ['goal', 'card'].includes(i.incidentType)).map((i) => ({
      dk: i.time, tur: i.incidentType, sinif: i.incidentClass || null, ev: !!i.isHome, oyuncu: i.player && (i.player.shortName || i.player.name) || null,
    })) : null,
  };
  return kaydet(`${id}-sonuc`, veri);
}
