"""Bijlage 4 woningbouw basis - invulbare PDF in huisstijl Visser Inspecties."""
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from pypdf import PdfReader, PdfWriter

REPO = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else "bijlage4.pdf"
TMP = OUT + ".tmp.pdf"

for naam, f in [("MW-L", "300-normal"), ("MW", "400-normal"), ("MW-B", "700-normal"), ("MW-I", "400-italic")]:
    pdfmetrics.registerFont(TTFont(naam, f"{REPO}/fonts/Merriweather-{f}.ttf"))

PAARS, PAARS_D = HexColor("#432d6a"), HexColor("#372968")
GRIJS, INKT = HexColor("#5f5872"), HexColor("#1e1830")
TINT, LIJN = HexColor("#f4f2f6"), HexColor("#d9d5e1")
ORANJE = HexColor("#ec670a")
LABELKLEUREN = ["#019541", "#54ae32", "#c6d500", "#ffee02", "#faba00", "#ec670a"]

W, H = 595.28, 841.89
L, R = 56.69, W - 56.69
TOP, MAX = 140, 688          # bruikbare hoogte binnen het briefpapier (vanaf boven gemeten)
DRUK = "ISSO 82.1 7e druk"

# ── inhoud ────────────────────────────────────────────────────────────
SECTIES = [
    ("Algemeen", False, [
        "Aanvraag bouwvergunning/bouwmelding inclusief energieprestatieberekening",
        "Verleende bouwvergunning",
        "Adressenbestand met kadastrale gegevens (BAG pand-ID/object-ID) van alle objecten",
        "Huisnummerbesluit (overzicht van bouwnummer met bijbehorende huisnummers)",
        "Verklaring dat de installaties voor ruimteverwarming zijn ingeregeld (verklaring waarop is aangegeven dat de inregeling van de installatie voldoet aan de eisen gesteld in het opnameprotocol)",
        "Verklaring dat de installaties voor tapwater zijn ingeregeld (verklaring waarop is aangegeven dat de inregeling van de installatie voldoet aan de eisen gesteld in het opnameprotocol)",
        "Verklaring dat de installaties voor ruimtekoeling zijn ingeregeld (verklaring waarop is aangegeven dat de inregeling van de installatie voldoet aan de eisen gesteld in het opnameprotocol)",
        "Verzamellijsten met daarop de installaties, zoals bijvoorbeeld type opwekkers voor ruimteverwarming e.d.",
        "Verzamellijsten met daarop de installaties, zoals bijvoorbeeld type opwekkers voor tapwater e.d.",
        "Verzamellijsten met daarop de installaties, zoals bijvoorbeeld type opwekkers voor ruimtekoeling e.d.",
        "Verzamellijsten met daarop type kozijnen/kozijnstaat en beglazingen",
        "Leverbon/factuur met productspecificatie en afleveradres voor zowel na-isolatie als alle installaties",
    ]),
    ("Bouwfysische berekeningen", False, [
        "Rc-waarde berekeningen van de constructies (volledige berekeningen)",
        "U-waarde berekeningen van de kozijnen incl. beglazing",
        "Dikte en type isolatiemateriaal",
        "Aansluiting isolatiemateriaal (foto’s tijdens het aanbrengen isolatiemateriaal)",
    ]),
    ("Bouwkundige aspecten/plattegronden/tekeningen", True, [
        "Bouwkundige tekeningen op schaal met afmetingen",
        "Plattegronden",
        "Gevelaanzichten",
        "Dwarsdoorsnede",
        "Detailtekeningen van de bouwkundige constructies van het gebouw (kunnen ook onderdeel zijn van de eerder genoemde bouwkundige tekeningen)",
    ]),
    ("Installaties/verzamellijst/documentatie", True, [
        "Installatieontwerp van gebouw (o.a. installatietekeningen voor verwarming, koeling en warmtapwater)",
        "Ontwerp- en installatietekeningen voor verwarming (legplan bij bijvoorbeeld vloerverwarming)",
        "Ontwerp- en installatietekeningen voor tapwatersysteem",
        "Ontwerp- en installatietekeningen voor koeling",
        "Ontwerp- en installatietekeningen voor ventilatie (met luchtdebieten)",
        "Principeschema klimaatinstallatie (bij o.a. warmtepompsystemen)",
        "Regeltechnische omschrijving klimaatinstallaties (aanvoertemperatuur, wijze van regeling etc.)",
        "PV-panelen en legplan",
    ]),
    ("Inregelverklaringen", False, ["Ruimteverwarming", "Tapwater", "Koeling"]),
    ("Rapportages/documenten", False, ["Luchtdichtheidsmetingen Qv-10", "Thermografisch onderzoek"]),
]
KOLOMMEN = ["Toets Bbl", "Revisie", "Bestek"]

