#!/usr/bin/env python3
"""Maakt pand-analyse.html (Visser Inspecties) uit de Pand analyse/Beslisschema-tool van
Erkend-Energielabel.nl (github.com/erkend-energielabel/beslisschemas, index.html).

Ombouw:
  - huisstijl Visser Inspecties (paars, logo, voettekst, PDF-kop en -voet)
  - invoer met postcode + huisnummer (+ toevoeging), adres via PDOK
  - OneDrive via de gedeelde inlog van de Visser-tools (login.js / inloggen.html)
    en projectkeuze in 0_In Behandeling; bestanden naar 020 AANTEKENINGEN
  - label-server: eigen Cloudflare Worker (in te stellen via ⚙ bij het energielabel)
  - home-knopje naar het dashboard

Gebruik (na een nieuwe versie van Jacob):
    python3 scripts/maak-pand-analyse.py /pad/naar/erkend-beslisschemas/index.html
"""
import base64, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRON = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / '_bron' / 'erkend-index.html'
DOEL = ROOT / 'pand-analyse.html'
s = BRON.read_text(encoding='utf-8')


def vervang(oud, nieuw, aantal=1):
    global s
    n = s.count(oud)
    if n != aantal:
        raise SystemExit(f'Verwacht {aantal}x, gevonden {n}x:\n{oud[:140]}')
    s = s.replace(oud, nieuw)


def vervang_re(patroon, nieuw, aantal=1, flags=0):
    global s
    s, n = re.subn(patroon, nieuw, s, flags=flags)
    if n != aantal:
        raise SystemExit(f'Regex verwacht {aantal}x, gevonden {n}x: {patroon[:100]}')


# ---------- logo (uit de Huismaten-tool) ----------
hm = (ROOT / 'huismaten-stap1.html').read_text(encoding='utf-8')
LOGO_B64 = re.search(r"LOGO_VISSER_B64\s*=\s*['\"]([A-Za-z0-9+/=]+)['\"]", hm).group(1)
LOGO_URI = 'data:image/png;base64,' + LOGO_B64          # 708 x 177 px

# ---------- kop van de pagina ----------
vervang('<link rel="manifest" href="manifest.webmanifest">\n', '')
vervang('<meta name="theme-color" content="#0B3D2E">', '<meta name="theme-color" content="#432D6A">')
vervang('<meta name="apple-mobile-web-app-title" content="EE Beslisschema">', '<meta name="apple-mobile-web-app-title" content="Pand analyse">')
vervang('<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">', '<link rel="apple-touch-icon" href="icons/icon-180.png">')
vervang('<title>Pand analyse/Beslisschema erkend-energielabel.nl</title>', '<title>Pand analyse · Visser Inspecties</title>')
vervang_re(r'<link rel="icon" href="data:image/png;base64,[A-Za-z0-9+/=]+">', '<link rel="icon" href="icons/icon-192.png">')
vervang('<script src="https://cdn.jsdelivr.net/npm/@azure/msal-browser@2.38.3/lib/msal-browser.min.js"></script>\n',
        '<script src="assets/login.js"></script>\n<script src="assets/home-knop.js" defer></script>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&display=swap">\n')

# ---------- kleuren: groen (Erkend-Energielabel) -> paars (Visser Inspecties) ----------
KLEUREN = {
    '#0B3D2E': '#432D6A', '0x0B3D2E': '0x432D6A', '#3CB54A': '#7A5BA6', '#7AB648': '#7A5BA6',
    '#e7f3e8': '#EFEAF5', '#eef7ef': '#F4F2F6', '#dff2e2': '#E8E1F1', '#f1f5f2': '#F4F2F6',
    '#f4f8f5': '#F6F4F8', '#f7fbf8': '#F8F7FA', '#ecf8ef': '#F1EDF6', '#e3ebe5': '#E6E2EC',
    '#dfe7e2': '#E2DEE8', '#d6e2d8': '#DCD7E3', '#cfdcd2': '#D6D0DE', '#e3e8e5': '#E5E2EA',
    '#f5f8f5': '#F5F4F7', '#8fd69b': '#C3A4EA', '#1c2e22': '#2C2339', '#33433a': '#3A3345',
    '#121815': '#14121A', '#1b231e': '#1D1A24', '#0b1a12': '#1A1026', '#E7F3E8': '#EFEAF5',
    '#2f9e3e': '#372968',
}
for oud, nieuw in KLEUREN.items():
    s = s.replace(oud, nieuw)
# koppen in Merriweather (zoals de andere tools)
vervang("h1{font-size:1.35rem;margin:.2rem 0 .1rem;color:var(--paars)}",
        "h1{font-family:Merriweather,Georgia,serif;font-size:1.35rem;margin:.2rem 0 .1rem;color:var(--paars)}")
vervang(".kop h1{color:#fff;margin:0;font-size:1.25rem}", ".kop h1{color:#fff;margin:0;font-size:1.25rem;font-family:Merriweather,Georgia,serif}")

# ---------- logo's ----------
vervang_re(r'(<div class="logobalk"><img src=")data:image/jpeg;base64,[A-Za-z0-9+/=]+(")', r'\g<1>' + LOGO_URI + r'\2')
vervang_re(r"const LOGO_WOORD = 'data:image/jpeg;base64,[A-Za-z0-9+/=]+';", "const LOGO_WOORD = '" + LOGO_URI + "';")
vervang("doc.addImage(LOGO_WOORD, 'JPEG', PM, 12, 70, 70*163/700);", "doc.addImage(LOGO_WOORD, 'PNG', PM, 12, 62, 62*177/708);")

