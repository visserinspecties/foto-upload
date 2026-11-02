/* Visser Inspecties tools — vaste kleuren per windrichting (8 sectoren van 45°, NTA 8800; N = 337,5°–22,5°).
   Dezelfde kleuren als in de Pand analyse-tool. Gebruik: VI_RICHTING.kleur('ZW') of VI_RICHTING.kleurAz(215). */
(function (w) {
  var DIRS = ['N', 'NO', 'O', 'ZO', 'Z', 'ZW', 'W', 'NW'];
  var KLEUR = { N: '#1f4e9c', NO: '#2f8fbf', O: '#3aa776', ZO: '#9cc23a', Z: '#e3a21a', ZW: '#e0662a', W: '#c0392b', NW: '#7d4ea3' };
  var PLAT = '#c9d3cd';
  function richting(az) { return DIRS[Math.round((((az % 360) + 360) % 360) / 45) % 8]; }
  w.VI_RICHTING = { DIRS: DIRS, KLEUR: KLEUR, PLAT: PLAT, richting: richting,
    kleur: function (d) { return KLEUR[d] || PLAT; }, kleurAz: function (az) { return KLEUR[richting(az)]; } };
})(window);