INTRO = ("In de onderstaande lijst geeft de opdrachtgever aan welke informatie van het betreffende gebouw "
         "hij of zij beschikbaar stelt aan de EnergiePrestatie-adviseur. Via ISSO Open (open.isso.nl) is een "
         "standaard intakeformulier te downloaden. Hoe meer informatie wordt aangeleverd, hoe beter het "
         "rekenresultaat. De aangeleverde informatie wordt aangegeven met een vinkje.")
LETOP = ("Alleen aangevinkte onderdelen zijn door de opdrachtgever aangeleverd. Staat het vakje hieronder "
         "aangevinkt, of is verder niets aangevinkt, dan heeft de EnergiePrestatie-adviseur geen informatie "
         "van de opdrachtgever ontvangen.")

# ── hulpfuncties ──────────────────────────────────────────────────────
c = canvas.Canvas(TMP, pagesize=(W, H))
c.setTitle("Bijlage 4 – Checklist beschikbaargestelde informatie – Woningbouw Basis")
c.setAuthor("John Visser – Visser Inspecties")
c.setSubject(DRUK)
form = c.acroForm
pagina = 0
top = TOP


def y(t):            # afstand vanaf boven → reportlab-coördinaat
    return H - t


def wrap(tekst, font, size, maxw):
    regels, r = [], ""
    for w in tekst.split():
        p = f"{r} {w}".strip()
        if stringWidth(p, font, size) > maxw and r:
            regels.append(r); r = w
        else:
            r = p
    if r:
        regels.append(r)
    return regels


def txt(t, x, tp, font="MW", size=9, kleur=INKT, align="l"):
    c.setFont(font, size); c.setFillColor(kleur)
    {"l": c.drawString, "r": c.drawRightString, "c": c.drawCentredString}[align](x, y(tp), t)


def vakje(naam, x, tp, size=11, aan=False, tooltip=""):
    """Klikbaar vakje; (x, tp) = linksboven."""
    form.checkbox(name=naam, tooltip=tooltip or naam, x=x, y=y(tp + size), size=size,
                  checked=aan, buttonStyle="check", borderStyle="solid", borderWidth=0.8,
                  borderColor=PAARS, fillColor=white, textColor=PAARS, forceBorder=True)


def veld(naam, x, tp, breed, hoog=14, tooltip=""):
    form.textfield(name=naam, tooltip=tooltip or naam, x=x, y=y(tp + hoog), width=breed, height=hoog,
                   fontName="Helvetica", fontSize=9, borderWidth=0, fillColor=white,
                   textColor=INKT, forceBorder=False)
    c.setStrokeColor(LIJN); c.setLineWidth(0.6)
    c.line(x, y(tp + hoog), x + breed, y(tp + hoog))


def nieuwe_pagina():
    global pagina, top
    if pagina:
        voet(); c.showPage()
    pagina += 1
    top = TOP


VOETEN = []