# ---------- projectgegevens: postcode + huisnummer ----------
oud_kaart = re.search(r'  <div class="kaart">\n    <div class="rij">\n      <div><label for="projnr">.*?</div>\n  </div>\n', s, re.S).group(0)
vervang(oud_kaart, '''  <div class="kaart" id="adreskaart">
    <div class="pc-rij">
      <div><label for="pc-pc">Postcode</label><input type="text" id="pc-pc" placeholder="3311GP" autocomplete="off" autocapitalize="characters" maxlength="7"></div>
      <div><label for="pc-nr">Huisnummer</label><input type="text" id="pc-nr" placeholder="293" inputmode="numeric" autocomplete="off" maxlength="6"></div>
      <div><label for="pc-toev">Toevoeging</label><select id="pc-toev"><option value="">–</option></select></div>
    </div>
    <div id="pc-adres" class="pc-adres klein">Vul postcode en huisnummer in, of kies hierboven je project.</div>
    <input type="hidden" id="projnr"><input type="hidden" id="project">
    <div class="rij" style="margin-top:10px">
      <div><label for="adviseur">EP-adviseur</label><input type="text" id="adviseur" placeholder="naam adviseur"></div>
    </div>
  </div>
''')
vervang('.rij3{display:grid;', '''.pc-rij{display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:10px}
.pc-rij select{width:100%;padding:10px;border:1px solid var(--lijn);border-radius:8px;font:inherit;background:var(--kaart);color:var(--tekst)}
.pc-adres{margin:10px 0 0;padding:8px 10px;border-radius:8px;background:var(--paars-licht)}
.pc-adres b{color:var(--paars)}
.pc-adres.fout{background:var(--rood-licht);color:var(--rood)}
@media(max-width:560px){.hoofdtabs{flex-wrap:wrap}.hoofdtabs .topgroep{flex:1 1 100%}.hoofdtabs .topgroep .topknop:not(.topinst){flex:1}}
.rij3{display:grid;''')

# ---------- teksten en voettekst ----------
oud_footer = re.search(r'  <footer><b>Erkend-Energielabel\.nl</b>.*?</footer>', s, re.S).group(0)
vervang(oud_footer, '''  <footer><b>Visser Inspecties</b> · John Visser · EnergiePrestatie-advies · www.visserinspecties.nl · info@visserinspecties.nl<br>Bron: ISSO-publicatie 82.1 Energieprestatie woningen en woongebouwen, 7e druk. Deze tool is een hulpmiddel en vervangt de publicatie niet; bij twijfel gelden de tekst van de ISSO en BRL 9500-W.<br>Pand analyse, opmeten en labels buurt: gebaseerd op de tool van Erkend-Energielabel.nl.</footer>''')
vervang("ERKEND-ENERGIELABEL.NL\\nBESLISSCHEMA'S ISSO 82.1 (7e druk)\\nProjectnummer: ${$('projnr').value.trim()||'-'}",
        "VISSER INSPECTIES\\nBESLISSCHEMA'S ISSO 82.1 (7e druk)\\nPostcode + nr: ${$('projnr').value.trim()||'-'}")
vervang("'Erkend-Energielabel.nl · Beslisschema’s ISSO 82.1 (7e druk)'", "'Visser Inspecties · Beslisschema’s ISSO 82.1 (7e druk)'")
vervang("doc.text('Erkend-Energielabel.nl · Aelbert Cuyplaan 45, 3343 DA Hendrik-Ido-Ambacht · T 06 51 63 08 96 · Info@Erkend-Energielabel.nl · KvK 42070461', PM, 297-11.5, {maxWidth: PBR-24});",
        "doc.text('Visser Inspecties · John Visser · EnergiePrestatie-advies · T 06 5160 47 35 · info@visserinspecties.nl · www.visserinspecties.nl · KvK 83376704', PM, 297-11.5, {maxWidth: PBR-24});")
vervang("author: $('adviseur').value||'Erkend-Energielabel.nl', creator:'Erkend-Energielabel.nl'",
        "author: $('adviseur').value||'John Visser', creator:'Visser Inspecties – Pand analyse'")
s = s.replace("['PROJECTNUMMER',$('projnr').value||'-']", "['POSTCODE + NR',$('projnr').value||'-']")
# bestandsnaam zoals de projectmappen: "3311GP Dordrecht, Spuiboulevard 293"
vervang("  const p = [$('projnr').value.trim(), $('project').value.trim()].filter(Boolean).join(' ').replace(/[\\\\/:*?\"<>|]/g,'').slice(0,80);",
        "  const p = (window.adresMapnaam ? adresMapnaam() : $('project').value.trim()).replace(/[\\\\/:*?\"<>|]/g,'').slice(0,80);")
vervang("window.bsProject = () => [$('projnr').value.trim(), $('project').value.trim()].filter(Boolean).join(' · ');",
        "window.bsProject = () => $('project').value.trim();")

# ---------- label-server: eigen worker ----------
vervang("const LABEL_API_STD='https://ep-label.long-rain-6721.workers.dev/';", "const LABEL_API_STD='https://ep-labels.falling-brook-4828.workers.dev/';   // eigen Cloudflare Worker (label-proxy/worker.js); per apparaat te wijzigen via ⚙")
s = s.replace("https://ep-label.jouwnaam.workers.dev", "https://ep-label.visserinspecties.workers.dev")

