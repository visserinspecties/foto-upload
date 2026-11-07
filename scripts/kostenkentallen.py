"""
Kostenkentallen voor Pand Analyse: JSON <-> Excel.

De Pand Analyse leest de prijzen uit data/kostenkentallen-<jaar>.json.
Daarnaast staat er een Excel-versie (zelfde inhoud) om te lezen of aan te passen.

Gebruik:
  python scripts/kostenkentallen.py naar-excel data/kostenkentallen-2026.json
      -> maakt data/kostenkentallen-2026.xlsx
  python scripts/kostenkentallen.py naar-json data/kostenkentallen-2027.xlsx
      -> maakt data/kostenkentallen-2027.json (na aanpassen in Excel)

Nieuw jaar: kopieer de Excel naar een nieuwe jaarnaam, pas prijzen en het tabblad
"Info" aan, draai naar-json, en zet in pand-analyse.html KK_BESTAND op het nieuwe bestand.
Het oude bestand blijft staan, zodat je altijd kunt terugzien met welke prijzen een
eerder advies gemaakt is (de GitHub-archief-tool zet alles ook in OneDrive).
"""
import json
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

PAARS = PatternFill('solid', fgColor='432D6A')
WIT = Font(bold=True, color='FFFFFF')
META_VELDEN = ['titel', 'prijspeil', 'bron', 'overgenomen', 'let_op', 'uitleg']
LEESBAAR = {'egw': 'eengezins', 'mgw': 'meergezins', 'tus': 'tussen', 'enk': 'enkel',
            'pro': 'project', 'min': 'min', 'mid': 'gem', 'max': 'max'}


def kop(ws, waarden):
    ws.append(waarden)
    for c in ws[ws.max_row]:
        c.fill, c.font = PAARS, WIT
        c.alignment = Alignment(wrap_text=True, vertical='center')


def naar_excel(pad_json: Path):
    d = json.loads(pad_json.read_text(encoding='utf-8'))
    var = d['varianten']
    namen = [' '.join(LEESBAAR.get(x, x) for x in v.split('-')) for v in var]
    wb = Workbook()
    info = wb.active
    info.title = 'Info'
    kop(info, ['Veld', 'Waarde'])
    for k in META_VELDEN:
        info.append([k, d.get(k, '')])
    info.append(['varianten', ', '.join(var)])
    info.column_dimensions['A'].width = 14
    info.column_dimensions['B'].width = 110
    for r in info.iter_rows(min_row=2):
        r[1].alignment = Alignment(wrap_text=True, vertical='top')

    for blad, idx, fmt in (('Prijzen excl btw', 0, '#,##0.00'), ('Aandeel arbeid', 1, '0%')):
        ws = wb.create_sheet(blad)
        kop(ws, ['Code', 'Omschrijving', 'Eenheid'] + namen)
        ws.append(['', '', ''] + var)            # technische sleutels; niet wijzigen
        for c in ws[2]:
            c.font = Font(italic=True, color='888888', size=8)
        for code, m in d['maatregelen'].items():
            ws.append([code, m['e'], m['h']] + [x[idx] for x in m['v']])
            for c in ws[ws.max_row][3:]:
                c.number_format = fmt
        ws.column_dimensions['A'].width = 9
        ws.column_dimensions['B'].width = 70
        ws.column_dimensions['C'].width = 8
        for i in range(len(var)):
            ws.column_dimensions[ws.cell(1, 4 + i).column_letter].width = 11
        ws.freeze_panes = 'D3'
    uit = pad_json.with_suffix('.xlsx')
    wb.save(uit)
    print('gemaakt:', uit)


def naar_json(pad_xlsx: Path):
    wb = load_workbook(pad_xlsx, data_only=True)
    meta = {r[0].value: r[1].value or '' for r in wb['Info'].iter_rows(min_row=2) if r[0].value}
    prijzen, arbeid = wb['Prijzen excl btw'], wb['Aandeel arbeid']
    var = [c.value for c in prijzen[2][3:] if c.value]
    kk = {}
    for rp, ra in zip(prijzen.iter_rows(min_row=3), arbeid.iter_rows(min_row=3)):
        code = rp[0].value
        if not code:
            continue
        if ra[0].value != code:
            sys.exit(f'Volgorde van de tabbladen klopt niet bij {code} / {ra[0].value}')
        v = []
        for cp, ca in zip(rp[3:3 + len(var)], ra[3:3 + len(var)]):
            if cp.value is None or ca.value is None:
                sys.exit(f'Lege cel bij {code}')
            v.append([round(float(cp.value), 2), round(float(ca.value), 3)])
        kk[code] = {'e': rp[1].value, 'h': rp[2].value, 'v': v}
    uit = {k: meta.get(k, '') for k in META_VELDEN}
    uit['varianten'] = var
    uit['maatregelen'] = kk
    pad = pad_xlsx.with_suffix('.json')
    pad.write_text(json.dumps(uit, ensure_ascii=False, indent=1), encoding='utf-8')
    print('gemaakt:', pad, f'({len(kk)} maatregelen)')


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('naar-excel', 'naar-json'):
        sys.exit(__doc__)
    (naar_excel if sys.argv[1] == 'naar-excel' else naar_json)(Path(sys.argv[2]))
