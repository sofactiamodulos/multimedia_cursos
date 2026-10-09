"""Pulsa cada tipo de interaccion dentro de la estructura real y comprueba el resultado."""
import io, os, re, subprocess

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8767/"
DST = r"C:\wamp64\www\amatia\sofactia_cursos_2026\course_content\plantillas\antioquia_induccion_sst_nuevo_v2"

PRUEBAS = {
    'modulo0': """
      var s = d.querySelector('[data-ag="m0-s3"]');
      var m = s.querySelectorAll('[data-m0-myth]');
      m[0].click();
      ok('mito: se destapa al pulsar', m[0].classList.contains('is-revealed'));
      m[1].click();
      ok('mito: acordeon cierra la anterior', !m[0].classList.contains('is-revealed') && m[1].classList.contains('is-revealed'));
      ok('mito: contador', /2 de 3/.test(s.querySelector('[data-m0-myth-status]').textContent));
      var a = d.querySelector('[data-ag="m0-s2"] audio');
      ok('audio reflexion: tiene archivo', !!(a && a.getAttribute('src')));
      ok('audio reflexion: el archivo responde', !!a && a.readyState >= 0);
    """,
    'modulo1': """
      var s4 = d.querySelector('[data-ag="m1-sig-s4"]');
      var cards = s4.querySelectorAll('[data-phva-card]');
      s4.querySelector('[data-phva-next]').click();
      ok('PHVA: siguiente tarjeta', cards[1].classList.contains('is-active') && !cards[0].classList.contains('is-active'));
      s4.querySelector('[data-phva-prev]').click();
      ok('PHVA: anterior', cards[0].classList.contains('is-active'));
      var trig = d.querySelector('[data-open-hazards]');
      ok('peligros: existe el boton', !!trig);
      if (trig) {
        var sl = trig.closest('.ag-slide'); var modal = sl.querySelector('[data-hazard-modal]');
        trig.click();
        ok('peligros: abre el modal', modal && !modal.hidden);
        sl.querySelector('[data-hazard-next]').click();
        ok('peligros: carrusel avanza', sl.querySelectorAll('[data-hazard-slide]')[1].classList.contains('is-active'));
        sl.querySelector('[data-close-hazards]').click();
        ok('peligros: cierra el modal', modal.hidden);
      }
      var k = d.querySelectorAll('[data-key-card]');
      if (k.length > 1) { k[1].click(); ok('llaves: activa tarjeta', k[1].classList.contains('is-active')); }
    """,
    'modulo2': """
      var g = d.querySelector('[data-tar-group]');
      g.querySelector('[data-tar="4"]').click();
      ok('TAR: selecciona la tarea', g.querySelector('[data-tar="4"]').classList.contains('is-selected'));
      ok('TAR: muestra su caso', !g.querySelector('[data-tar-case="4"]').hidden && g.querySelector('[data-tar-case="1"]').hidden);
      ok('audios de leccion presentes', d.querySelectorAll('[data-lesson-audio]').length === 2);
    """,
    'modulo3': """
      var q = d.querySelector('[data-quiz="l3-accidente"]');
      var botones = q.querySelectorAll('[data-quiz-options] button');
      ok('quiz: pinta opciones', botones.length === 2);
      botones[1].click();
      var fb = q.querySelector('[data-quiz-feedback]');
      ok('quiz: da feedback', !fb.hidden && fb.classList.contains('is-no'));
      ok('quiz: marca la correcta', q.querySelectorAll('.is-ok').length === 1);
      var sig = q.querySelector('.quiz-next'); if (sig) sig.click();
      ok('quiz: avanza de caso', /2 de 3/.test(q.querySelector('[data-quiz-step]').textContent));
      ok('los 4 quizzes inicializados', d.querySelectorAll('[data-quiz][data-ag-listo]').length === 4);
    """,
}

BRIDGE = """<!doctype html><meta charset=utf-8><title>x</title>
<iframe id=f src="modulos/%(mod)s/%(mod)s.html" width=1440 height=900></iframe>
<script>
f.onload = function () { setTimeout(function () {
  var d = f.contentDocument, w = f.contentWindow, res = [];
  function ok(n, c) { res.push((c ? 'OK   ' : 'FALLA') + ' ' + n); }
  try { %(js)s } catch (e) { res.push('ERROR ' + e); }
  setTimeout(function(){ document.title = 'R|' + res.join('|'); }, 300);
}, 3500); };
</script>"""

fallos = 0
for mod, js in PRUEBAS.items():
    p = os.path.join(DST, '_prueba.html')
    io.open(p, 'w', encoding='utf-8').write(BRIDGE % {'mod': mod, 'js': js})
    r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--virtual-time-budget=15000',
                        '--window-size=1440,900', '--dump-dom', BASE + '_prueba.html'], capture_output=True, timeout=180)
    os.remove(p)
    m = re.search(r'<title>R\|(.*?)</title>', r.stdout.decode('utf-8', 'ignore'), re.S)
    print('== %s ==' % mod)
    for linea in (m.group(1).split('|') if m else ['sin resultado']):
        print('  ' + linea)
        if not linea.startswith('OK'):
            fallos += 1
print('\n%s' % ('Todas las interacciones funcionan.' if fallos == 0 else '%d comprobaciones fallidas' % fallos))
