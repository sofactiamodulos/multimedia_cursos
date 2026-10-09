"""Comprueba que todas las imagenes (img, source y fondos CSS) cargan en portada, ruta y cada modulo."""
import io, os, re, subprocess
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8767/"
DST = r"C:\wamp64\www\amatia\sofactia_cursos_2026\course_content\plantillas\antioquia_induccion_sst_nuevo_v2"
PAGES = ['index.html', 'inicio/inicio.html'] + ['modulos/modulo%d/modulo%d.html' % (i, i) for i in range(4)]
BRIDGE = """<!doctype html><meta charset=utf-8><title>x</title>
<iframe id=f src="%(src)s" width=1440 height=900></iframe>
<script>
f.onload = function () { setTimeout(function () {
  var d = f.contentDocument, w = f.contentWindow, urls = {};
  d.querySelectorAll('img[src]').forEach(function (i) { urls[i.src] = 1; });
  d.querySelectorAll('source[srcset]').forEach(function (s) { urls[new URL(s.getAttribute('srcset'), d.baseURI).href] = 1; });
  d.querySelectorAll('[style*="url("]').forEach(function (e) { var m = e.getAttribute('style').match(/url\(['"]?([^'")]+)/); if (m) urls[new URL(m[1], d.baseURI).href] = 1; });
  Array.prototype.forEach.call(d.styleSheets, function (ss) { try { Array.prototype.forEach.call(ss.cssRules, function (r) {
    var t = r.cssText || '', re = /url\("?([^")]+\.(?:webp|png|jpe?g|svg))"?\)/g, m;
    while ((m = re.exec(t))) { if (/assets\/img/.test(m[1])) urls[new URL(m[1], ss.href || d.baseURI).href] = 1; }
  }); } catch (e) {} });
  var lista = Object.keys(urls).filter(function (u) { return /assets\/img/.test(u); }), pend = lista.length, out = [];
  if (!pend) { document.title = 'R|0'; return; }
  lista.forEach(function (u) {
    var im = new Image();
    im.onload = function () { out.push('OK ' + u.split('assets/img/')[1] + ' ' + im.naturalWidth + 'x' + im.naturalHeight); if (!--pend) fin(); };
    im.onerror = function () { out.push('ROTA ' + u); if (!--pend) fin(); };
    im.src = u;
  });
  function fin() { document.title = 'R|' + out.join('|'); }
}, 3500); };
</script>"""
rotas = 0
for pg in PAGES:
    p = os.path.join(DST, '_img.html')
    io.open(p, 'w', encoding='utf-8').write(BRIDGE % {'src': pg})
    r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--virtual-time-budget=30000', '--window-size=1440,900', '--dump-dom', BASE + '_img.html'], capture_output=True, timeout=200)
    os.remove(p)
    m = re.search(r'<title>R\|(.*?)</title>', r.stdout.decode('utf-8', 'ignore'), re.S)
    filas = m.group(1).split('|') if m else ['SIN RESULTADO']
    print(pg)
    for l in sorted(filas):
        print('   ' + l)
        if not l.startswith('OK') and l != '0': rotas += 1
print('\nImagenes rotas: %d' % rotas)