def voet():
    VOETEN.append(pagina)
    # labelkleurenbalkje + druk/pagina, boven de contactgegevens van het briefpapier
    sw = 60 / 6
    for i, k in enumerate(LABELKLEUREN):
        c.setFillColor(HexColor(k)); c.rect(R - 60 + i * sw, y(703), sw + 0.2, 2.5, stroke=0, fill=1)
    txt(DRUK, L, 706, "MW-L", 7, GRIJS)


def ruimte(nodig):
    if top + nodig > MAX:
        nieuwe_pagina()
        return True
    return False


VAK_X = L + 6           # vakjeskolom links
TEKST_X = L + 30
KOL_B = 52              # breedte per extra kolom
KOL_X0 = R - 3 * KOL_B  # begin extra kolommen


def sectiekop(titel, kolommen, vervolg=False):
    global top
    hoog = 20
    c.setFillColor(PAARS); c.rect(L, y(top + hoog), R - L, hoog, stroke=0, fill=1)
    txt(titel + (" (vervolg)" if vervolg else ""), TEKST_X, top + 13.5, "MW-B", 8.5, white)
    if kolommen:
        for i, k in enumerate(KOLOMMEN):
            txt(k, KOL_X0 + i * KOL_B + KOL_B / 2, top + 13.5, "MW-B", 7, white, "c")
    top += hoog


def regel(nr, tekst, kolommen):
    global top
    maxw = (KOL_X0 - 8 if kolommen else R - 8) - TEKST_X
    regels = wrap(tekst, "MW", 8.3, maxw)
    hoog = max(21, 9 + len(regels) * 11.5)
    if ruimte(hoog):
        sectiekop(huidige_sectie[0], kolommen, vervolg=True)
    # rij
    if nr % 2 == 0:
        c.setFillColor(TINT); c.rect(L, y(top + hoog), R - L, hoog, stroke=0, fill=1)
    vakje(f"info_{nr:02d}", VAK_X, top + (hoog - 11) / 2, tooltip=tekst[:80])
    ty = top + (hoog - len(regels) * 11.5) / 2 + 8.5
    for i, r in enumerate(regels):
        txt(r, TEKST_X, ty + i * 11.5, "MW", 8.3, INKT)
    if kolommen:
        for i, k in enumerate(KOLOMMEN):
            cx = KOL_X0 + i * KOL_B
            c.setStrokeColor(LIJN); c.setLineWidth(0.5); c.line(cx, y(top), cx, y(top + hoog))
            vakje(f"info_{nr:02d}_{k.split()[0].lower()}", cx + KOL_B / 2 - 5, top + (hoog - 10) / 2,
                  size=10, tooltip=f"{k}: {tekst[:60]}")
    c.setStrokeColor(LIJN); c.setLineWidth(0.5); c.line(L, y(top + hoog), R, y(top + hoog))
    top += hoog


# ── pagina 1: kop, projectgegevens, intro, LET OP ─────────────────────
nieuwe_pagina()
txt("Bijlage 4", L, top, "MW-B", 9, ORANJE)
top += 20
for r in wrap("Checklist beschikbaargestelde informatie door opdrachtgever", "MW-B", 17, R - L):
    txt(r, L, top, "MW-B", 17, PAARS); top += 22
txt("Woningbouw Basis (niet limitatief)", L, top, "MW-I", 10, GRIJS)
top += 22

# projectgegevens
txt("Adres object", L, top + 10, "MW-L", 8, GRIJS)
veld("adres_object", L + 72, top, 230, tooltip="Adres object")
txt("Projectnummer", L + 320, top + 10, "MW-L", 8, GRIJS)
veld("projectnummer", L + 395, top, R - (L + 395), tooltip="Projectnummer")
top += 30

for r in wrap(INTRO, "MW-L", 8.5, R - L):
    txt(r, L, top, "MW-L", 8.5, INKT); top += 13
top += 10

