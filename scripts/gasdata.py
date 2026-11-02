"""Zet de open kleinverbruiksdata van netbeheerders om naar kleine JSON-bestanden per postcodegebied (PC4).
Gebruikt door de Pand analyse-app om per postcode te laten zien of woningen een eigen gasaansluiting hebben
(indicatie eigen cv-ketel) of niet (indicatie blokverwarming / stadswarmte / all-electric).
Uitvoer: gas/<PC4>.json  {"b":"Stedin 2026","r":[[van,tot,straat,"G"|"E",aantal,sja],...]}  +  gas/index.json"""
import csv, io, json, os, sys, urllib.request, collections, datetime

BRONNEN = [  # (naam, url) — nieuwste bestand per netbeheerder; jaarlijks bijwerken
    ("Stedin 2026", "https://www.stedin.net/-/media/project/online/files/zakelijk/open-data/stedin-kleinverbruikgegevens-2026.csv"),
]
UIT = sys.argv[1] if len(sys.argv) > 1 else "gas"

def getal(s):
    try: return float(str(s).replace(".", "").replace(",", "."))
    except Exception: return None

per = collections.defaultdict(list)
meta = []
for naam, url in BRONNEN:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Erkend-Energielabel.nl gasdata)"})
    ruw = urllib.request.urlopen(req, timeout=300).read()
    tekst = ruw.decode("utf-8-sig", errors="replace")
    rd = csv.DictReader(io.StringIO(tekst), delimiter=";")
    n = 0
    for r in rd:
        prod = (r.get("PRODUCTSOORT") or "").strip().upper()
        if prod not in ("GAS", "ELK"): continue
        van = (r.get("POSTCODE_VAN") or "").replace(" ", "").upper(); tot = (r.get("POSTCODE_TOT") or van).replace(" ", "").upper()
        if len(van) != 6: continue
        aantal = int(getal(r.get("AANSLUITINGEN_AANTAL")) or 0)
        sja = getal(r.get("SJA_GEMIDDELD") or r.get("SJV_GEMIDDELD"))
        rij = [van, tot, (r.get("STRAATNAAM") or "").strip(), "G" if prod == "GAS" else "E", aantal, round(sja) if sja is not None else None, naam]
        for pc4 in sorted({van[:4], tot[:4]}): per[pc4].append(rij)
        n += 1
    meta.append({"bron": naam, "url": url, "regels": n})
    print(naam, n, "regels", file=sys.stderr)

os.makedirs(UIT, exist_ok=True)
for pc4, rijen in per.items():
    with open(os.path.join(UIT, pc4 + ".json"), "w", encoding="utf-8") as f:
        json.dump({"r": rijen}, f, ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(UIT, "index.json"), "w", encoding="utf-8") as f:
    json.dump({"bijgewerkt": datetime.date.today().isoformat(), "bronnen": meta, "pc4": len(per)}, f, ensure_ascii=False, indent=1)
print(len(per), "postcodegebieden", file=sys.stderr)
