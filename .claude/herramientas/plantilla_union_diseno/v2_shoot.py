"""Captura una pagina del curso nuevo (servido por HTTP) en un slider concreto.
Uso: shoot.py <ruta> <modulo|-> <indice> <ancho> <alto> <salida.png> [js_extra]
Ademas devuelve un diagnostico: errores de consola visibles y medidas del slider."""
import os, sys, subprocess, re, io

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8767/"
DST = r"C:\wamp64\www\amatia\sofactia_cursos_2026\course_content\plantillas\antioquia_induccion_sst_nuevo_v2"

ruta, modulo, idx, w, h, out = sys.argv[1:7]
extra = sys.argv[7] if len(sys.argv) > 7 else ''

BRIDGE = """<!doctype html><meta charset=utf-8><title>x</title>
<style>html,body{margin:0;background:#333}iframe{border:0;display:block}</style>
<script>
try { if ('%(mod)s' !== '-') localStorage.setItem('equsera_%(mod)s_slider_index', '%(idx)s'); } catch(e) {}
</script>
<iframe id=f src="%(ruta)s" width=%(w)s height=%(h)s></iframe>
<script>
f.onload = function () {
  setTimeout(function () {
    var d = f.contentDocument, w = f.contentWindow, r = [];
    try { %(extra)s } catch (e) { r.push('extra:' + e); }
    setTimeout(function () {
      var act = d.querySelector('.content-section.active');
      var sc = d.querySelector('.module-content-scroll');
      if (act) {
        r.push('activo=' + act.id + ' ' + (act.dataset.sliderId || ''));
        r.push('slide_h=' + Math.round(act.scrollHeight));
      }
      if (sc) r.push('zona_h=' + Math.round(sc.clientHeight) + ' zona_scroll=' + Math.round(sc.scrollHeight));
      r.push('doc_h=' + d.documentElement.scrollHeight + ' vp=' + w.innerHeight);
      r.push('ancho_doc=' + d.documentElement.scrollWidth + ' vp_w=' + w.innerWidth);
      document.title = 'R|' + r.join('|');
    }, 900);
  }, 2600);
};
</script>"""

p = os.path.join(DST, '_shot.html')
io.open(p, 'w', encoding='utf-8').write(BRIDGE % {'ruta': ruta, 'mod': modulo, 'idx': idx, 'w': w, 'h': h, 'extra': extra})
args = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
        '--autoplay-policy=no-user-gesture-required', '--virtual-time-budget=9000',
        '--window-size=%d,%d' % (max(int(w), 560), int(h) + 40)]
if int(w) < 600:
    args.append('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')
r = subprocess.run(args + ['--dump-dom', BASE + '_shot.html'], capture_output=True, timeout=120)
m = re.search(r'<title>R\|(.*?)</title>', r.stdout.decode('utf-8', 'ignore'), re.S)
print('  ' + ('\n  '.join(m.group(1).split('|')) if m else 'sin diagnostico'))
subprocess.run(args + ['--screenshot=' + out, BASE + '_shot.html'], capture_output=True, timeout=120)
os.remove(p)
print('  captura:', out)
