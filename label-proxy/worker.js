/* Visser Inspecties — server voor de tools (Cloudflare Worker).
   1) Energielabels uit EP-Online (Pand analyse; gebaseerd op de worker van Erkend-Energielabel.nl).
   2) Kwaliteitsverklaringen uit de BCRG-databank (altijd actueel):  /bcrg?search=…  /bcrg/<id>  /bcrg-pdf?u=…
   3) Typeplaatje herkennen met Cloudflare Workers AI (binding met de naam AI):  POST /herken  {beeld:"data:image/jpeg;base64,…"}
   - Met variabele EP_KEY (gratis EP-Online API-key): officiële webservice.
   - Zonder EP_KEY: het openbare zoekscherm van www.ep-online.nl.
   Aanroep:  GET https://<worker>/?q=3343DA%2045&vbo=0531010000000065                                  */
const TOEGESTAAN = ['https://visserinspecties.github.io', 'http://localhost', 'http://127.0.0.1'];
const SITE = 'https://www.ep-online.nl/Energylabel/Search';
const API = 'https://public.ep-online.nl/api/v5/PandEnergielabel';

export default {
  async fetch(req, env, ctx) {
    const origin = req.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': '*',   /* openbare gegevens: elke plek waar de app draait (ook tablet/bestand) */
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin'
    };
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    const url = new URL(req.url);
    if (url.pathname === '/bcrg' || url.pathname.startsWith('/bcrg/')) return bcrg(url, cors);
    if (url.pathname === '/bcrg-pdf') return bcrgPdf(url, cors);
    if (url.pathname === '/gh-release') return ghRelease(url, cors);
    if (url.pathname === '/herken') {
      if (req.method !== 'POST') return json({ fout: 'Gebruik POST' }, 405, cors);
      if (!TOEGESTAAN.some(o => origin.startsWith(o))) return json({ fout: 'Niet toegestaan vanaf deze website' }, 403, cors);
      return herken(req, env, cors);
    }
    const bron = env.EP_KEY ? 'EP-Online webservice' : 'EP-Online (openbaar zoekscherm)';
    const sessie = { env };
    /* meerdere adressen tegelijk: ?b=3343DA 43~0531010000000063;3343DA 45~0531010000000065 (max 25) */
    if (url.searchParams.has('b')) {
      const items = url.searchParams.get('b').split(';').map(x => x.split('~')).slice(0, 25)
        .map(([q, v]) => ({ q: normQ(q), vbo: (v || '').replace(/\D/g, '') })).filter(x => x.q || x.vbo);
      const uit = new Array(items.length);
      let i = 0;
      const werker = async () => { while (i < items.length) { const k = i++; const it = items[k];
        try { const r = await zoekEen(it.q, it.vbo, sessie, ctx); uit[k] = { q: it.q, vbo: it.vbo, label: r.label }; }
        catch (e) { uit[k] = { q: it.q, vbo: it.vbo, fout: String(e.message || e) }; } } };
      await Promise.all([werker(), werker(), werker(), werker()]);
      return json({ bron, resultaten: uit }, 200, cors);
    }
    const q = normQ(url.searchParams.get('q'));
    const vbo = (url.searchParams.get('vbo') || '').replace(/\D/g, '');
    if (!/^\d{4} ?[A-Z]{2} \d+/.test(q) && !vbo) return json({ fout: 'Geef q=postcode huisnummer (bv. 3343DA 45) en/of vbo=BAG-verblijfsobject-id' }, 400, cors);
    try {
      const r = await zoekEen(q, vbo, sessie, ctx);
      return json({ q, vbo, bron, label: r.label, alle: r.alle, opgehaald: new Date().toISOString() }, 200, { ...cors, 'Cache-Control': 'public, max-age=86400' });
    } catch (e) { return json({ fout: 'EP-Online niet bereikbaar: ' + (e.message || e) }, 502, cors); }
  }
};