# ---------- OneDrive: gedeelde Visser-inlog i.p.v. eigen app-registratie ----------
start = s.index('/* ============ ONEDRIVE (eigen app-registratie) ============ */')
eind = s.index("function toonMelding(soort, tekst){")
s = s[:start] + r'''/* ============ ONEDRIVE (gedeelde inlog van de Visser-tools) ============ */
const GRAPH = 'https://graph.microsoft.com/v1.0';
const OD_CLIENT = 'fdf237c9-bf46-47fa-ab3d-a8834a73e284', OD_TENANT = '984fd1fb-3d68-4c94-aff2-47f699fb5dae';
const OD_SCOPE = 'https://graph.microsoft.com/Files.ReadWrite offline_access';
const cfg = {root:'0_In Behandeling', sub:'020 AANTEKENINGEN'};
let odProject = null;   // {naam, pad} — pad = projectmap (zonder 020 AANTEKENINGEN)
let ingelogd = false;

function leesCfg(){
  try{ odProject = JSON.parse(localStorage.getItem('pa_project')||'null'); }catch(e){}
  if(!odProject){   // zelfde project als in Huismaten / beslisschema's
    for(const k of ['huismaten_project','bs_gekozen_project']){
      try{ const p=JSON.parse(localStorage.getItem(k)||'null'); if(p && p.pad && p.naam && p.naam!==cfg.sub){ odProject={naam:p.naam, pad:p.pad.replace(/\/020 AANTEKENINGEN$/,'')}; break; } }catch(e){}
    }
  }
}
function toonCfg(){}

function zetBalk(soort, tekst, knoppen){
  const el = $('od-status'); el.className = 'odbalk ' + (soort||''); el.textContent = tekst;
  (knoppen||[]).forEach(([label, actie]) => { const b=document.createElement('button'); b.type='button'; b.textContent=label; b.onclick=actie; el.appendChild(b); });
}
const naarInlog = () => { if(window.VILogin) VILogin.naarInlog(); };
function balk(){
  if(location.protocol==='file:'){ zetBalk('let','☁️ OneDrive werkt alleen als de pagina online staat (https), niet als los bestand.'); return; }
  if(!ingelogd){ zetBalk('let','☁️ Niet ingelogd bij OneDrive.',[['Inloggen',naarInlog]]); return; }
  if(!odProject){ zetBalk('let','☁️ OneDrive verbonden — kies een project.',[['Kies project',kiesProject]]); return; }
  zetBalk('ok',`✅ OneDrive verbonden · project: ${odProject.naam}`,[['Wijzig project',kiesProject]]);
}
async function token(){
  let rt=null; try{ rt=localStorage.getItem('rt'); }catch(e){}
  if(!rt){ ingelogd=false; balk(); throw new Error('Niet ingelogd bij OneDrive.'); }
  let r;
  try{ r = await fetch(`https://login.microsoftonline.com/${OD_TENANT}/oauth2/v2.0/token`, {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({client_id:OD_CLIENT, grant_type:'refresh_token', refresh_token:rt, scope:OD_SCOPE})}); }
  catch(e){ throw new Error('Geen verbinding met Microsoft.'); }
  const d = await r.json().catch(()=>({}));
  if(!d.access_token){ if(d.error==='invalid_grant'||d.error==='interaction_required'){ try{ localStorage.removeItem('rt'); }catch(e){} ingelogd=false; balk(); } throw new Error('Inlog verlopen — log opnieuw in.'); }
  if(d.refresh_token){ try{ localStorage.setItem('rt', d.refresh_token); }catch(e){} }
  ingelogd = true; return d.access_token;
}
async function graph(pad, opt={}){
  const t = await token();
  const r = await fetch(GRAPH+pad, {...opt, headers:{...(opt.headers||{}), Authorization:'Bearer '+t}});
  if(!r.ok){ let m=r.status+' '+r.statusText; try{ m=(await r.json()).error.message||m; }catch(_){}; const e=new Error(m); e.status=r.status; throw e; }
  return r;
}
const padUrl = p => '/me/drive/root' + (p ? ':/' + p.split('/').map(encodeURIComponent).join('/') + ':' : '');
async function initMsal(){
  if(location.protocol==='file:'){ balk(); return; }
  let rt=null; try{ rt=localStorage.getItem('rt'); }catch(e){}
  if(!rt){ ingelogd=false; balk(); return; }
  zetBalk('','☁️ OneDrive: controleren…');
  try{ await token(); }catch(e){ if(ingelogd===false && !(localStorage.getItem('rt'))) { balk(); return; } zetBalk('let','⚠️ '+(e.message||e),[['Controleer',initMsal]]); return; }
  if(odProject){
    try{ await graph(padUrl(odProject.pad)+'?$select=id'); }
    catch(e){ if(e.status===404){ zetBalk('fout','❌ Projectmap niet gevonden: '+odProject.pad,[['Kies project',kiesProject]]); return; } }
  }
  balk();
}

function kiesMap(){
  return new Promise(resolve => {
    const overlay=$('od-overlay'), lijst=$('od-lijst'), padEl=$('od-pad'), ok=$('od-ok'), terug=$('od-terug'), ann=$('od-annuleer');
    const stapel = [];
    const huidigPad = () => stapel.map(x=>x.naam).join('/');
    async function toon(){
      padEl.textContent = 'OneDrive' + (stapel.length ? ' / '+stapel.map(x=>x.naam).join(' / ') : '');
      terug.disabled = !stapel.length; ok.disabled = true; lijst.innerHTML = '<div class="od-leeg">Mappen laden…</div>';
      try{
        const top = stapel.length ? stapel[stapel.length-1].id : null;
        const r = await graph(top ? `/me/drive/items/${top}/children?$top=500&$select=id,name,folder` : '/me/drive/root/children?$top=500&$select=id,name,folder');
        const mappen = ((await r.json()).value||[]).filter(i=>i.folder).sort((a,b)=>a.name.localeCompare(b.name,'nl',{numeric:true}));
        ok.disabled = !stapel.length; lijst.innerHTML = '';
        mappen.forEach(m => { const d=document.createElement('div'); d.className='od-item'; d.textContent='📁 '+m.name; d.onclick=()=>{ stapel.push({id:m.id,naam:m.name}); toon(); }; lijst.appendChild(d); });
        if(!mappen.length) lijst.innerHTML = '<div class="od-leeg">Geen submappen hier.</div>';
      }catch(err){ lijst.innerHTML = '<div class="od-leeg">⚠️ '+esc(err.message||err)+'</div>'; }
    }
    function sluit(r){ overlay.classList.remove('actief'); ok.onclick=terug.onclick=ann.onclick=null; resolve(r); }
    terug.onclick = () => { stapel.pop(); toon(); };
    ann.onclick = () => sluit(null);
    ok.onclick = () => { const t=stapel[stapel.length-1]; sluit({id:t.id, naam:t.naam, pad:huidigPad()}); };
    overlay.classList.add('actief');
    (async () => {
      try{ const j = await (await graph(padUrl(cfg.root)+'?$select=id')).json(); stapel.push({id:j.id, naam:cfg.root}); }catch(_){}
      toon();
    })();
  });
}

async function kiesProject(){
  let keuze;
  try{ await token(); keuze = await kiesMap(); }catch(e){ zetBalk('fout','❌ '+(e.message||e),[['Inloggen',naarInlog],['Opnieuw',kiesProject]]); return; }
  if(!keuze) return;
  let delen = keuze.pad.split('/');
  if(delen[delen.length-1]===cfg.sub && delen.length>1) delen = delen.slice(0,-1);   // 020 AANTEKENINGEN gekozen: de projectmap erboven
  bewaarLokaal();
  odProject = {naam:delen[delen.length-1], pad:delen.join('/')};
  try{ localStorage.setItem('pa_project', JSON.stringify(odProject)); }catch(e){}
  await adresUitProject();
  leesLokaal(); renderLog(); balk(); window.vbsRender && vbsRender(); MEET.laadProject(logSleutel());
}
// postcode + huisnummer uit de projectmap halen: projectgegevens.json, anders de mapnaam "3311GP Dordrecht, Spuiboulevard 293"
async function adresUitProject(){
  if(!odProject) return;
  let tekst = odProject.naam;
  try{ const r = await graph(padUrl(odProject.pad+'/'+cfg.sub+'/projectgegevens.json').replace(/:$/,'')+':/content'); const pg = JSON.parse(await r.text()); if(pg && pg.adres) tekst = pg.adres + ' ' + odProject.naam; }catch(_){}
  const pc = (tekst.match(/\b(\d{4})\s?([A-Za-z]{2})\b/)||[]);
  const nr = (odProject.naam.match(/,\s*[^,]*?\s(\d+)\s*([A-Za-z]?)(?:[\s-]+(\w{1,4}))?\s*$/)||[]);
  if(pc[1] && nr[1] && window.PC){ PC.zet(pc[1]+pc[2].toUpperCase(), nr[1], (nr[2]||'')+(nr[3]||'')); }
}

async function doelMapId(){
  const pad = odProject.pad + '/' + cfg.sub;
  try{ return (await (await graph(padUrl(pad)+'?$select=id')).json()).id; }
  catch(e){
    if(e.status!==404) throw e;
    const ouder = (await (await graph(padUrl(odProject.pad)+'?$select=id')).json()).id;   // projectmap moet bestaan; alleen de submap aanmaken
    const r = await graph(`/me/drive/items/${ouder}/children`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:cfg.sub, folder:{}, '@microsoft.graph.conflictBehavior':'replace'})});
    return (await r.json()).id;
  }
}
async function upload(mapId, naam, inhoud, type){
  const r = await graph(`/me/drive/items/${mapId}:/${encodeURIComponent(naam)}:/content?@microsoft.graph.conflictBehavior=rename`,
    {method:'PUT', headers:{'Content-Type':type}, body: inhoud instanceof Blob ? inhoud : new Blob([inhoud],{type})});
  return (await r.json()).name;
}
async function opslaanInOneDrive(){
  await meetVoorPdf();
  if(!log.length && !pandMee() && !window.__meetPdf){ toonMelding('fout','Er is nog niets vastgelegd.'); return; }
  try{
    if(!odProject){ await kiesProject(); if(!odProject) return; }
    toonMelding('ok','Bezig met opslaan…');
    const map = await doelMapId();
    const basis = bestandsnaam().replace(/\.txt$/,'');
    const n1 = await upload(map, basis+'.txt', maakTxt(), 'text/plain;charset=utf-8');
    const pd = await pandVoorPdf();
    const pdf = maakPdf(pd);
    const n2 = pdf ? await upload(map, pdfNaam(pd), pdf.output('blob'), 'application/pdf')
                   : await upload(map, basis+'.html', rapportHtml(false), 'text/html;charset=utf-8');
    toonMelding('ok', `✅ Opgeslagen in ${odProject.naam} / ${cfg.sub}: “${n1}” en “${n2}”.`);
  }catch(e){
    if(e.status===404){ zetBalk('fout','❌ Projectmap niet gevonden: '+odProject.pad,[['Kies project',kiesProject]]); }
    toonMelding('fout','Niet opgeslagen in OneDrive: '+(e.message||e)+' — de lijst staat nog hier; download het bestand als vangnet.');
  }
}
''' + s[eind:]
# instellingenpaneel (eigen app-registratie) weg
oud_instel = re.search(r'  <details class="instel" id="instel">.*?</details>\n', s, re.S).group(0)
vervang(oud_instel, '')
vervang('<button id="od-ok" class="primair">Deze map gebruiken</button>', '<button id="od-ok" class="primair">Dit project gebruiken</button>')
vervang('<h2>Kies de projectmap</h2>', '<h2>Kies het project</h2>')

