/* Visser Inspecties tools — zorgt dat de pagina's ook zonder bereik openen.
   Pagina's: eerst internet proberen (max. 4 s), anders de laatst bewaarde versie.
   Lettertypes en iconen: uit de bewaarde kopie, op de achtergrond bijwerken.
   Inloggen en OneDrive (Microsoft) gaan nooit via deze opslag. */
const CACHE = 'vi-tools-v1';
const START = ['./', 'index.html', 'foto-upload.html', 'icons/icon-180.png', 'icons/icon-192.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(START)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function withTimeout(promise, ms) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('timeout')), ms);
    promise.then(r => { clearTimeout(t); resolve(r); }, err => { clearTimeout(t); reject(err); });
  });
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // eigen pagina's en bestanden
  if (url.origin === self.location.origin) {
    e.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const net = fetch(req).then(res => {
        if (res.ok) cache.put(url.origin + url.pathname, res.clone());
        return res;
      });
      try {
        return await withTimeout(net, 4000);
      } catch (err) {
        const hit = await cache.match(req, { ignoreSearch: true });
        if (hit) return hit;
        return net; // niets bewaard: toch op het netwerk wachten
      }
    })());
    return;
  }

  // lettertypes van Google
  if (url.host === 'fonts.googleapis.com' || url.host === 'fonts.gstatic.com') {
    e.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const hit = await cache.match(req);
      const net = fetch(req).then(res => { if (res.ok || res.type === 'opaque') cache.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    })());
  }
  // al het andere (Microsoft-login, OneDrive) gaat gewoon direct naar internet
});