const normQ = q => String(q || '').trim().toUpperCase().replace(/\s+/g, ' ');
async function zoekEen(q, vbo, sessie, ctx) {
  const env = sessie.env;
  const sleutel = new Request('https://cache.label/v2/' + encodeURIComponent(q + '|' + vbo + '|' + (env.EP_KEY ? 'api' : 'site')));
  const hit = await caches.default.match(sleutel);
  if (hit) return await hit.json();
  let labels;
  if (env.EP_KEY) labels = await viaApi(q, vbo, env.EP_KEY);
  else { labels = await viaSite(vbo || q, sessie); if (!labels.length && vbo && q) labels = await viaSite(q, sessie); }
  labels.sort((a, b) => (a.ingetrokken ? 1 : 0) - (b.ingetrokken ? 1 : 0) || datum(b.registratiedatum) - datum(a.registratiedatum));
  const passend = vbo ? labels.filter(l => l.vbo === vbo) : labels;
  const r = { label: passend[0] || (vbo && labels.length === 1 ? labels[0] : (vbo ? null : labels[0])) || null, alle: labels };
  ctx.waitUntil(caches.default.put(sleutel, new Response(JSON.stringify(r), { headers: { 'Content-Type': 'application/json', 'Cache-Control': 'public, max-age=86400' } })));
  return r;
}

