"""
Kostenkentallen voor Pand Analyse.

De Pand Analyse leest de prijzen uit data/kostenkentallen.json (altijd de actuele set).
Elke peildatum blijft daarnaast bewaard als eigen bestand, met het RVO-origineel in data/bron/.

Bron: RVO-kostenkentallen woningbouw, vast downloadadres:
  https://regelhulpenvoorbedrijven.nl/kostenkentallen/kostenkentallen/woningbouw.xlsx
De GitHub Action .github/workflows/kostenkentallen.yml haalt dat bestand wekelijks op
en draait 'uit-rvo'; alleen bij een wijziging worden nieuwe bestanden gemaakt.

Gebruik:
  python scripts/kostenkentallen.py uit-rvo <woningbouw.xlsx> [--url URL]
      RVO-Excel omzetten. Bij een wijziging t.o.v. data/kostenkentallen.json:
        data/bron/rvo-woningbouw-<peil>.xlsx      (origineel, ongewijzigd)
        data/kostenkentallen-<peil>.json / .xlsx  (omgezet, leesbaar met oranje balken)
        data/kostenkentallen.json                 (actueel, wat de tool gebruikt)
      Schrijft 'gewijzigd=true/false' naar $GITHUB_OUTPUT als die bestaat.
  python scripts/kostenkentallen.py naar-excel <kostenkentallen-....json>
      Leesbare Excel maken van een prijsbestand.

Prijs per variant = kolom 'Totaal bouwkosten (€/eh)' (incl. opslagen, excl. btw);
aandeel arbeid = 'Totaal arbeid' / 'Totaal directe kosten' (nodig voor 9%/21% btw).
"""
import datetime as dt
import json
import os
import re
import shutil
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
ACTUEEL = DATA / 'kostenkentallen.json'
RVO_URL = 'https://regelhulpenvoorbedrijven.nl/kostenkentallen/kostenkentallen/woningbouw.xlsx'
VARIANTEN = ['egw-tus-enk-min', 'egw-tus-enk-mid', 'egw-tus-enk-max',
             'egw-tus-pro-min', 'egw-tus-pro-mid', 'egw-tus-pro-max',
             'mgw-tus-enk-min', 'mgw-tus-enk-mid', 'mgw-tus-enk-max',
             'mgw-tus-pro-min', 'mgw-tus-pro-mid', 'mgw-tus-pro-max']
UITLEG = ("Per maatregel (RVO-code): e = omschrijving, h = eenheid, groep/sub = hoofdgroep (oranje balk) "
          "en subgroep, v = 12 varianten in de volgorde van 'varianten'; elke variant is "
          "[totaal bouwkosten per eenheid excl. btw incl. opslagen, aandeel arbeid 0-1] of null als RVO "
          "die variant niet geeft. egw = eengezinswoning, mgw = meergezinswoning, tus = tussenwoning, "
          "enk = enkele woning, pro = projectmatig, min/mid/max = goedkoop/gemiddeld/duur.")
MAANDEN = 'januari februari maart april mei juni juli augustus september oktober november december'.split()

# kolommen in de RVO-Excel (0-based)
K_SFB, K_VAR, K_SOORT, K_CODE, K_OMS, K_TOEL, K_EH = 0, 1, 2, 3, 4, 5, 7
K_ARBEID, K_DIRECT, K_BOUW_EH = 11, 18, 21

ORANJE = PatternFill('solid', fgColor='E9762B')
GRIJS = PatternFill('solid', fgColor='8C8C8C')
PAARS = PatternFill('solid', fgColor='432D6A')
WIT_VET = Font(bold=True, color='FFFFFF')


def getal(x):
    return float(x) if isinstance(x, (int, float)) else None


def schoon(oms):
    oms = re.sub(r',\s*(egw|mgw)-[a-z-]+\.?$', '', str(oms or '').strip())
    return re.sub(r'\s+', ' ', oms.rstrip('.')).strip()


