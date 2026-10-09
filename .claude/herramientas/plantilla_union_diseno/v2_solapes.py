"""v2: cada pantalla trae su cabecera y su pie. Lo que importa ya no es solo que
nada salga de la ventana, sino que el contenido no quede TAPADO: por debajo del
pie o por encima de la cabecera de su propia pantalla."""
import io, os, re, subprocess, sys

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8767/"
DST = r"C:\wamp64\www\amatia\sofactia_cursos_2026\course_content\plantillas\antioquia_induccion_sst_nuevo_v2"
VIEWS = [(int(v.split('x')[0]), int(v.split('x')[1])) for v in (sys.argv[1:] or ['1440x900', '1366x768', '390x740'])]
MODS = ['modulo0', 'modulo1', 'modulo2', 'modulo3']
UA = '--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'

BRIDGE = """<!doctype html><meta charset=utf-8><title>x</title>
<script>try{localStorage.clear()}catch(e){}</script>
<iframe id=f src="modulos/%(mod)s/%(mod)s.html" width=%(w)d height=%(h)d></iframe>
<script>
f.onload = function () { setTimeout(function () {
  var d = f.contentDocument, w = f.contentWindow, out = [];
  var st = d.createElement('style'); st.textContent = '*,*::before,*::after{animation:none!important;transition:none!important}'; d.head.appendChild(st);
  var secs = d.querySelectorAll('#sliders-container > .content-section'), i = 0;
  function uno() {
    if (i >= secs.length) { document.title = 'R|' + out.join('|'); return; }
    w.capsuleManager.showSection(i);
    setTimeout(function () {
      var act = d.querySelector('.content-section.active');
      var vp = w.innerHeight;
      var pie = act.querySelector('.footer, .slide-footer');
      var cab = act.querySelector('.lesson-header, .slide-nav-head');
      var limAbajo = pie ? pie.getBoundingClientRect().top : vp;
      var limArriba = cab ? cab.getBoundingClientRect().bottom : 0;
      var zona = act.querySelector('.stage, .slide-stage, .activity-stage, .audio-stage, .evaluation-stage');
      var malos = [];
      var desplaza = zona && zona.scrollHeight > zona.clientHeight + 2 && /auto|scroll/.test(w.getComputedStyle(zona).overflowY);
      if (desplaza) {
        var zr = zona.getBoundingClientRect();
        limAbajo = zr.bottom; limArriba = zr.top;   /* lo que pasa del borde se alcanza desplazando */
      }
      if (zona) {
        zona.querySelectorAll('*').forEach(function (e) {
          if (!e.getClientRects().length) return;
          if (e.closest('[hidden]') || e.closest('[data-hazard-modal]')) return;
          var cs = w.getComputedStyle(e);
          if (cs.position === 'absolute' || cs.position === 'fixed' || cs.visibility === 'hidden') return;
          var r = e.getBoundingClientRect();
          if (r.height < 6 || r.width < 6) return;
          var cn = e.tagName.toLowerCase() + ((typeof e.className === 'string' && e.className) ? '.' + e.className.trim().split(/\\s+/)[0] : '');
          if (desplaza) {
            /* en zona desplazable solo es fallo lo que queda por ENCIMA del inicio de la zona */
            if (r.top < limArriba - 2 && zona.scrollTop === 0) malos.push(cn + ' sobre-inicio+' + Math.round(limArriba - r.top));
            else if (r.right > w.innerWidth + 2) malos.push(cn + ' derecha+' + Math.round(r.right - w.innerWidth));
            return;
          }
          if (r.bottom > limAbajo + 2) malos.push(cn + ' bajo-pie+' + Math.round(r.bottom - limAbajo));
          else if (r.top < limArriba - 2) malos.push(cn + ' sobre-cabecera+' + Math.round(limArriba - r.top));
          else if (r.right > w.innerWidth + 2) malos.push(cn + ' derecha+' + Math.round(r.right - w.innerWidth));
        });
      }
      if (zona) {
        /* bloques del escenario montados unos sobre otros (hijos directos y nietos) */
        var bloques = [];
        Array.prototype.forEach.call(zona.children, function (c) {
          bloques.push(c);
          Array.prototype.forEach.call(c.children, function (n) { bloques.push(n); });
        });
        bloques = bloques.filter(function (e) {
          if (!e.getClientRects().length || e.closest('[hidden]') || e.closest('[data-hazard-modal]')) return false;
          var cs = w.getComputedStyle(e);
          return cs.position !== 'absolute' && cs.position !== 'fixed' && cs.visibility !== 'hidden';
        });
        for (var x = 0; x < bloques.length; x++) for (var y = x + 1; y < bloques.length; y++) {
          var A = bloques[x], B = bloques[y];
          if (A.contains(B) || B.contains(A)) continue;
          var ra = A.getBoundingClientRect(), rb = B.getBoundingClientRect();
          var ix = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
          var iy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
          if (ix > 4 && iy > 4) malos.push('encima:' + A.className.toString().split(' ')[0] + '/' + B.className.toString().split(' ')[0] + '+' + Math.round(iy));
        }
      }
      out.push((i + 1) + ';' + act.dataset.sliderId + ';' + malos.length + ';' + malos.slice(0, 3).join(',') + (desplaza ? ' [desplaza ' + (zona.scrollHeight - zona.clientHeight) + 'px]' : ''));
      i += 1; uno();
    }, 400);
  }
  uno();
}, 3500); };
</script>"""

malas = []
for (w, h) in VIEWS:
    for mod in MODS:
        p = os.path.join(DST, '_solapes.html')
        io.open(p, 'w', encoding='utf-8').write(BRIDGE % {'mod': mod, 'w': w, 'h': h})
        args = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                '--virtual-time-budget=40000', '--window-size=%d,%d' % (max(w, 560), h + 40), '--dump-dom', BASE + '_solapes.html']
        if w < 600:
            args.insert(2, UA)
        r = subprocess.run(args, capture_output=True, timeout=240)
        os.remove(p)
        m = re.search(r'<title>R\|(.*?)</title>', r.stdout.decode('utf-8', 'ignore'), re.S)
        if not m:
            print('%dx%d %s: sin resultado' % (w, h, mod)); continue
        for fila in m.group(1).split('|'):
            n, sid, nmal, quien = (fila.split(';') + [''] * 4)[:4]
            if nmal != '0':
                malas.append((w, h, mod, sid, nmal, quien))
            elif 'desplaza' in quien:
                print('  (desplazable) %dx%d %s %s %s' % (w, h, mod, sid, quien.strip()))

if malas:
    print('PANTALLAS CON CONTENIDO TAPADO: %d' % len(malas))
    for x in malas:
        print('  %dx%d %-8s %-9s %s elem  %s' % x)
else:
    print('Ningun contenido queda tapado por la cabecera ni por el pie.')
