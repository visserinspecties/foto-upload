# Label-server voor de Pand analyse-tool (Visser Inspecties)

De tool zoekt het geregistreerde energielabel op in EP-Online. EP-Online staat dat niet rechtstreeks
vanuit een website toe, daarom loopt het via een kleine tussenserver (Cloudflare Worker) op je eigen account.
Gebaseerd op de worker van Erkend-Energielabel.nl.

## Eenmalig instellen (± 10 minuten, gratis)

1. Maak een gratis account op https://dash.cloudflare.com (Workers Free: 100.000 verzoeken per dag).
2. Links: **Workers & Pages** → **Create** → **Create Worker** → naam `ep-label` → **Deploy**.
3. **Edit code** → alles weghalen → de inhoud van `worker.js` (deze map) erin plakken → **Deploy**.
4. Kopieer het adres van de worker. Huidige worker: `https://ep-labels.falling-brook-4828.workers.dev/` (staat als standaard in de tool).
5. Open de Pand analyse-tool → tab **Pand analyse** → zoek een adres → bij **Bestaand energielabel** op ⚙ →
   plak het adres → OK. De tool onthoudt het op dit apparaat (doe het op iPad, iPhone en pc één keer).

## Aanrader: officiële EP-Online-sleutel

Zonder sleutel leest de server het openbare zoekscherm van ep-online.nl. Met een (gratis) API-sleutel
gebruikt hij de officiële webservice, dat is betrouwbaarder.

1. Vraag een sleutel aan via https://apikey.ep-online.nl.
2. Cloudflare → je worker `ep-label` → **Settings** → **Variables and Secrets** → **Add** →
   type **Secret**, naam `EP_KEY`, waarde = je sleutel → **Deploy**.

## Testen

Open `https://ep-label.<jouwnaam>.workers.dev/?q=3311GP%20293` in de browser.
Je krijgt dan JSON terug met het label (`"klasse": ...`) of een melding dat er geen label is.
