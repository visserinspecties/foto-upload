/* Visser Inspecties tools — "home"-knopje (⌂) uiterst rechtsboven, terug naar het dashboard.
   Gebruik: <script src="assets/home-knop.js" defer></script> onderaan de <head>.
   - Heeft de pagina een paarse balk (.band) zonder ⌂? Dan komt het knopje rechts in die balk.
   - Anders zweeft het knopje vast rechtsboven, en schuift de kopregel iets op zodat niets eronder verdwijnt.
   - Niet op het dashboard zelf, en niet als de pagina al een ⌂ heeft. */
(function () {
  function plaats() {
    var pad = location.pathname.split('/').pop();
    if (pad === '' || pad === 'index.html') return;              // dashboard zelf
    if (document.querySelector('[data-home-knop]')) return;       // al geplaatst
    var bestaand = Array.prototype.some.call(document.querySelectorAll('a[href="index.html"]'),
      function (a) { return a.textContent.trim() === '⌂'; });
    if (bestaand) return;                                          // pagina heeft er al een

    var a = document.createElement('a');
    a.href = 'index.html';
    a.textContent = '⌂';
    a.title = 'Terug naar het dashboard';
    a.setAttribute('aria-label', 'Terug naar het dashboard');
    a.setAttribute('data-home-knop', '');

    var basis = 'color:#fff;text-decoration:none;background:rgba(255,255,255,.14);border-radius:10px;' +
      'padding:8px 12px;font-size:13px;line-height:1;font-family:system-ui,-apple-system,sans-serif;';

    var band = document.querySelector('.band');
    if (band) {
      a.style.cssText = basis + 'margin-left:auto;flex:0 0 auto;';
      // staat er al iets met margin-left:auto (bv. de gebruikersnaam), dan direct erachter
      band.appendChild(a);
      var cs = getComputedStyle(band);
      if (cs.display !== 'flex') { a.style.cssText = basis + 'float:right;'; }
      else {
        var heeftAuto = Array.prototype.some.call(band.children, function (c) {
          return c !== a && getComputedStyle(c).marginLeft === 'auto';
        });
        if (heeftAuto) a.style.marginLeft = '0';
      }
      return;
    }

    // geen paarse balk: zwevend knopje in huisstijl-paars
    a.style.cssText = basis + 'position:fixed;top:10px;right:12px;z-index:9999;' +
      'background:#432d6a;box-shadow:0 2px 8px rgba(0,0,0,.18);';
    document.body.appendChild(a);
    var kop = document.querySelector('header, .header, .header-row, .top');
    if (kop) {
      var pr = parseFloat(getComputedStyle(kop).paddingRight) || 0;
      if (pr < 56) kop.style.paddingRight = '56px';
      // kopregel bovenaan de pagina: knopje verticaal in die kopregel centreren
      var r = kop.getBoundingClientRect();
      if (r.top <= 2 && r.height >= 30 && r.height <= 120) {
        a.style.top = Math.max(4, Math.round(r.top + (r.height - a.offsetHeight) / 2)) + 'px';
      }
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', plaats);
  else plaats();
})();
