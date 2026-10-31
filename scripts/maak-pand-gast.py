#!/usr/bin/env python3
"""Maakt pand-orientatie-gast.html en pand-3d-gast.html uit de gewone versies.

Gastversie = dezelfde tool, maar:
  - geen Microsoft-inlog en geen OneDrive (geen statusbalk, geen projectkeuze, geen "Opslaan in project")
  - geen knop "Projectgegevens (.txt) inlezen" en geen ⌂-knop naar het dashboard
  - eigen opslag in de browser (los van de gewone tools op hetzelfde adres)
  - de knop "Bekijk in 3D" gaat naar de 3D-gastversie (en terug)
  - PNG, PDF en draaibaar HTML werken gewoon en komen op het eigen apparaat

Opnieuw draaien na elke wijziging aan pand-orientatie.html of pand-3d.html:
    python3 scripts/maak-pand-gast.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VOORAF = """<script>
/* GASTVERSIE: geen inlog/OneDrive, eigen opslag (los van de gewone tool). */
var GASTVERSIE = true;
(function(){
  var P = 'gast_', S = Storage.prototype, g = S.getItem, z = S.setItem, r = S.removeItem;
  S.getItem = function(k){ return g.call(this, P + k); };
  S.setItem = function(k, v){ return z.call(this, P + k, v); };
  S.removeItem = function(k){ return r.call(this, P + k); };
})();
</script>
<style>
#od-status,#pj-scherm,#pj-let,#b-txt,.opslaan-vak,.vak:has(> #opslaan){display:none!important}
.gast-sub{font-size:12px;font-weight:400;opacity:.85;margin-top:2px}
header > div{flex:1}
@media (min-width: 801px){ .wrap{height:calc(100vh - 70px)!important} }
</style>
"""


def maak(bron, doel, vervangingen):
    s = (ROOT / bron).read_text(encoding='utf-8')

    def vervang(oud, nieuw, aantal=1):
        nonlocal s
        n = s.count(oud)
        if n != aantal:
            raise SystemExit(f'{bron}: verwacht {aantal}x, gevonden {n}x:\n{oud[:120]}')
        s = s.replace(oud, nieuw)

    # 1. Vlag + eigen opslag + verbergen, vóór alle andere scripts
    i = s.index('<script')
    s = s[:i] + VOORAF + s[i:]

    # 2. Titel, geen dashboard-knop
    s = s.replace('<title>', '<title>Gastversie · ', 1)
    vervang('<script src="assets/home-knop.js" defer></script>\n', '')

    # 3. Inloggen en OneDrive uitzetten
    vervang('async function controleerOneDrive() {\n',
            'async function controleerOneDrive() {\n  if (GASTVERSIE) return;\n')
    vervang('async function verwerkLoginCallback() {\n',
            'async function verwerkLoginCallback() {\n  if (GASTVERSIE) return false;\n')

    for oud, nieuw in vervangingen:
        vervang(oud, nieuw)

    (ROOT / doel).write_text(s, encoding='utf-8')
    print('Gemaakt:', doel, f'({len(s)//1024} kB)')


SUB = '<div class="gast-sub">Gastversie van Visser Inspecties — werkt zonder inloggen; bestanden komen op je eigen apparaat</div>'

maak('pand-orientatie.html', 'pand-orientatie-gast.html', [
    ('<header><h1>Pand-oriëntatie via BAG</h1></header>',
     '<header><div><h1>Pand-oriëntatie via BAG</h1>' + SUB + '</div></header>'),
    ("location.href = 'pand-3d.html?' + q.toString();",
     "location.href = 'pand-3d-gast.html?' + q.toString();"),
])

maak('pand-3d.html', 'pand-3d-gast.html', [
    ('<header><h1>Pand in 3D</h1><a href="pand-orientatie.html">← Pand-oriëntatie</a></header>',
     '<header><div><h1>Pand in 3D</h1>' + SUB + '</div><a href="pand-orientatie-gast.html">← Pand-oriëntatie</a></header>'),
    ('async function herstelUitProject() {\n',
     'async function herstelUitProject() {\n  if (GASTVERSIE) return;\n'),
    ("gemaakt met Pand in 3D'",
     "gemaakt met Pand in 3D van Visser Inspecties · www.visserinspecties.nl'"),
])