const json = (o, s, h) => new Response(JSON.stringify(o), { status: s, headers: { 'Content-Type': 'application/json; charset=utf-8', ...h } });
const datum = d => { const m = /(\d{2})-(\d{2})-(\d{4})/.exec(d || ''); return m ? +(m[3] + m[2] + m[1]) : 0; };
const schoon = s => String(s || '').replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&sup2;/g, '²').replace(/&nbsp;/g, ' ').replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCharCode(parseInt(h, 16))).replace(/&#(\d+);/g, (_, d) => String.fromCharCode(+d)).replace(/\s+/g, ' ').trim();
const leeg = v => (v == null || v === '-' || v === '' ? null : v);

/* ---------- openbaar zoekscherm ---------- */
async function sessieStart(sessie) {
  if (sessie.token) return sessie;
  if (!sessie.bezig) sessie.bezig = (async () => {
    const r1 = await fetch(SITE, { headers: KOP });
    const html1 = await r1.text();
    const token = (/name="__RequestVerificationToken"[^>]*value="([^"]+)"/.exec(html1) || /value="([^"]+)"[^>]*name="__RequestVerificationToken"/.exec(html1) || [])[1];
    if (!token) throw new Error('geen formulier-token');
    sessie.koekjes = (r1.headers.getSetCookie ? r1.headers.getSetCookie() : (r1.headers.get('set-cookie') || '').split(/,(?=\s*[^;,]+=)/))
      .map(c => c.split(';')[0].trim()).filter(Boolean).join('; ');
    sessie.token = token;
  })();
  await sessie.bezig; return sessie;
}
const KOP = { 'User-Agent': 'Mozilla/5.0 (Erkend-Energielabel.nl pand analyse)', 'Accept': 'text/html' };
async function viaSite(zoek, sessie) {
  await sessieStart(sessie);
  const body = new URLSearchParams({ SearchValue: zoek, __RequestVerificationToken: sessie.token });
  const r2 = await fetch(SITE, { method: 'POST', headers: { ...KOP, 'Content-Type': 'application/x-www-form-urlencoded', 'Cookie': sessie.koekjes, 'Origin': 'https://www.ep-online.nl', 'Referer': SITE }, body });
  if (!r2.ok) throw new Error('zoeken HTTP ' + r2.status);
  return parseSite(await r2.text());
}
function parseSite(html) {
  const blokken = html.split(/<div class="se-result-item[^"]*"/).slice(1);
  return blokken.map(b => {
    const v = {};
    const re = /se-item-description[^"]*"[^>]*>\s*<span[^>]*>([\s\S]*?)<\/span>\s*<\/div>\s*<div class="[^"]*se-item-(?:value|number)[^"]*"[^>]*>\s*(?:<span[^>]*>([\s\S]*?)<\/span>)?/g;
    let m; while ((m = re.exec(b))) { const k = schoon(m[1]); if (!(k in v)) v[k] = schoon(m[2]); }
    const adres = schoon((/sort-value-pht[^>]*>([\s\S]*?)<\/span>/.exec(b) || [])[1]);
    const status = schoon((/Status van het energielabel:<\/span>[\s\S]*?<span[^>]*>([\s\S]*?)<\/span>/.exec(b) || [])[1]);
    const getal = k => { const x = leeg(v[k]); if (x == null) return null; const n = parseFloat(x.replace(/[^\d,-]/g, '').replace(',', '.')); return isNaN(n) ? null : n; };
    const functie = (/data-filter-value-function="(\w+)"/.exec(b) || [])[1] || null;
    return {
      adres, status: status || null, functie: functie === 'residential' ? 'woning' : functie === 'utility' ? 'utiliteit' : functie,
      klasse: leeg(v['Labelklasse'] || v['Energieklasse']),
      vbo: leeg(v['BAG verblijfsobject id']), pand: leeg(v['BAG pand id']),
      registratienummer: leeg(v['Registratienummer']),
      registratiedatum: leeg(v['Registratiedatum']), opnamedatum: leeg(v['Opnamedatum']), geldigTot: leeg(v['Geldig tot']),
      certificaathouder: leeg(v['Certificaathouder']), ingetrokken: leeg(v['Ingetrokken']),
      statusRegistratie: leeg(v['Status']), soortOpname: leeg(v['Soort opname']), berekening: leeg(v['Berekening volgens']),
      ag: getal('Gebr. opp. thermische zone'),
      energiebehoefte: getal('Energiebehoefte'), ep2: getal('Prim. fossiel energiegebruik'),
      hernieuwbaar: getal('Aandeel hernieuwbare energie'), warmtebehoefte: getal('Warmtebehoefte'),
      energieindex: getal('Energie-index') ?? getal('Energieindex')
    };
  }).filter(l => l.klasse || l.vbo);
}

/* ---------- officiële webservice (met API-key) ---------- */
async function viaApi(q, vbo, key) {
  let u;
  if (vbo) u = `${API}/AdresseerbaarObject/${vbo}`;
  else {
    const m = /^(\d{4}) ?([A-Z]{2}) (\d+)\s*([A-Z])?(?:[- ]?(\w+))?$/.exec(q);
    if (!m) throw new Error('adres niet herkend');
    u = `${API}/Adres?postcode=${m[1]}${m[2]}&huisnummer=${m[3]}` + (m[4] ? `&huisletter=${m[4]}` : '') + (m[5] ? `&huisnummertoevoeging=${m[5]}` : '');
  }
  const r = await fetch(u, { headers: { Authorization: key, Accept: 'application/json' } });
  if (r.status === 404) return [];
  if (!r.ok) throw new Error('webservice HTTP ' + r.status);
  const d = await r.json();
  const nl = s => { if (!s) return null; const t = new Date(s); return isNaN(t) ? s : t.toLocaleDateString('nl-NL', { day: '2-digit', month: '2-digit', year: 'numeric' }).replace(/\//g, '-'); };
  return (Array.isArray(d) ? d : [d]).map(x => ({
    adres: [x.Postcode, x.Huisnummer, x.Huisletter, x.Huisnummertoevoeging].filter(Boolean).join(' '),
    status: x.Status || null, klasse: x.Energieklasse || x.Labelklasse || null,
    vbo: x.BAGVerblijfsobjectID || null, pand: x.BAGPandID || null, registratienummer: x.Registratienummer || null,
    registratiedatum: nl(x.Registratiedatum), opnamedatum: nl(x.Opnamedatum), geldigTot: nl(x.Geldig_tot || x.GeldigTot),
    certificaathouder: x.Certificaathouder || null, ingetrokken: x.Ingetrokken ? 'ja' : null,
    statusRegistratie: x.Gebouwklasse || null, soortOpname: x.SoortOpname || null, berekening: x.Berekeningstype || null,
    ag: x.Gebruiksoppervlakte_thermische_zone ?? null, energiebehoefte: x.Energiebehoefte ?? null,
    ep2: x.PrimaireFossieleEnergie ?? null, hernieuwbaar: x.Aandeel_hernieuwbare_energie ?? null,
    warmtebehoefte: x.Warmtebehoefte ?? null, energieindex: x.EnergieIndex ?? null
  }));
}


/* ================= BCRG: kwaliteitsverklaringen ================= */
const BCRG = 'https://mijn.bcrg.nl/api/v1/declarations/';
async function bcrg(url, cors) {
  const id = url.pathname.replace(/^\/bcrg\/?/, '').replace(/\/$/, '');
  let doel;
  if (id) { if (!/^[0-9a-f-]{36}$/i.test(id)) return json({ fout: 'Ongeldig id' }, 400, cors); doel = BCRG + id + '/'; }
  else {
    const q = new URLSearchParams();
    for (const k of ['search', 'category', 'declaration_type', 'ordering', 'limit', 'offset']) { const v = url.searchParams.get(k); if (v) q.set(k, v); }
    if (!q.has('limit')) q.set('limit', '20');
    doel = BCRG + '?' + q.toString();
  }
  try {
    const r = await fetch(doel, { headers: { Accept: 'application/json', 'User-Agent': 'VisserInspecties-tools/1.0' }, cf: { cacheTtl: 600, cacheEverything: true } });
    return new Response(await r.text(), { status: r.status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'public, max-age=600', ...cors } });
  } catch (e) { return json({ fout: 'BCRG niet bereikbaar: ' + (e.message || e) }, 502, cors); }
}
async function bcrgPdf(url, cors) {
  const u = url.searchParams.get('u') || '';
  if (!/^https:\/\/mijn\.bcrg\.nl\/media\/[\w\/.\-%]+\.pdf$/i.test(u)) return json({ fout: 'Alleen pdf-documenten van mijn.bcrg.nl' }, 400, cors);
  const r = await fetch(u, { cf: { cacheTtl: 86400, cacheEverything: true } });
  if (!r.ok) return json({ fout: 'Pdf niet gevonden (' + r.status + ')' }, r.status, cors);
  return new Response(r.body, { headers: { 'Content-Type': 'application/pdf', 'Cache-Control': 'public, max-age=86400', ...cors } });
}

/* ================= Typeplaatje herkennen (Workers AI) ================= */
const VRAAG = 'Dit is een foto van een typeplaatje, label of datablad van een installatie of bouwproduct (bijv. cv-ketel, warmtepomp, zonnepaneel, boiler, WTW-unit, isolatie, glas). ' +
  'Lees de tekst en geef ALLEEN een JSON-object terug, zonder uitleg, met deze velden: ' +
  '{"merk":"fabrikant/merk","type":"productnaam en type zoals op het plaatje, bv. Avanta Ace 28c CCS","typenummer":"artikel- of typenummer indien aanwezig","productsoort":"bv. cv-ketel, warmtepomp, pv-paneel, boiler, ventilatie-unit","codes":["andere belangrijke codes"],"tekst":"korte samenvatting van de belangrijkste technische gegevens op het plaatje"}. ' +
  'Laat een veld leeg ("") als je het niet kunt lezen. Verzin niets.';
async function herken(req, env, cors) {
  if (!env.AI) return json({ fout: 'Workers AI is nog niet gekoppeld: voeg in Cloudflare bij Settings → Bindings een Workers AI-binding toe met de naam AI.' }, 500, cors);
  let body; try { body = await req.json(); } catch (e) { return json({ fout: 'Geen geldige aanvraag' }, 400, cors); }
  const dataUrl = String(body.beeld || '');
  const m = /^data:image\/(jpeg|jpg|png|webp);base64,([A-Za-z0-9+/=]+)$/.exec(dataUrl);
  if (!m) return json({ fout: 'Stuur een foto (jpeg/png) als data-URL' }, 400, cors);
  if (m[2].length > 6_000_000) return json({ fout: 'Foto te groot' }, 413, cors);
  const bytes = Uint8Array.from(atob(m[2]), c => c.charCodeAt(0));
  const pogingen = [
    ['@cf/meta/llama-4-scout-17b-16e-instruct', () => ({ messages: [{ role: 'user', content: [{ type: 'text', text: VRAAG }, { type: 'image_url', image_url: { url: dataUrl } }] }], max_tokens: 700, temperature: 0 })],
    ['@cf/mistralai/mistral-small-3.1-24b-instruct', () => ({ messages: [{ role: 'user', content: [{ type: 'text', text: VRAAG }, { type: 'image_url', image_url: { url: dataUrl } }] }], max_tokens: 700, temperature: 0 })],
    ['@cf/meta/llama-3.2-11b-vision-instruct', () => ({ messages: [{ role: 'user', content: VRAAG }], image: Array.from(bytes), max_tokens: 700, temperature: 0 })],
    ['@cf/llava-hf/llava-1.5-7b-hf', () => ({ image: Array.from(bytes), prompt: VRAAG, max_tokens: 512 })]
  ];
  const fouten = [];
  for (const [model, invoer] of pogingen) {
    try {
      let r;
      try { r = await env.AI.run(model, invoer()); }
      catch (e) {
        if (/agree/i.test(String(e.message || e))) { await env.AI.run(model, { prompt: 'agree' }); r = await env.AI.run(model, invoer()); }
        else throw e;
      }
      const tekst = typeof r === 'string' ? r : (r.response ?? r.description ?? r.result?.response ?? JSON.stringify(r));
      const data = leesJson(typeof tekst === 'string' ? tekst : JSON.stringify(tekst));
      if (data && (data.merk || data.type || data.typenummer)) return json({ model, ...data }, 200, cors);
      fouten.push(model + ': niets herkend');
    } catch (e) { fouten.push(model + ': ' + String(e.message || e).slice(0, 160)); }
  }
  return json({ fout: 'Typeplaatje niet herkend. Probeer een scherpere foto of typ het type.', details: fouten }, 422, cors);
}
function leesJson(t) {
  if (t && typeof t === 'object') return t;
  const a = t.indexOf('{'), b = t.lastIndexOf('}');
  if (a < 0 || b <= a) return null;
  try { return JSON.parse(t.slice(a, b + 1)); } catch (e) { try { return JSON.parse(t.slice(a, b + 1).replace(/,\s*([}\]])/g, '$1')); } catch (_) { return null; } }
}

/* Bijlage van een GitHub-release doorgeven (GitHub staat downloaden vanuit een website niet toe).
   Alleen release-bijlagen van visserinspecties; gebruikt door de tool GitHub archief.
   Voorbeeld: /gh-release?u=https://github.com/visserinspecties/foto-upload/releases/download/<tag>/<bestand> */
async function ghRelease(url, cors) {
  const u = url.searchParams.get('u') || '';
  if (!/^https:\/\/github\.com\/visserinspecties\/[\w.-]+\/releases\/download\/[^/]+\/[^/]+$/.test(u))
    return json({ fout: 'Alleen release-bijlagen van visserinspecties' }, 400, cors);
  const r = await fetch(u, { redirect: 'follow', headers: { 'User-Agent': 'VisserInspecties-tools/1.0' } });
  if (!r.ok) return json({ fout: 'GitHub gaf ' + r.status }, r.status, cors);
  const h = { ...cors, 'Content-Type': r.headers.get('Content-Type') || 'application/octet-stream' };
  if (r.headers.get('Content-Length')) h['Content-Length'] = r.headers.get('Content-Length');
  return new Response(r.body, { headers: h });
}
