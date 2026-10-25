#!/usr/bin/env python3
"""Maakt huismaten-gast.html uit huismaten-stap1.html.

Gastversie = dezelfde tool, maar:
  - geen Microsoft-inlog en geen OneDrive (geen rode balk, geen projectknoppen)
  - exports gaan alleen naar het eigen apparaat
  - eigen opslag in de browser (los van de gewone Huismaten op hetzelfde adres)
  - PDF: op elke pagina logo + "Gemaakt met de Huismaten-tool van Visser Inspecties",
    en beveiligd: alleen afdrukken toegestaan (niet bewerken, niet kopiëren)

Opnieuw draaien na elke wijziging aan huismaten-stap1.html:
    python3 scripts/maak-huismaten-gast.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRON = ROOT / 'huismaten-stap1.html'
DOEL = ROOT / 'huismaten-gast.html'

s = BRON.read_text(encoding='utf-8')


def vervang(oud, nieuw, aantal=1):
    global s
    n = s.count(oud)
    if n != aantal:
        raise SystemExit(f'Verwacht {aantal}x, gevonden {n}x:\n{oud[:120]}')
    s = s.replace(oud, nieuw)


# 1. Vlag + eigen opslag, vóór alle andere scripts
VOORAF = """<script>
/* GASTVERSIE: geen inlog/OneDrive, eigen opslag (los van de gewone Huismaten-tool). */
var GASTVERSIE = true;
(function(){
  var P = 'gast_', S = Storage.prototype, g = S.getItem, z = S.setItem, r = S.removeItem;
  S.getItem = function(k){ return g.call(this, P + k); };
  S.setItem = function(k, v){ return z.call(this, P + k, v); };
  S.removeItem = function(k){ return r.call(this, P + k); };
  if (window.indexedDB) {
    var open = indexedDB.open.bind(indexedDB);
    indexedDB.open = function(n, v){ return v === undefined ? open(P + n) : open(P + n, v); };
  }
})();
</script>
<style>#od-status,#project-banner,#btn-tekening-upload,#btn-excel-onedrive{display:none!important}</style>
"""
i = s.index('<script>')
s = s[:i] + VOORAF + s[i:]

# 2. Titel en ondertitel
vervang('<p class="sub">Kernmechanisme: vloeroppervlak en gevel/dakvlak tekenen</p>',
        '<p class="sub">Gastversie van Visser Inspecties — werkt zonder inloggen; PDF en Excel komen op je eigen apparaat</p>')
s = s.replace('<title>', '<title>Gastversie · ', 1)

# 3. Inloggen en OneDrive uitzetten
vervang('function loginMogelijk() { return location.origin === LOGIN_VASTE_ORIGIN; }',
        'function loginMogelijk() { return !GASTVERSIE && location.origin === LOGIN_VASTE_ORIGIN; }')
vervang('async function controleerOneDrive() {\n',
        'async function controleerOneDrive() {\n  if (GASTVERSIE) return;\n')
vervang('async function onedriveBeschikbaar(){',
        'async function onedriveBeschikbaar(){ if (GASTVERSIE) return false;')
vervang('function initProjectBanner() {\n',
        'function initProjectBanner() {\n  if (GASTVERSIE) return;\n')

# 4. Meldingen na export: niet rood "niet in OneDrive", maar gewoon "gemaakt"
vervang("  geenproject: 'ℹ️ geen project gekozen — niet geüpload',",
        "  geenproject: GASTVERSIE ? '✅ gemaakt — bewaard op dit apparaat' : 'ℹ️ geen project gekozen — niet geüpload',")
vervang("    const kleur = rec.status === 'ok' ? '#1d5a2b'",
        "    const kleur = (rec.status === 'ok' || (GASTVERSIE && rec.status === 'geenproject')) ? '#1d5a2b'")
vervang("  const naamTxt = r => `\"${r.naam}\"`;\n",
        "  const naamTxt = r => `\"${r.naam}\"`;\n"
        "  if (GASTVERSIE) {\n"
        "    el.style.cssText += ';display:block;background:#e3f1e3;color:#1d5a2b;border:2px solid #1d5a2b;';\n"
        "    el.innerHTML = '✅ ' + lijst.map(naamTxt).join(' en ') + ' gemaakt' + (isIOS() ? ' — tik hieronder op de knop om op te slaan.' : ' — staan in je downloadmap.');\n"
        "    return;\n"
        "  }\n")

# 5. PDF: beveiligen (alleen afdrukken) + vaste regel "Gemaakt met..."
vervang("const pdf = new jsPDF({orientation:'landscape', unit:'mm', format:'a3'});",
        "const pdf = new jsPDF(Object.assign({orientation:'landscape', unit:'mm', format:'a3'}, GASTVERSIE ? {encryption:{\n"
        "      userPassword:'',\n"
        "      ownerPassword: Array.from(crypto.getRandomValues(new Uint8Array(24)), b => b.toString(16).padStart(2,'0')).join(''),\n"
        "      userPermissions:['print']}} : {}));")
vervang("      pdf.addImage(LOGO_VISSER_B64, 'PNG', pageW-margin-logoBreedte, logoY, logoBreedte, logoHoogte);\n",
        "      pdf.addImage(LOGO_VISSER_B64, 'PNG', pageW-margin-logoBreedte, logoY, logoBreedte, logoHoogte);\n"
        "      if (GASTVERSIE) pdf.text('Gemaakt met de Huismaten-tool van Visser Inspecties · www.visserinspecties.nl', margin, pageH-margin+5.5);\n")
vervang("    const blob = pdf.output('blob');\n",
        "    if (GASTVERSIE) pdf.setProperties({creator:'Huismaten-tool - Visser Inspecties', author:'Visser Inspecties'});\n"
        "    const blob = pdf.output('blob');\n")

DOEL.write_text(s, encoding='utf-8')
print('Gemaakt:', DOEL.name, f'({len(s)//1024} kB)')
