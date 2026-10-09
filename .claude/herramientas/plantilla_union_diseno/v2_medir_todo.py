"""Recorre todos los sliders de cada modulo dentro de la estructura real y mide:
desborde vertical de la zona, contenido recortado y desborde horizontal."""
import io, os, re, subprocess, sys

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8767/"
DST = r"C:\wamp64\www\amatia\sofactia_cursos_2026\course_content\plantillas\antioquia_induccion_sst_nuevo_v2"
VIEWS = [(int(v.split('x')[0]), int(v.split('x')[1])) for v in (sys.argv[1:] or ['1440x900', '1366x768'])]
MODS = ['modulo0', 'modulo1', 'modulo2', 'modulo3']

BRIDGE = """<!doctype html><meta charset=utf-8><title>x</title>
<style>html,body{margin:0}iframe{border:0;display:block}</style>
<script>try{localStorage.setItem('equsera_%(mod)s_slider_index','0')}catch(e){}</script>
<iframe id=f src="modulos/%(mod)s/%(mod)s.html" width=%(w)d height=%(h)d></iframe>
<script>
f.onload = function () {
  setTimeout(function () {
    var d = f.contentDocument, w = f.contentWindow, out = [];
    var st = d.createElement('style'); st.textContent = '*,*::before,*::after{animation:none!important;transition:none!important}'; d.head.appendChild(st);
    var secs = d.querySelectorAll('.content-section');
    var i = 0;
    function uno() {
      if (i >= secs.length) { document.title = 'R|' + out.join('|'); return; }
      if (w.capsuleManager) w.capsuleManager.showSection(i);
      else { secs.forEach(function (s, k) { s.classList.toggle('active', k === i); }); }
      setTimeout(function () {
        var act = d.querySelector('.content-section.active');
        var zona = d.querySelector('.module-content-scroll');
        var zr = zona.getBoundingClientRect();
        var recortes = [];
        act.querySelectorAll('.ag-slide *').forEach(function (e) {
          if (!e.getClientRects().length) return;
          var cs = w.getComputedStyle(e);
          if (cs.position === 'fixed' || cs.visibility === 'hidden') return;
          if (e.closest('[hidden]') || e.closest('[data-hazard-modal]')) return;
          var r = e.getBoundingClientRect();
          if (r.height < 4 || r.width < 4) return;
          if (r.bottom > zr.bottom + 2 || r.right > zr.right + 2) {
            var cn = (typeof e.className === 'string' && e.className) ? '.' + e.className.trim().split(/\\s+/)[0] : '';
            recortes.push(e.tagName.toLowerCase() + cn + '+' + Math.round(Math.max(r.bottom - zr.bottom, r.right - zr.right)));
          }
        });
        out.push((i + 1) + ';' + act.dataset.sliderId + ';' + Math.round(zona.scrollHeight - zona.clientHeight) + ';' +
                 recortes.length + ';' + recortes.slice(0, 3).join(','));
        i += 1;
        uno();
      }, 450);
    }
    uno();
  }, 3500);
};
</script>"""

malas = []
for (w, h) in VIEWS:
    for mod in MODS:
        p = os.path.join(DST, '_medir.html')
        io.open(p, 'w', encoding='utf-8').write(BRIDGE % {'mod': mod, 'w': w, 'h': h})
        ua = ['--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'] if w < 600 else []
        r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1'] + ua + [
                            '--virtual-time-budget=40000', '--window-size=%d,%d' % (max(w, 560), h + 40), '--dump-dom', BASE + '_medir.html'],
                           capture_output=True, timeout=240)
        os.remove(p)
        m = re.search(r'<title>R\|(.*?)</title>', r.stdout.decode('utf-8', 'ignore'), re.S)
        if not m:
            print('%dx%d %s: sin resultado' % (w, h, mod))
            continue
        for fila in m.group(1).split('|'):
            n, sid, scroll, nrec, quien = (fila.split(';') + [''] * 5)[:5]
            ok = int(scroll) <= 2 and nrec == '0'
            if not ok:
                malas.append((w, h, mod, sid, scroll, nrec, quien))
            print('%4dx%-4d %-8s %-9s scroll=%-4s recortes=%-3s %s' % (w, h, mod, sid, scroll, nrec, '' if ok else quien))

print()
if malas:
    print('PANTALLAS CON PROBLEMAS: %d' % len(malas))
    for x in malas:
        print('  %dx%d %s %s  scroll=%s recortes=%s  %s' % x)
else:
    print('Todas las pantallas caben, sin scroll ni recortes.')