# LET OP-kader
lt = wrap(LETOP, "MW", 9, R - L - 34)
kh = 16 + 14 + len(lt) * 13 + 10 + 24
c.setFillColor(HexColor("#fdf0e6")); c.roundRect(L, y(top + kh), R - L, kh, 7, stroke=0, fill=1)
c.setStrokeColor(ORANJE); c.setLineWidth(1.2); c.roundRect(L, y(top + kh), R - L, kh, 7, stroke=1, fill=0)
c.setFillColor(ORANJE); c.rect(L, y(top + kh), 6, kh, stroke=0, fill=1)
tt = top + 18
txt("LET OP", L + 20, tt, "MW-B", 10, ORANJE); tt += 16
for r in lt:
    txt(r, L + 20, tt, "MW", 9, INKT); tt += 13
tt += 6
c.setFillColor(white); c.roundRect(L + 16, y(tt + 22), 300, 22, 4, stroke=0, fill=1)
vakje("geen_informatie_ontvangen", L + 22, tt + 5, size=12, aan=True,
      tooltip="Geen informatie ontvangen van de opdrachtgever")
txt("Geen informatie ontvangen van de opdrachtgever", L + 42, tt + 15, "MW-B", 9, PAARS)
top += kh + 18

# ── checklist ─────────────────────────────────────────────────────────
nr = 0
for titel, kolommen, items in SECTIES:
    huidige_sectie = (titel,)
    ruimte(20 + 21 * 2)          # kop niet los onderaan een pagina
    sectiekop(titel, kolommen)
    for t in items:
        nr += 1
        regel(nr, t, kolommen)
    top += 12

# ── ondertekening ─────────────────────────────────────────────────────
ruimte(120)
top += 14
txt("Ingevuld door opdrachtgever", L, top, "MW-B", 9, PAARS)
top += 14
half = (R - L) / 2
for i, (a, b) in enumerate([("Naam", "Bedrijf"), ("Datum", "Paraaf")]):
    txt(a, L, top + 10, "MW-L", 8, GRIJS); veld(a.lower(), L + 50, top, half - 70)
    txt(b, L + half, top + 10, "MW-L", 8, GRIJS); veld(b.lower(), L + half + 50, top, half - 50)
    top += 30

voet()
c.save()

# ── samenvoegen met briefpapier ───────────────────────────────────────
totaal = len(VOETEN)
inhoud = PdfReader(TMP)
brief = PdfReader(f"{REPO}/assets/briefpapier.pdf").pages[0]

# BTW/IBAN/KVK op het briefpapier staan als 0000 → wit overschrijven met echte gegevens (net als opdrachtbevestiging)
ov_pad = OUT + ".ov.pdf"
ov = canvas.Canvas(ov_pad, pagesize=(W, H))
for p in range(totaal):
    ov.setFillColor(white); ov.rect(250, H - 806, 200, 60, stroke=0, fill=1)
    ov.setFont("MW", 9.2); ov.setFillColor(PAARS_D)
    for i, t in enumerate(["BTW: NL003811767B63", "IBAN: NL30 KNAB 0409 0615 57", "KVK: 83376704"]):
        ov.drawString(255.6, H - (761 + i * 19), t)
    ov.setFont("MW-L", 7); ov.setFillColor(GRIJS)
    ov.drawRightString(R - 66, H - 706, f"Pagina {p + 1} van {totaal}")
    ov.showPage()
ov.save()
ovr = PdfReader(ov_pad)

w = PdfWriter()
w.append(inhoud)              # neemt pagina's mét formuliervelden over
for i, page in enumerate(w.pages):
    page.merge_page(brief, over=False)
    page.merge_page(ovr.pages[i], over=True)
w.set_need_appearances_writer(False)
w.add_metadata({"/Title": "Bijlage 4 – Checklist beschikbaargestelde informatie – Woningbouw Basis",
                "/Author": "John Visser – Visser Inspecties", "/Subject": DRUK})
with open(OUT, "wb") as f:
    w.write(f)
print("pagina's:", totaal, "→", OUT)