# ---------- postcode + huisnummer: adres opzoeken via PDOK ----------
vervang("leesCfg(); toonCfg();\n", r'''leesCfg(); toonCfg();
/* Postcode + huisnummer -> adres (PDOK Locatieserver). Vult het verborgen adresveld dat de rest van de tool gebruikt. */
window.PC = (function(){
  const pcEl=$('pc-pc'), nrEl=$('pc-nr'), tvEl=$('pc-toev'), uit=$('pc-adres');
  let gevonden=[], timer=null, laatste='';
  const normPc = v => String(v||'').toUpperCase().replace(/\s+/g,'');
  const geldig = () => /^\d{4}[A-Z]{2}$/.test(normPc(pcEl.value)) && /^\d+$/.test(nrEl.value.trim());
  const toev = d => (d.huisletter||'') + (d.huisnummertoevoeging ? (d.huisletter?'-':'')+d.huisnummertoevoeging : '');
  function bewaar(){ try{ localStorage.setItem('pa_adres', JSON.stringify({pc:normPc(pcEl.value), nr:nrEl.value.trim(), tv:tvEl.value})); }catch(e){} }
  function kies(){
    const d = gevonden.find(x => toev(x)===tvEl.value) || gevonden[0]; if(!d) return;
    const nummer = d.huisnummer + (toev(d) ? (d.huisletter && !d.huisnummertoevoeging ? '' : ' ') + toev(d) : '');
    const adres = `${d.straatnaam} ${nummer}, ${d.postcode} ${d.woonplaatsnaam}`;
    const oud = $('project').value;
    $('project').value = adres; $('projnr').value = `${d.postcode} ${nummer}`;
    window.__pcAdres = d;
    uit.className = 'pc-adres klein'; uit.innerHTML = '📍 <b>'+esc(adres)+'</b>';
    try{ localStorage.setItem('ee_bs_project', adres); localStorage.setItem('ee_bs_projnr', $('projnr').value); }catch(e){}
    bewaar();
    if(oud !== adres){
      $('project').dispatchEvent(new Event('change')); $('project').dispatchEvent(new Event('input'));
      const q = $('bag-q'); if(q){ q.value = d.postcode + ' ' + nummer; }
      if(window.BAG && !$('tab-bag').hidden) try{ BAG.zoek(d.postcode + ' ' + nummer); }catch(e){}
    }
  }
  async function zoek(voorkeurToev){
    if(!geldig()){ return; }
    const pc = normPc(pcEl.value), nr = nrEl.value.trim(), sleutel = pc+'|'+nr;
    if(sleutel===laatste && gevonden.length){ kies(); return; }
    laatste = sleutel; uit.className='pc-adres klein'; uit.textContent='Adres zoeken…';
    try{
      const url = 'https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?q=' + encodeURIComponent(`postcode:${pc} and huisnummer:${nr}`) +
        '&fq=type:adres&rows=50&fl=weergavenaam,straatnaam,huisnummer,huisletter,huisnummertoevoeging,postcode,woonplaatsnaam';
      const j = await (await fetch(url)).json();
      gevonden = ((j.response||{}).docs||[]).filter(d => String(d.huisnummer)===nr && normPc(d.postcode)===pc)
        .sort((a,b) => toev(a).localeCompare(toev(b),'nl',{numeric:true}));
    }catch(e){ gevonden=[]; uit.className='pc-adres klein fout'; uit.textContent='Adres opzoeken lukt niet (geen internet?).'; return; }
    if(!gevonden.length){ uit.className='pc-adres klein fout'; uit.textContent='Geen adres gevonden voor '+pc+' '+nr+'.'; tvEl.innerHTML='<option value="">–</option>'; return; }
    tvEl.innerHTML = gevonden.map(d => `<option value="${esc(toev(d))}">${toev(d) ? esc(toev(d)) : '(geen)'}</option>`).join('');
    tvEl.disabled = gevonden.length < 2;
    const vk = String(voorkeurToev||'').toUpperCase().replace(/[\s-]/g,'');
    const match = gevonden.find(d => toev(d).toUpperCase().replace(/[\s-]/g,'')===vk);
    tvEl.value = match ? toev(match) : toev(gevonden[0]);
    kies();
  }
  const later = () => { clearTimeout(timer); timer = setTimeout(() => zoek(), 450); };
  pcEl.addEventListener('input', () => { const p=normPc(pcEl.value); if(pcEl.value!==p && /^\d{4}[A-Z]{0,2}$/.test(p)) pcEl.value=p; later(); });
  nrEl.addEventListener('input', () => { nrEl.value = nrEl.value.replace(/\D/g,''); later(); });
  tvEl.addEventListener('change', kies);
  try{ const a = JSON.parse(localStorage.getItem('pa_adres')||'null'); if(a){ pcEl.value=a.pc||''; nrEl.value=a.nr||''; if(a.pc && a.nr) zoek(a.tv); } }catch(e){}
  return { zet(pc, nr, tv){ pcEl.value=pc; nrEl.value=nr; laatste=''; zoek(tv); } };
})();
// mapnaam-stijl voor bestandsnamen: "3311GP Dordrecht, Spuiboulevard 293"
window.adresMapnaam = () => { const d = window.__pcAdres; if(!d) return $('project').value.trim();
  const t = (d.huisletter||'') + (d.huisnummertoevoeging ? (d.huisletter?'-':' ')+d.huisnummertoevoeging : '');
  return `${d.postcode} ${d.woonplaatsnaam}, ${d.straatnaam} ${d.huisnummer}${t}`; };
if(!$('adviseur').value) $('adviseur').value = 'John Visser';
''')
# adres uit projectgegevens.json bij het openen (als er een project is maar nog geen adres)
vervang("initMsal();\n/* ============ TABBLADEN", "initMsal().then(() => { if(odProject && ingelogd && !$('pc-pc').value) adresUitProject(); });\n/* ============ TABBLADEN")

