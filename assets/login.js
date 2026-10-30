/* Visser Inspecties tools — centrale Microsoft-inlog.
   Alle tools delen één app-registratie en één refresh-token ('rt' in localStorage).
   Inloggen gebeurt altijd via inloggen.html; dat is het enige adres dat in Entra hoeft te staan.

   Gebruik in een tool:
     <script src="assets/login.js"></script>
     VILogin.ingelogd()          → true/false (er is een bewaarde inlog)
     VILogin.naarInlog()         → naar inloggen.html, en daarna automatisch terug naar deze pagina
     VILogin.inlogLink(tekst)    → HTML voor een link naar de inlogpagina die terugkeert naar deze pagina
     VILogin.naam()              → bewaarde weergavenaam (of '') */
(function (w) {
  function lees(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function terugAdres() {
    var pagina = location.pathname.split('/').pop() || 'index.html';
    return pagina + location.search + location.hash;
  }
  function inlogUrl() { return 'inloggen.html?terug=' + encodeURIComponent(terugAdres()); }
  w.VILogin = {
    ingelogd: function () { return !!lees('rt'); },
    naam: function () { return lees('vi_naam') || ''; },
    inlogUrl: inlogUrl,
    naarInlog: function () { location.href = inlogUrl(); },
    inlogLink: function (tekst) {
      return '<a href="' + inlogUrl().replace(/"/g, '&quot;') + '">' + (tekst || 'Inloggen met Microsoft') + '</a>';
    },
    /* Controleert of de bewaarde inlog nog werkt. Geeft {status:'ok'|'uit'|'onbekend', naam}.
       'onbekend' = geen verbinding met Microsoft; dan weten we het niet zeker. */
    controleer: function () {
      var rt = lees('rt');
      if (!rt) return Promise.resolve({ status: 'uit', naam: '' });
      return fetch('https://login.microsoftonline.com/984fd1fb-3d68-4c94-aff2-47f699fb5dae/oauth2/v2.0/token', {
        method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ client_id: 'fdf237c9-bf46-47fa-ab3d-a8834a73e284', grant_type: 'refresh_token',
          refresh_token: rt, scope: 'https://graph.microsoft.com/User.Read offline_access' })
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (!d.access_token) {
          if (d.error === 'invalid_grant') { try { localStorage.removeItem('rt'); } catch (e) {} return { status: 'uit', naam: '' }; }
          return { status: 'onbekend', naam: lees('vi_naam') || '' };
        }
        if (d.refresh_token) try { localStorage.setItem('rt', d.refresh_token); } catch (e) {}
        if (lees('vi_naam')) return { status: 'ok', naam: lees('vi_naam') };
        return fetch('https://graph.microsoft.com/v1.0/me?$select=displayName', { headers: { Authorization: 'Bearer ' + d.access_token } })
          .then(function (r) { return r.ok ? r.json() : {}; })
          .then(function (j) { if (j.displayName) try { localStorage.setItem('vi_naam', j.displayName); } catch (e) {}
            return { status: 'ok', naam: j.displayName || '' }; });
      }).catch(function () { return { status: 'onbekend', naam: lees('vi_naam') || '' }; });
    }
  };
})(window);
