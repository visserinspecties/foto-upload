/* Beslisschema's ISSO 82.1 — verslag als PDF in de stijl van de tool.
   Gebruikt pdf-lib + fontkit (map lib/) en de lettertypes uit fonts/.
   window.BeslisPdf.maak({project, datum, maker, entries}) → Uint8Array */
(function(){
'use strict';

function laadScript(src){ return new Promise((ok,fout)=>{ const s=document.createElement('script'); s.src=src; s.onload=ok; s.onerror=()=>fout(new Error('Kan '+src+' niet laden')); document.head.appendChild(s); }); }
let _as=null;
async function assets(){
  if(_as) return _as;
  if(!window.PDFLib) await laadScript('lib/pdf-lib.min.js').catch(()=>{});
  if(!window.PDFLib) await laadScript('https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js').catch(()=>{});
  if(!window.fontkit) await laadScript('lib/fontkit.umd.min.js').catch(()=>{});
  if(!window.fontkit) await laadScript('https://unpkg.com/@pdf-lib/fontkit@1.1.1/dist/fontkit.umd.min.js').catch(()=>{});
  if(!window.PDFLib || !window.fontkit) throw new Error('Het PDF-onderdeel kon niet worden geladen (ben je online?)');
  const get=async u=>{ const r=await fetch(u); if(!r.ok) throw new Error(u+' niet gevonden ('+r.status+')'); return new Uint8Array(await r.arrayBuffer()); };
  const lijst=['fonts/Merriweather-700-normal.ttf','fonts/IBMPlexSans-Regular.ttf','fonts/IBMPlexSans-SemiBold.ttf','fonts/IBMPlexMono-Medium.ttf'];
  const [kop,r,b,m]=await Promise.all(lijst.map(get));
  let bp=null; try{ bp=await get('assets/briefpapier.pdf'); }catch(_){}   // alleen voor het logo
  _as={kop,r,b,m,bp}; return _as;
}

const hex=h=>{ const n=parseInt(h.slice(1),16); return window.PDFLib.rgb((n>>16&255)/255,(n>>8&255)/255,(n&255)/255); };
const mix=(a,b,t)=>{ const A=parseInt(a.slice(1),16), B=parseInt(b.slice(1),16); const c=s=>Math.round(((A>>s)&255)*(1-t)+((B>>s)&255)*t); return window.PDFLib.rgb(c(16)/255,c(8)/255,c(0)/255); };

// zelfde kleuren als de tool (licht thema)
const KLEUR={
  tz:['#B83E0F','#FBE9DD'], avr:['#946000','#FAF0D8'], overig:['#56636D','#E7ECEF'],
  niet:['#1B5A9E','#E2EDF9'], aor:['#1B5A9E','#E2EDF9'], sv:['#0F6F86','#DDF1F5'], aos:['#0F6F86','#DDF1F5'],
  zone:['#5B2D86','#EFE8F6'], res:['#5B2D86','#EFE8F6']
};
const LABEL={tz:'Binnen thermische zone', niet:'Buiten thermische zone', overig:'Overige ruimte', sv:'Sterk geventileerd', avr:'AVR', aor:'AOR', aos:'AOS', zone:'Klimatiseringszones', res:'Uitkomst'};
const THERMO=['#1B5A9E','#0F6F86','#56636D','#946000','#B83E0F'];
const VERV={'⇒':'→','✗':'×','≈':'~','↳':'-','≥':'>=','≤':'<=','→':'-','✓':'v'};

async function maak(data){
  const as=await assets(); const {PDFDocument}=window.PDFLib;
  const doc=await PDFDocument.create(); doc.registerFontkit(window.fontkit);
  const fK=await doc.embedFont(as.kop,{subset:true}), fR=await doc.embedFont(as.r,{subset:true}), fB=await doc.embedFont(as.b,{subset:true}), fM=await doc.embedFont(as.m,{subset:true});
  let logo=null;
  if(as.bp){ try{ const src=await PDFDocument.load(as.bp); logo=await doc.embedPage(src.getPage(0),{left:356,bottom:756,right:572,top:812}); }catch(_){} }
  doc.setTitle("Beslisschema's ISSO 82.1"+(data.project?' – '+data.project:''));
  doc.setAuthor(data.auteur||'Visser Inspecties'); doc.setCreator("Visser Inspecties – beslisschema's ISSO 82.1");

  const INK=hex('#18232A'), MUTED=hex('#5A6870'), LINE=hex('#D5DCDE'), SOFT=hex('#EEF3F1'), ACC=hex('#5B2D86'), ACCS=hex('#EFE8F6'), WIT=window.PDFLib.rgb(1,1,1);
  const W=595.28, H=841.89, L=50, R=W-50, ONDER=H-62;
  const sets=new Map();
  const veilig=(t,f)=>{ if(!sets.has(f)) sets.set(f,new Set(f.getCharacterSet())); const s=sets.get(f);
    return Array.from(String(t==null?'':t)).map(c=>{ if(c==='\n'||c==='\t') return ' '; if(s.has(c.codePointAt(0))) return c; const v=VERV[c]; return v!=null && Array.from(v).every(x=>s.has(x.codePointAt(0)))?v:''; }).join(''); };
  const breed=(t,f,s)=>f.widthOfTextAtSize(veilig(t,f),s);
  let page, y;
  const tekst=(t,x,yy,s,f,c,align)=>{ t=veilig(t,f); const w=f.widthOfTextAtSize(t,s); const xx=align==='r'?x-w:align==='c'?x-w/2:x; page.drawText(t,{x:xx,y:H-yy,size:s,font:f,color:c}); return w; };
  const wrap=(t,f,s,max)=>{ const out=[]; String(t||'').split('\n').forEach(alinea=>{ let r=''; alinea.split(/\s+/).filter(Boolean).forEach(w=>{ const p=r?r+' '+w:w; if(breed(p,f,s)>max && r){ out.push(r); r=w; } else r=p; }); out.push(r); }); return out; };
  const thermo=(x,yy,w,h)=>{ const n=60; for(let i=0;i<n;i++){ const t=i/(n-1)*(THERMO.length-1), k=Math.min(THERMO.length-2,Math.floor(t)); page.drawRectangle({x:x+i*w/n,y:H-yy-h,width:w/n+0.4,height:h,color:mix(THERMO[k],THERMO[k+1],t-k)}); } };
  const rond=(x,yy,w,h,r,opt)=>{ page.drawSvgPath(`M ${r} 0 H ${w-r} Q ${w} 0 ${w} ${r} V ${h-r} Q ${w} ${h} ${w-r} ${h} H ${r} Q 0 ${h} 0 ${h-r} V ${r} Q 0 0 ${r} 0 Z`,Object.assign({x,y:H-yy},opt)); };
  const pagina=()=>{ page=doc.addPage([W,H]); thermo(0,0,W,5);
    tekst("BESLISSCHEMA'S ISSO 82.1"+(data.project?'  ·  '+data.project:''),L,28,7,fM,MUTED); y=48; };
  const ruimte=h=>{ if(y+h>ONDER){ pagina(); return true; } return false; };

  /* ── eerste pagina: kop ── */
  page=doc.addPage([W,H]); thermo(0,0,W,5);
  if(logo){ const sc=0.62; page.drawPage(logo,{x:R-216*sc,y:H-24-56*sc,width:216*sc,height:56*sc}); }
  tekst('ISSO-PUBLICATIE 82.1 · 7E DRUK',L,46,8,fM,MUTED);
  tekst("Beslisschema's ISSO 82.1",L,74,22,fK,INK);
  tekst('Verslag thermische zone en aangrenzende ruimten',L,92,10,fR,MUTED);
  y=112; thermo(L,y,R-L,3); y+=20;
  // projectgegevens
  const velden=[['PROJECT / ADRES',data.project||'–'],['DATUM',data.datum||''],['OPGESTELD DOOR',data.maker||'']];
  const kolW=[(R-L)*0.48,(R-L)*0.2,(R-L)*0.32]; let x=L;
  velden.forEach((v,i)=>{ tekst(v[0],x,y,6.8,fM,MUTED); wrap(v[1],fB,9.5,kolW[i]-12).forEach((r,j)=>tekst(r,x,y+14+j*12.5,9.5,fB,INK)); x+=kolW[i]; });
  y+=14+12.5*Math.max(...velden.map((v,i)=>wrap(v[1],fB,9.5,kolW[i]-12).length))+16;

  /* ── overzicht ── */
  const E=data.entries||[];
  tekst('OVERZICHT',L,y,7.5,fM,ACC); y+=8;
  page.drawLine({start:{x:L,y:H-y},end:{x:R,y:H-y},thickness:0.6,color:LINE}); y+=14;
  const cx=[L,L+22,L+190,L+330];
  tekst('NR',cx[0],y,6.5,fM,MUTED); tekst('RUIMTE',cx[1],y,6.5,fM,MUTED); tekst('SOORT RUIMTE',cx[2],y,6.5,fM,MUTED); tekst('UITKOMST',cx[3],y,6.5,fM,MUTED); y+=12;
  E.forEach((e,i)=>{
    const kl=KLEUR[e.verdict]||KLEUR.res;
    const r1=wrap(e.ruimte,fB,9,cx[2]-cx[1]-10), r2=wrap(e.soort||'–',fR,9,cx[3]-cx[2]-10), r3=wrap(e.title,fR,9,R-cx[3]-14);
    const h=Math.max(r1.length,r2.length,r3.length)*12+8;
    if(ruimte(h)){}
    tekst(String(i+1),cx[0],y,9,fM,MUTED);
    r1.forEach((r,j)=>tekst(r,cx[1],y+j*12,9,fB,INK));
    r2.forEach((r,j)=>tekst(r,cx[2],y+j*12,9,fR,INK));
    page.drawCircle({x:cx[3]+3.5,y:H-y+3,size:3.5,color:hex(kl[0])});
    r3.forEach((r,j)=>tekst(r,cx[3]+12,y+j*12,9,fR,INK));
    y+=h-8; page.drawLine({start:{x:L,y:H-y+3},end:{x:R,y:H-y+3},thickness:0.4,color:LINE}); y+=11;
  });
  y+=14;

  /* ── per ruimte ── */
  const BINNEN=R-L-24;
  E.forEach((e,i)=>{
    const kl=KLEUR[e.verdict]||KLEUR.res, KC=hex(kl[0]), KB=hex(kl[1]);
    const titel=wrap(e.title,fB,11.5,BINNEN-4), soort=wrap(e.soort||'–',fB,10,BINNEN-4);
    const boxH=14+9+soort.length*13+10+9+titel.length*14.5+10;
    ruimte(30+boxH+40);
    tekst((i+1)+'. '+(e.ruimte||'(ruimte zonder naam)'),L,y+12,14,fK,INK);
    if(e.datum) tekst(e.datum,R,y+12,8,fR,MUTED,'r');
    y+=24;
    rond(L,y,R-L,boxH,6,{color:KB}); page.drawRectangle({x:L,y:H-y-boxH,width:5,height:boxH,color:KC});
    let yy=y+14+6;
    tekst('SOORT RUIMTE',L+18,yy,6.8,fM,MUTED); yy+=13;
    soort.forEach(r=>{ tekst(r,L+18,yy,10,fB,INK); yy+=13; }); yy+=6;
    tekst('UITKOMST · '+(LABEL[e.verdict]||'').toUpperCase(),L+18,yy,6.8,fM,KC); yy+=14.5;
    titel.forEach(r=>{ tekst(r,L+18,yy,11.5,fB,INK); yy+=14.5; });
    y+=boxH+14;

    // route en antwoorden
    tekst('ROUTE EN ANTWOORDEN',L,y,7,fM,ACC); y+=12;
    (e.lines||[]).forEach(raw=>{
      const l=String(raw); const t=l.trim(); if(!t) return;
      if(t.startsWith('•')){
        let q=t.slice(1).trim(), calc='';
        const m=q.match(/\s{2}\[(.*)\]$/); if(m){ calc=m[1]; q=q.slice(0,m.index); }
        const p=q.lastIndexOf(' → '); let ant=''; if(p>0){ ant=q.slice(p+3); q=q.slice(0,p); }
        let extra=''; const mx=ant.match(/\s\((overgenomen uit eerder antwoord|uitkomst van het doorlopen schema)\)$/); if(mx){ extra=mx[1]; ant=ant.slice(0,mx.index); }
        const qr=wrap(q,fR,8.8,BINNEN-14), ar=wrap(ant,fB,8.8,BINNEN-60), cr=calc?wrap(calc,fM,7.3,BINNEN-30):[];
        const h=qr.length*11.5+ar.length*11.5+(extra?10:0)+cr.length*10+7;
        ruimte(h);
        page.drawCircle({x:L+15,y:H-y+3,size:1.6,color:MUTED});
        qr.forEach(r=>{ tekst(r,L+22,y,8.8,fR,INK); y+=11.5; });
        const aw=tekst('Antwoord',L+22,y,6.8,fM,MUTED);
        ar.forEach((r,j)=>{ tekst(r,L+22+aw+8,y,8.8,fB,ACC); y+=11.5; });
        if(extra){ tekst(extra,L+22+aw+8,y-1,7.3,fR,MUTED); y+=10; }
        cr.forEach(r=>{ tekst(r,L+22+aw+8,y-1,7.3,fM,MUTED); y+=10; });
        y+=7;
      } else if(t.startsWith('⇒')){
        const tr=wrap(t.slice(1).trim(),fB,9,BINNEN-24); const h=tr.length*12+12;
        ruimte(h);
        rond(L+10,y-9,R-L-10,h-4,4,{color:SOFT});
        tekst('UITKOMST',L+18,y+1,6.5,fM,MUTED);
        tr.forEach((r,j)=>tekst(r,L+70,y+1+j*12,9,fB,INK)); y+=h+2;
      } else if(t.startsWith('(')){
        ruimte(14); tekst(t,L+14,y,7.5,fR,MUTED); y+=13;
      } else if(t.startsWith('-')){
        const tr=wrap(t.slice(1).trim(),fR,8.5,BINNEN-40); ruimte(tr.length*11+4);
        tr.forEach(r=>{ tekst('–  '+r,L+40,y,8.5,fR,INK); y+=11; }); y+=3;
      } else {
        const sub=l.replace(/^\s+/,'').startsWith('↳') || /^\s{2}\S/.test(l);
        const kop=t.replace(/^↳\s*/,'');
        const tr=wrap((sub?'↳ ':'')+kop,fM,7.6,BINNEN); ruimte(tr.length*11+18);
        y+=4; tr.forEach(r=>{ tekst(r,L+(sub?12:0),y,7.6,fM,ACC); y+=11; }); y+=4;
      }
    });
    y+=18;
  });

  /* ── voet op elke pagina ── */
  const pages=doc.getPages(), N=pages.length;
  pages.forEach((p,i)=>{ page=p;
    page.drawLine({start:{x:L,y:42},end:{x:R,y:42},thickness:0.5,color:LINE});
    tekst('Bron: ISSO-publicatie 82.1, 7e druk  ·  '+(data.voet||'Visser Inspecties · EnergiePrestatie-advies'),L,H-28,7,fR,MUTED);
    tekst('pagina '+(i+1)+' van '+N,R,H-28,7,fM,MUTED,'r');
  });
  return await doc.save();
}

window.BeslisPdf={maak};
})();