# ================================================================
#  VG / AG / LG / RG (zoals Pand-oriëntatie) + buren wegklikken
# ================================================================
vervang('.bag-tools button.on{background:#432D6A;color:#fff}', '''.bag-tools button.on{background:#432D6A;color:#fff}
.bag-code{background:#432D6A;color:#fff;border-radius:6px;padding:1px 6px;font-weight:800;font-size:11px;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.35);cursor:pointer}
.bag-code.vg{background:#E08A00;font-size:12px;padding:2px 7px}
.bag-codepill{display:inline-block;min-width:30px;text-align:center;border-radius:6px;padding:1px 6px;font-weight:800;font-size:.75rem;background:#EFEAF5;color:#432D6A}
.bag-codepill.vg{background:#E08A00;color:#fff}
.bag-vgblok{background:#F4F2F6;border-left:4px solid #E08A00;border-radius:8px;padding:8px 10px;margin:0 0 10px;font-size:.85rem}
.bag-vgblok table{width:100%;margin-top:6px}
.bag-vgknop{margin-top:8px}''')
vervang('<button type="button" id="bag-t3d" class="on">3D</button>',
        '<button type="button" id="bag-buren" class="on" title="Belendende panden tonen of verbergen">Buren</button><button type="button" id="bag-t3d" class="on">3D</button>')
vervang('<button type="button" id="bag-reset">Reset</button>',
        '<button type="button" id="bag-buren3" class="on" title="Belendende panden tonen of verbergen">Buren</button><button type="button" id="bag-reset">Reset</button>')
vervang('<th>Or.</th><th>Rol</th></tr></thead>', '<th>Or.</th><th>Gevel</th><th>Rol</th></tr></thead>')
vervang('<tbody id="bag-tb"><tr><td colspan="5" class="klein">—</td></tr></tbody>', '<tbody id="bag-tb"><tr><td colspan="6" class="klein">—</td></tr></tbody>')

# toestand
vervang("const S={center:null,addr:null,addrPt:null,blds:[],sel:null,edges:[],area:0,roles:{},auto:{},eSel:-1,autoSel:true,hlDir:null,exag:1,tab:'orient'};",
        "const S={center:null,addr:null,addrPt:null,blds:[],sel:null,edges:[],area:0,roles:{},auto:{},eSel:-1,autoSel:true,hlDir:null,exag:1,tab:'orient',vgInfo:'',vgTok:0,burenUit:(()=>{try{return localStorage.getItem('pa_buren_uit')==='1'}catch(e){return false}})()};")