def lees_rvo(pad: Path):
    ws = load_workbook(pad, data_only=True, read_only=True).worksheets[0]
    rijen = ws.iter_rows(values_only=True)
    kop = next(rijen)
    if 'Totaal bouwkosten (€/eh)' not in str(kop[K_BOUW_EH]) or 'Totaal\narbeid' != kop[K_ARBEID]:
        sys.exit(f'Onverwachte kolomindeling in {pad.name}: {kop[K_ARBEID]!r} / {kop[K_BOUW_EH]!r}. '
                 'RVO heeft het bestand veranderd; omzetting gestopt, niets bijgewerkt.')
    regel2 = str(next(rijen)[0] or '')
    m = re.search(r'peildatum\s+([a-z]+)\s+(\d{4})', regel2, re.I)
    if not m or m.group(1).lower() not in MAANDEN:
        sys.exit(f'Peildatum niet gevonden in regel 2: {regel2[:120]!r}')
    peil = f'{m.group(1).lower()} {m.group(2)}'

    groepen, maatr = [], {}
    groep = sub = None
    for r in rijen:
        soort = r[K_SOORT]
        if soort == '*':
            groep = {'nr': str(r[K_SFB]), 'naam': str(r[K_OMS]).strip(), 'onderdeel': str(r[K_TOEL] or '').strip(),
                     'subgroepen': []}
            groepen.append(groep)
        elif soort == '#' and groep:
            sub = {'nr': str(r[K_SFB]), 'naam': str(r[K_OMS]).strip()}
            groep['subgroepen'].append(sub)
        elif isinstance(soort, (int, float)) and soort != 0 and r[K_CODE] and r[K_VAR] in VARIANTEN:
            code = str(r[K_CODE]).strip()
            bouw, arbeid, direct = getal(r[K_BOUW_EH]), getal(r[K_ARBEID]), getal(r[K_DIRECT])
            if bouw is None:
                continue
            m_ = maatr.setdefault(code, {'e': schoon(r[K_OMS]), 'h': r[K_EH] or '', 'groep': groep['nr'],
                                         'sub': sub['nr'] if sub else '', 'v': [None] * len(VARIANTEN)})
            m_['v'][VARIANTEN.index(r[K_VAR])] = [round(bouw, 2),
                                                 round(arbeid / direct, 3) if direct and arbeid is not None else 0]
    if len(maatr) < 50:
        sys.exit(f'Maar {len(maatr)} maatregelen gevonden; dat klopt niet. Niets bijgewerkt.')
    return peil, groepen, maatr


def inhoud_gelijk(a, b):
    return all(a.get(k) == b.get(k) for k in ('prijspeil', 'groepen', 'maatregelen'))


def uit_rvo(pad: Path, url: str):
    peil, groepen, maatr = lees_rvo(pad)
    slug = peil.replace(' ', '-')
    vandaag = dt.date.today().isoformat()
    bronnaam = f'rvo-woningbouw-{slug}.xlsx'
    d = {'titel': 'RVO-kostenkentallen woningbouw — gebruikt door Pand Analyse',
         'prijspeil': peil,
         'bron': 'RVO-kostenkentallen woningbouw (kostenkentallen.rvo.nl)',
         'bron_url': url,
         'bronbestand': f'data/bron/{bronnaam}',
         'opgehaald': vandaag,
         'let_op': 'Bedragen zijn totale bouwkosten per eenheid (directe kosten + opslagen), excl. btw. '
                   'Het RVO-platform toont op het scherm alleen de directe kosten (zonder opslagen).',
         'uitleg': UITLEG, 'varianten': VARIANTEN, 'groepen': groepen, 'maatregelen': maatr}

    oud = json.loads(ACTUEEL.read_text(encoding='utf-8')) if ACTUEEL.exists() else {}
    gewijzigd = not inhoud_gelijk(oud, d)
    print(f'RVO-bestand: peildatum {peil}, {len(groepen)} hoofdgroepen, {len(maatr)} maatregelen')
    if gewijzigd:
        naam = f'kostenkentallen-{slug}'
        bestaand = DATA / f'{naam}.json'
        if bestaand.exists() and not inhoud_gelijk(json.loads(bestaand.read_text(encoding='utf-8')), d):
            naam += f'-bijgewerkt-{vandaag}'                 # tussentijdse RVO-update, zelfde peildatum
            bronnaam = f'rvo-woningbouw-{slug}-bijgewerkt-{vandaag}.xlsx'
            d['bronbestand'] = f'data/bron/{bronnaam}'
        (DATA / 'bron').mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pad, DATA / 'bron' / bronnaam)
        tekst = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
        (DATA / f'{naam}.json').write_text(tekst, encoding='utf-8')
        ACTUEEL.write_text(tekst, encoding='utf-8')
        naar_excel(DATA / f'{naam}.json')
        if oud:
            verschil(oud, d)
        print('GEWIJZIGD: nieuwe prijzen klaargezet als', naam)
    else:
        print('ONGEWIJZIGD: prijzen zijn gelijk aan data/kostenkentallen.json')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f'gewijzigd={"true" if gewijzigd else "false"}\npeil={peil}\n')


