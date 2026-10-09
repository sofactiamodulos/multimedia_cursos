"""Prueba la navegacion de la v2 con los botones propios de cada pantalla y
recoge los errores de JavaScript de la pagina."""
import io, os, re, subprocess

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8767/"
DST = r"C:\wamp64\www\amatia\sofactia_cursos_2026\course_content\plantillas\antioquia_induccion_sst_nuevo_v2"

BRIDGE = """<!doctype html><meta charset=utf-8><title>x</title>
<script>try{localStorage.clear()}catch(e){}</script>
<iframe id=f src="%(src)s" width=1440 height=900></iframe>
<script>
var errores = [], res = [], paso = 0;
function ok(n, c) { res.push((c ? 'OK   ' : 'FALLA') + ' ' + n); }
function engancha() {
  try {
    f.contentWindow.addEventListener('error', function (e) { errores.push((e.message || 'error') + ' @' + (e.filename || '').split('/').pop() + ':' + e.lineno); });
  } catch (e) {}
}
f.addEventListener('load', function () {
  engancha();
  paso += 1;
  var w = f.contentWindow, d = f.contentDocument;
  var ruta = w.location.pathname;
  setTimeout(function () {
    try { %(js)s } catch (e) { res.push('ERROR ' + e); fin(); }
  }, 3200);
});
function fin() {
  document.title = 'R|' + res.join('|') + '|ERRORES_JS=' + (errores.length ? errores.join(' ;; ') : 'ninguno');
}
</script>"""

JS = r"""
  if (paso === 1) {
    var secs = d.querySelectorAll('#sliders-container > .content-section');
    ok('modulo0: 4 pantallas cargadas', secs.length === 4);
    ok('sin menu lateral', !d.querySelector('.route-sidebar'));
    ok('sin module-header', !d.querySelector('.module-header'));
    ok('sin module-nav-footer', !d.querySelector('.module-nav-footer'));
    var act = d.querySelector('.content-section.active');
    ok('cabecera con progreso real (01 / 04)', /01 \/ 04/.test(act.textContent));
    act.querySelector('[data-ag-next]').click();
    setTimeout(function () {
      var a2 = d.querySelector('.content-section.active');
      ok('Continuar avanza a la pantalla 2', a2 && a2.id === 'section1');
      ok('la cabecera se actualiza (02 / 04)', /02 \/ 04/.test(a2.textContent));
      a2.querySelector('[data-ag-prev]').click();
      setTimeout(function () {
        ok('Anterior vuelve a la pantalla 1', d.querySelector('.content-section.active').id === 'section0');
        // ir a la ultima y pulsar Continuar: debe cerrar el modulo y abrir el modulo 1
        w.capsuleManager.showSection(3);
        setTimeout(function () {
          d.querySelector('.content-section.active [data-ag-next]').click();
        }, 500);
      }, 500);
    }, 500);
  } else if (paso === 2) {
    ok('el cierre de Momento 0 abre el modulo 1', /modulo1\.html$/.test(ruta));
    var p1 = d.querySelector('.content-section.active');
    ok('modulo1 arranca en su portada', p1 && p1.id === 'section0');
    // primera pantalla: su boton "Volver a lecciones" lleva a la ruta
    p1.querySelector('[data-ag-ruta]').click();
  } else if (paso === 3) {
    ok('Volver a lecciones abre la ruta', /inicio\.html$/.test(ruta));
    var cards = d.querySelectorAll('#routeGrid .lesson-card');
    ok('ruta: 4 tarjetas', cards.length === 4);
    ok('ruta: Momento 0 completado', cards[0].classList.contains('is-done'));
    ok('ruta: Momento 1 desbloqueado', !cards[1].classList.contains('is-locked'));
    ok('ruta: Momento 2 bloqueado', cards[2].classList.contains('is-locked'));
    ok('ruta: progreso 25%', /25%/.test(d.querySelector('[data-ruta-pct]').textContent));
    ok('ruta: boton ofrece el momento 01', /01/.test(d.querySelector('[data-ruta-abrir]').textContent));
    ok('ruta: sin menu lateral', !d.querySelector('.route-sidebar'));
    fin();
  }
"""

p = os.path.join(DST, '_nav.html')
io.open(p, 'w', encoding='utf-8').write(BRIDGE % {'src': 'modulos/modulo0/modulo0.html', 'js': JS})
r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--virtual-time-budget=40000',
                    '--window-size=1440,900', '--dump-dom', BASE + '_nav.html'], capture_output=True, timeout=240)
os.remove(p)
m = re.search(r'<title>R\|(.*?)</title>', r.stdout.decode('utf-8', 'ignore'), re.S)
fallos = 0
for l in (m.group(1).split('|') if m else ['sin resultado']):
    print('  ' + l)
    if l.startswith('FALLA') or l.startswith('ERROR ') or l == 'sin resultado':
        fallos += 1
print('\n%s' % ('Navegacion correcta.' if not fallos else '%d fallos' % fallos))