# functies: codes per gevel en automatische voorgevel (gevel die naar de straat van het adres kijkt)
vervang("const role=i=>S.roles[i]||'Gevel';", r"""const role=i=>S.roles[i]||'Gevel';
/* ---- VG/AG/LG/RG: staande voor de voorgevel, kijkend naar het huis: links = LG, rechts = RG ---- */
const angD=(a,b)=>{const d=Math.abs(((a-b)%360+360)%360);return d>180?360-d:d};
function vgIndex(){for(const k in S.roles)if(S.roles[k]==='Voorgevel'&&S.edges[+k])return +k;return -1}
function codes(){const vi=vgIndex();if(vi<0)return null;const av=S.edges[vi].az,doel={VG:av,LG:(av+90)%360,AG:(av+180)%360,RG:(av+270)%360};
  return S.edges.map((e,i)=>{if(role(i)==='Belendend')return null;if(i===vi)return'VG';let best=null,bd=1e9;for(const k in doel){const d=angD(e.az,doel[k]);if(d<bd){bd=d;best=k}}return best})}
function codeVan(i){const c=codes();return c?c[i]:null}
function zetVoorgevel(i,bron){for(const k in S.roles)if(S.roles[k]==='Voorgevel'||(S.roles[k]==='Achtergevel'&&S.vgAuto))delete S.roles[k];
  S.roles[i]='Voorgevel';delete S.auto[i];autoFill(i);S.vgAuto=bron==='auto';if(bron!=='auto')S.vgInfo='Voorgevel zelf aangewezen: gevel '+(i+1)+'.';
  S.eSel=i;S.autoSel=false;renderMap(false);renderGevels();changed()}
const opSeg=(p,a,b)=>{const dx=b[0]-a[0],dy=b[1]-a[1],l2=dx*dx+dy*dy,t=l2?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l2)):0;return[a[0]+t*dx,a[1]+t*dy]};
function dichtbij(p,lijnen){let best=null,bd=1e18;for(const l of lijnen)for(let i=0;i<l.length-1;i++){const q=opSeg(p,l[i],l[i+1]),d=Math.hypot(q[0]-p[0],q[1]-p[1]);if(d<bd){bd=d;best=q}}return best?{punt:best,afstand:bd}:null}
async function autoVoorgevel(){
  const b=selB();if(!b||!S.edges.length)return;const tok=++S.vgTok;S.vgInfo='';
  if(vgIndex()>=0)return;
  const v=vboOf(b);if(!v||!v.postcode||!v.huisnummer){S.vgInfo='Voorgevel niet automatisch bepaald (geen adres bij dit pand): wijs hem zelf aan.';renderGevels();return}
  try{
    const q=`postcode:${String(v.postcode).replace(/\s/g,'')} and huisnummer:${v.huisnummer}`;
    const ad=((((await (await fetch(LS+'/free?q='+encodeURIComponent(q)+'&fq=type:adres&rows=1&fl=openbareruimte_id,centroide_rd,straatnaam')).json()).response)||{}).docs||[])[0];
    if(tok!==S.vgTok)return;
    const pm=/POINT\(([-\d.]+) ([-\d.]+)\)/.exec((ad&&ad.centroide_rd)||'');
    if(!ad||!ad.openbareruimte_id||!pm){S.vgInfo='Voorgevel niet automatisch bepaald (geen straatgegevens): wijs hem zelf aan.';renderGevels();return}
    const weg=((((await (await fetch(LS+'/free?fq=type:weg&fq=openbareruimte_id:'+encodeURIComponent(ad.openbareruimte_id)+'&rows=1&fl=geometrie_rd')).json()).response)||{}).docs||[])[0];
    if(tok!==S.vgTok)return;
    if(!weg||!weg.geometrie_rd){S.vgInfo='Voorgevel niet automatisch bepaald (straat niet gevonden): wijs hem zelf aan.';renderGevels();return}
    const lijnen=[];for(const g of weg.geometrie_rd.match(/\(([^()]+)\)/g)||[]){const pts=g.replace(/[()]/g,'').split(',').map(t=>t.trim().split(/\s+/).map(Number));if(pts.length>=2)lijnen.push(pts)}
    const adr=S.addrPt||[+pm[1],+pm[2]],d0=dichtbij(adr,lijnen);
    if(!d0){S.vgInfo='Voorgevel niet automatisch bepaald: wijs hem zelf aan.';renderGevels();return}
    const richting=((Math.atan2(d0.punt[0]-adr[0],d0.punt[1]-adr[1])*180/Math.PI)+360)%360;
    let beste=-1,score=1e18,ruim=false;
    for(const grens of[50,181]){S.edges.forEach((e,i)=>{if(e.len<2||role(i)==='Belendend')return;const vs=angD(e.az,richting);if(vs>grens)return;
        const sc=dichtbij(e.mid,lijnen).afstand+vs*0.05-Math.min(e.len,10)*0.2;if(sc<score){score=sc;beste=i}});
      if(beste>=0){ruim=grens>50;break}}
    if(beste<0||vgIndex()>=0||tok!==S.vgTok){if(beste<0){S.vgInfo='Voorgevel niet automatisch bepaald: wijs hem zelf aan.';renderGevels()}return}
    S.vgInfo='Voorgevel automatisch gekozen: gevel '+(beste+1)+' kijkt naar '+(ad.straatnaam||'de straat')+(ruim?' (bij benadering)':'')+'. Klopt het niet? Kies een andere gevel en tik op “Maak voorgevel”.';
    zetVoorgevel(beste,'auto');
  }catch(e){if(tok===S.vgTok){S.vgInfo='Voorgevel kon niet automatisch bepaald worden (geen verbinding): wijs hem zelf aan.';renderGevels()}}
}""")
# na het (her)berekenen van de gevels de voorgevel zoeken
vervang("  S.sel=id;S.roles={};S.eSel=-1;compute();\n", "  S.sel=id;S.roles={};S.eSel=-1;compute();setTimeout(autoVoorgevel,0);\n")
vervang("$('bag-tol').onchange=()=>{S.roles={};compute();renderAll(false);changed()};", "$('bag-tol').onchange=()=>{S.roles={};compute();renderAll(false);changed();autoVoorgevel()};")