def verschil(oud, nieuw):
    """Korte samenvatting voor in de commit-log."""
    om, nm = oud.get('maatregelen', {}), nieuw['maatregelen']
    erbij, weg = sorted(set(nm) - set(om)), sorted(set(om) - set(nm))
    anders = [c for c in nm if c in om and om[c]['v'] != nm[c]['v']]
    print(f'  peildatum: {oud.get("prijspeil")} -> {nieuw["prijspeil"]}')
    print(f'  {len(anders)} maatregelen met andere prijzen, {len(erbij)} nieuw, {len(weg)} vervallen')
    if weg:
        print('  vervallen:', ', '.join(weg[:30]))


def naar_excel(pad_json: Path):
    d = json.loads(pad_json.read_text(encoding='utf-8'))
    var = d['varianten']
    namen = [v.replace('egw', 'eengezins').replace('mgw', 'meergezins').replace('-tus', '')
             .replace('-enk', ' enkel').replace('-pro', ' project').replace('-mid', ' gem')
             .replace('-min', ' min').replace('-max', ' max') for v in var]
    wb = Workbook()
    info = wb.active
    info.title = 'Info'
    info.append(['Veld', 'Waarde'])
    for c in info[1]:
        c.fill, c.font = PAARS, WIT_VET
    for k in ('titel', 'prijspeil', 'bron', 'bron_url', 'bronbestand', 'opgehaald', 'let_op', 'uitleg'):
        info.append([k, d.get(k, '')])
    info.column_dimensions['A'].width = 14
    info.column_dimensions['B'].width = 110
    for r in info.iter_rows(min_row=2):
        r[1].alignment = Alignment(wrap_text=True, vertical='top')

    per_groep = {}
    for code, m in d['maatregelen'].items():
        per_groep.setdefault(m['groep'], []).append((code, m))
    breedte = 5 + len(var)
    for blad, idx, fmt in (('Prijzen excl btw', 0, '#,##0.00'), ('Aandeel arbeid', 1, '0%')):
        ws = wb.create_sheet(blad)
        ws.append(['Code', 'Omschrijving', 'Eenheid', 'Groep', 'Subgroep'] + namen)
        for c in ws[1]:
            c.fill, c.font = PAARS, WIT_VET
            c.alignment = Alignment(wrap_text=True, vertical='center')
        for g in d['groepen']:
            ws.append([g['nr'], g['naam']] + [None] * (breedte - 2))       # oranje balk
            for c in ws[ws.max_row]:
                c.fill, c.font = ORANJE, WIT_VET
            subnamen = {s['nr']: s['naam'] for s in g['subgroepen']}
            huidige_sub = None
            for code, m in per_groep.get(g['nr'], []):
                if m['sub'] != huidige_sub:
                    huidige_sub = m['sub']
                    ws.append([huidige_sub, subnamen.get(huidige_sub, '')] + [None] * (breedte - 2))
                    for c in ws[ws.max_row]:
                        c.fill, c.font = GRIJS, WIT_VET
                ws.append([code, m['e'], m['h'], m['groep'], m['sub']] +
                          [x[idx] if x else None for x in m['v']])
                for c in ws[ws.max_row][5:]:
                    c.number_format = fmt
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 80
        for kol in 'CDE':
            ws.column_dimensions[kol].width = 8
        for i in range(len(var)):
            ws.column_dimensions[ws.cell(1, 6 + i).column_letter].width = 11
        ws.freeze_panes = 'F2'
    uit = pad_json.with_suffix('.xlsx')
    wb.save(uit)
    print('gemaakt:', uit.relative_to(ROOT) if uit.is_relative_to(ROOT) else uit)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'uit-rvo':
        url = a[a.index('--url') + 1] if '--url' in a else RVO_URL
        uit_rvo(Path(a[1]), url)
    elif len(a) == 2 and a[0] == 'naar-excel':
        naar_excel(Path(a[1]))
    else:
        sys.exit(__doc__)