# kaart: buren verbergen + VG/AG/LG/RG-labels op de gevels
vervang("  S.blds.forEach(b=>{const ll=b.ring.map(c=>rd2wgs(c[0],c[1]));const h=relH(b);const sel=b.id===S.sel;\n    L.polygon(",
        "  S.blds.forEach(b=>{const ll=b.ring.map(c=>rd2wgs(c[0],c[1]));const h=relH(b);const sel=b.id===S.sel;if(S.burenUit&&!sel)return;\n    L.polygon(")
vervang("    // pijl op de geselecteerde gevel, loodrecht naar buiten\n",
        "    // VG/AG/LG/RG binnen het pand: één label per gevel, bij het langste geveldeel (VG bij de echte voorgevel)\n    {const cs=codes(),vi=vgIndex(),lang={};if(cs){visible().forEach(({e,i})=>{const c=cs[i];if(!c)return;if(lang[c]===undefined||e.len>S.edges[lang[c]].len)lang[c]=i});if(vi>=0)lang.VG=vi;\n      Object.entries(lang).forEach(([c,i])=>{const e=S.edges[i],t=e.len>5?0.62:0.5,p=[e.a[0]+(e.c[0]-e.a[0])*t-e.n[0]*2.2,e.a[1]+(e.c[1]-e.a[1])*t-e.n[1]*2.2];\n      L.marker(rd2wgs(...p),{icon:L.divIcon({html:`<span class=\"bag-code${c==='VG'?' vg':''}\">${c}</span>`,className:'',iconSize:null,iconAnchor:[14,9]})}).addTo(grp).on('click',()=>selEdge(i))})}}\n    // pijl op de geselecteerde gevel, loodrecht naar buiten\n")
vervang("  map.on('click',e=>{const[x,y]=wgs2rd(e.latlng.lat,e.latlng.lng);const hit=S.blds.find(b=>inside([x,y],b.ring));\n    if(hit)selectBld(hit.id,false);else loadArea(x,y,null)});",
        "  map.on('click',e=>{const[x,y]=wgs2rd(e.latlng.lat,e.latlng.lng);const hit=S.blds.find(b=>inside([x,y],b.ring));\n    if(S.burenUit&&!(hit&&hit.id===S.sel))return;   // buren verborgen: niet per ongeluk een ander pand kiezen\n    if(hit)selectBld(hit.id,false);else loadArea(x,y,null)});")
# 3D: buren verbergen
vervang("  S.blds.forEach(b=>{const sel=b.id===S.sel;\n    if(b.geo&&gref!=null){", "  S.blds.forEach(b=>{const sel=b.id===S.sel;if(S.burenUit&&!sel)return;\n    if(b.geo&&gref!=null){")
# knoppen
vervang("  $('bag-reset').onclick=resetView;\n", r"""  $('bag-reset').onclick=resetView;
  const burenKnop=()=>{['bag-buren','bag-buren3'].forEach(id=>{const k=$(id);if(k){k.classList.toggle('on',!S.burenUit);k.textContent=S.burenUit?'Buren uit':'Buren'}})};
  ['bag-buren','bag-buren3'].forEach(id=>{const k=$(id);if(k)k.onclick=()=>{S.burenUit=!S.burenUit;try{localStorage.setItem('pa_buren_uit',S.burenUit?'1':'0')}catch(e){}burenKnop();renderMap(false);build3d(false)}});
  burenKnop();
""")

# tabel: kolom Gevel
vervang("<td><span class=\"bag-pill\" style=\"background:${role(i)==='Belendend'?'#aaa':DCOL[e.dir]}\">${e.dir}</span></td>\n    <td><select",
        "<td><span class=\"bag-pill\" style=\"background:${role(i)==='Belendend'?'#aaa':DCOL[e.dir]}\">${e.dir}</span></td>\n    <td>${(c=>c?`<span class=\"bag-codepill${c==='VG'?' vg':''}\">${c}</span>`:'<span class=\"klein\">–</span>')(codeVan(i))}</td>\n    <td><select")
vervang("if(!vis.length){tb.innerHTML='<tr><td colspan=\"5\" class=\"klein\">—</td></tr>';return}", "if(!vis.length){tb.innerHTML='<tr><td colspan=\"6\" class=\"klein\">—</td></tr>';return}")
vervang("    S.roles[i]=s.value;delete S.auto[i];autoFill(i);renderMap(false);renderGevels();changed()});",
        "    S.roles[i]=s.value;delete S.auto[i];if(s.value==='Voorgevel'){S.vgAuto=false;S.vgInfo='Voorgevel zelf aangewezen: gevel '+(i+1)+'.'}autoFill(i);renderMap(false);renderGevels();changed()});")

# geselecteerde gevel: code + knop "Maak voorgevel"
vervang("""<div class="klein">t.o.v. het ware noorden · gevel ${S.eSel+1}${rol!=='Gevel'?' · '+rol.toLowerCase():''} · lengte ${fmt(e.len)} m</div>""",
        """<div class="klein">t.o.v. het ware noorden · gevel ${S.eSel+1}${codeVan(S.eSel)?' · <b>'+codeVan(S.eSel)+'</b>':''}${rol!=='Gevel'?' · '+rol.toLowerCase():''} · lengte ${fmt(e.len)} m</div>""")
vervang("""<p class="klein" style="margin:6px 0 0">${S.autoSel?'Automatisch gekozen: meest zuidgerichte gevel.':'Zelf gekozen gevel.'} Loodrecht op de gevel, vanuit het pand naar buiten. Klik een andere gevel op de kaart om te wisselen.</p>""",
        """<p class="klein" style="margin:6px 0 0">${S.autoSel?'Automatisch gekozen: meest zuidgerichte gevel.':(rol==='Voorgevel'?'Voorgevel.':'Zelf gekozen gevel.')} Loodrecht op de gevel, vanuit het pand naar buiten. Klik een andere gevel op de kaart om te wisselen.</p>
    ${!bel&&rol!=='Voorgevel'?'<button type="button" class="actie licht bag-vgknop" id="bag-maakvg">⭐ Maak voorgevel (VG)</button>':''}""")
vervang("function renderGroepen(){\n", "function renderGroepen(){\n  {const k=$('bag-maakvg');if(k)k.onclick=()=>zetVoorgevel(S.eSel,'hand')}\n")
# blok bovenaan "Gevelrichtingen": VG/AG/LG/RG met richting en lengte
vervang("  if(!gr.length){el.innerHTML='<p class=\"klein\">—</p>';return}\n  const mx=Math.max(...gr.map(g=>g.len));\n  el.innerHTML=gr.map(",
        "  if(!gr.length){el.innerHTML='<p class=\"klein\">—</p>';return}\n  const mx=Math.max(...gr.map(g=>g.len));\n  el.innerHTML=vgBlok()+gr.map(")
vervang("function renderGroepen(){\n", r"""function vgBlok(){
  const cs=codes(),vi=vgIndex();
  if(!cs)return`<div class="bag-vgblok">${esc(S.vgInfo||'Voorgevel zoeken…')}<br><span class="klein">Kies een gevel op de kaart of in de tabel en tik op “Maak voorgevel”.</span></div>`;
  const tot={},az={};S.edges.forEach((e,i)=>{const c=cs[i];if(!c||e.len<(+$('bag-minl').value||0))return;tot[c]=(tot[c]||0)+e.len});
  const av=S.edges[vi].az,dz={VG:av,LG:(av+90)%360,AG:(av+180)%360,RG:(av+270)%360};
  return`<div class="bag-vgblok">${esc(S.vgInfo||('Voorgevel: gevel '+(vi+1)+'.'))}<table>${['VG','AG','LG','RG'].map(k=>`<tr><td><span class="bag-codepill${k==='VG'?' vg':''}">${k}</span></td><td>${dirOf(dz[k])} · ${Math.round(dz[k])}°</td><td style="text-align:right">${tot[k]?fmt(tot[k])+' m':'<span class="klein">–</span>'}</td></tr>`).join('')}</table><span class="klein">Staande voor de voorgevel, kijkend naar het huis: links = LG, rechts = RG. Gedeelde muren tellen niet mee.</span></div>`;
}
function renderGroepen(){
""")

# PDF en tekst: code bij de gevels
vervang("gevels:visible().map(({e,i})=>({nr:i+1,rol:role(i),", "gevels:visible().map(({e,i})=>({nr:i+1,code:codeVan(i)||'',rol:role(i),")
vervang("gekozen:(()=>{const e=S.edges[S.eSel];if(!e)return null;return{dir:e.dir,az:Math.round(e.az),len:fm(e.len),nr:S.eSel+1,rol:role(S.eSel),",
        "gekozen:(()=>{const e=S.edges[S.eSel];if(!e)return null;return{code:codeVan(S.eSel)||'',vgInfo:S.vgInfo,dir:e.dir,az:Math.round(e.az),len:fm(e.len),nr:S.eSel+1,rol:role(S.eSel),")
vervang("doc.text(pdfTekst(`Gevel ${g.nr}${g.rol!=='Gevel'?' ('+g.rol.toLowerCase()+')':''} · gevellengte ${g.len} · oriëntatie ${g.dir}`), tx, y+14.5);",
        "doc.text(pdfTekst(`Gevel ${g.nr}${g.code?' · '+g.code:''}${g.rol!=='Gevel'?' ('+g.rol.toLowerCase()+')':''} · gevellengte ${g.len} · oriëntatie ${g.dir}`), tx, y+14.5);")
vervang("const uitleg = (g.auto ? 'Automatisch gekozen: meest zuidgerichte gevel. ' : 'Door de adviseur gekozen gevel. ') + 'Richting loodrecht op de gevel, vanuit het pand naar buiten.';",
        "const uitleg = (g.auto ? 'Automatisch gekozen: meest zuidgerichte gevel. ' : g.rol==='Voorgevel' ? (g.vgInfo ? g.vgInfo.replace(/ Klopt het niet\\?.*$/,'')+' ' : 'Voorgevel. ') : 'Door de adviseur gekozen gevel. ') + 'Richting loodrecht op de gevel, vanuit het pand naar buiten.';")

# plattegrond in de PDF: buren volgen de knop, VG/AG/LG/RG bij de gevels
vervang("  S.blds.forEach(o=>{if(o.id===b.id)return;s+=`<polygon points=",
        "  S.blds.forEach(o=>{if(o.id===b.id||S.burenUit)return;s+=`<polygon points=")
vervang("""    s+=`<line x1="${A[0]}" y1="${A[1]}" x2="${Z[0]}" y2="${Z[1]}" stroke="${c}" stroke-width="${bel?4:6}" ${bel?'stroke-dasharray="7 6"':''}/>`});""",
        """    s+=`<line x1="${A[0]}" y1="${A[1]}" x2="${Z[0]}" y2="${Z[1]}" stroke="${c}" stroke-width="${bel?4:6}" ${bel?'stroke-dasharray="7 6"':''}/>`});
  {const cs=codes(),vi=vgIndex(),lang={};if(cs)visible().forEach(({e,i})=>{const c=cs[i];if(!c)return;if(lang[c]===undefined||e.len>S.edges[lang[c]].len)lang[c]=i});if(vi>=0)lang.VG=vi;
   Object.entries(lang).forEach(([c,i])=>{const e=S.edges[i],d=Math.max(1.8,16/sc),t=e.len>5?0.62:0.5;const q=P([e.a[0]+(e.c[0]-e.a[0])*t-e.n[0]*d,e.a[1]+(e.c[1]-e.a[1])*t-e.n[1]*d]);
    s+=`<rect x="${q[0]-14}" y="${q[1]-8}" width="28" height="16" rx="4" fill="${c==='VG'?'#E08A00':'#432D6A'}"/><text x="${q[0]}" y="${+q[1]+4}" text-anchor="middle" font-size="11" font-weight="700" fill="#fff">${c}</text>`})}""")

DOEL.write_text(s, encoding='utf-8')
print('Gemaakt:', DOEL.name, f'({len(s)//1024} kB)')
