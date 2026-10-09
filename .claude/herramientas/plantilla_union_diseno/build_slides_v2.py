# -*- coding: utf-8 -*-
"""Genera los sliders de antioquia_induccion_sst_nuevo a partir del contenido
de antioquia-gold-nuevo, con el formato de la estructura de gases_caribe:
modulos/moduloN/sliders/sliderN/sliderN.{html,css,js} + MODULE_CONFIGS."""
import io, os, re, json, sys

SRC = r"C:\Users\USUARIO\AppData\Local\Temp\claude\c--wamp64-www-amatia-sofactia-cursos-2026\d7be2f0f-4269-4762-bd81-2ccf1b7f4103\scratchpad\fuente\course_content\plantillas\antioquia-gold-nuevo"
DST = r"C:\wamp64\www\amatia\sofactia_cursos_2026\course_content\plantillas\antioquia_induccion_sst_nuevo_v2"

html = io.open(os.path.join(SRC, 'index.html'), encoding='utf-8').read()


def bloque_section(texto, inicio):
    """Devuelve la <section> completa que empieza en `inicio`, respetando anidamiento."""
    pos, depth = inicio, 0
    for m in re.finditer(r'<section\b|</section>', texto[inicio:]):
        if m.group(0) == '</section>':
            depth -= 1
            if depth == 0:
                return texto[inicio:inicio + m.end()]
        else:
            depth += 1
    raise ValueError('section sin cerrar')


def pantalla(nombre):
    m = re.search(r'<section\b[^>]*data-screen="%s"[^>]*>' % re.escape(nombre), html)
    return bloque_section(html, m.start())


def quitar(frag, patron):
    return re.sub(patron, '', frag, flags=re.S)


def rutas_assets(frag):
    frag = re.sub(r'(["\'(])\.?/?assets/([^"\')\s]+?\.mp3)', r'\1../../assets/audio/\2', frag)
    frag = re.sub(r'(["\'(])\.?/?assets/(?!audio/)([^"\')\s]+)', r'\1../../assets/img/\2', frag)
    return frag



def conectar_navegacion(frag):
    """Los botones propios de cada pantalla pasan a mover la estructura del curso:
    data-ag-prev / data-ag-next llaman a prevSection()/nextSection() (que llevan el
    seguimiento y el paso al siguiente modulo) y data-ag-ruta vuelve a la ruta.
    EL ORDEN IMPORTA: primero los botones de avance/cierre, al final los de volver.
    Si "volver a la ruta" se aplica antes, el boton de cierre de un modulo salta a
    la ruta sin completarlo y el modulo siguiente queda bloqueado."""
    # 1. cierre de leccion ("Siguiente leccion" / "Volver a lecciones" final)
    frag = re.sub(r'\sdata-go="m[0-9]-[a-z-]+"\s+data-lesson-done="\d+"', ' data-ag-next', frag)
    frag = re.sub(r'\sdata-lesson-done="\d+"', '', frag)
    # 2. pie de Momento 0: el principal avanza, el secundario retrocede
    frag = re.sub(r'(class="primary-action"[^>]*?)\sdata-go="[^"]*"', r'\1 data-ag-next', frag)
    frag = re.sub(r'(class="back-button"[^>]*?)\sdata-go="[^"]*"', r'\1 data-ag-prev', frag)
    # 3. pie de las lecciones
    frag = re.sub(r'\sdata-prev(?=[\s>])', ' data-ag-prev', frag)
    frag = re.sub(r'\sdata-next(?=[\s>])', ' data-ag-next', frag)
    # 4. lo que queda son enlaces de volver
    frag = re.sub(r'\sdata-go="(?:cover|m0-ruta)"', ' data-ag-ruta', frag)
    return frag

def sin_hidden(etiqueta_abre):
    return re.sub(r'\s+hidden(?=[\s>])', '', etiqueta_abre, count=1)


def texto_plano(s):
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def titulo(frag):
    for tag in ('h1', 'h2'):
        m = re.search(r'<%s\b[^>]*>(.*?)</%s>' % (tag, tag), frag, re.S)
        if m:
            return texto_plano(m.group(1)).rstrip('.')
    return 'Pantalla'


def escribir_slider(modulo, n, cuerpo, clave):
    carpeta = os.path.join(DST, 'modulos', modulo, 'sliders', 'slider%d' % n)
    os.makedirs(carpeta, exist_ok=True)
    io.open(os.path.join(carpeta, 'slider%d.html' % n), 'w', encoding='utf-8').write(
        '<section class="module-slide ag-slide" data-ag="%s">\n%s\n</section>\n' % (clave, cuerpo))
    io.open(os.path.join(carpeta, 'slider%d.css' % n), 'w', encoding='utf-8').write(
        '/* %s · slider%d\n   El diseño vive en plugins/css/antioquia-theme.css (compartido).\n'
        '   Aqui solo van ajustes propios de esta pantalla, si hicieran falta. */\n' % (modulo, n))
    io.open(os.path.join(carpeta, 'slider%d.js' % n), 'w', encoding='utf-8').write(
        "(function () {\n"
        "    window.initSlider%d = function () {\n"
        "        var root = document.querySelector('[data-ag=\"%s\"]');\n"
        "        if (root && window.AG) window.AG.init(root);\n"
        "    };\n"
        "    if (document.readyState !== 'loading') window.initSlider%d();\n"
        "})();\n" % (n, clave, n))


config = {}

# ----------------------------------------------------------------------------
# MODULO 0 — Momento 0 (la pantalla de ruta la sustituye inicio/inicio.html)
# ----------------------------------------------------------------------------
m0 = ['m0-bienvenida', 'm0-reflexion', 'm0-acuerdos', 'm0-cero-eventos']
slides = []
for i, nombre in enumerate(m0, 1):
    sec = pantalla(nombre)
    abre = re.match(r'<section\b[^>]*>', sec).group(0)
    sec = sin_hidden(abre) + sec[len(abre):]
    sec = conectar_navegacion(rutas_assets(sec))
    escribir_slider('modulo0', i, sec, 'm0-s%d' % i)
    slides.append({'id': 'slider%d' % i, 'path': './sliders/slider%d/slider%d.html' % (i, i), 'title': titulo(sec)})
config['modulo0'] = {'orden': 0, 'subtitle': 'Bienvenida y acuerdos al entrar.', 'title': 'Introducción', 'image': '../assets/img/trabajdores_comunicacion.webp',
                     'time': '3 min', 'slides': slides}

# ----------------------------------------------------------------------------
# MODULOS 1-3 — cada paso de la leccion es un slider
# ----------------------------------------------------------------------------
SUBT = {'modulo1': 'Lo que te protege cada dia.', 'modulo2': 'Peligros y como prevenirlos.', 'modulo3': 'Que hacer si algo pasa.'}

LECCIONES = [
    ('modulo1', 'm1-sig', 'Nuestro SIG para tu protección', '../assets/img/colaboradoresUno.webp', '4 min'),
    ('modulo2', 'm2-riesgos', 'Nuestros riesgos y formas de prevenirlos', '../assets/img/hombre_mascara.webp', '5 min'),
    ('modulo3', 'm3-reportes', 'Cómo reportar accidentes y manejo de emergencias', '../assets/img/trabajadores_cuerda.webp', '4 min'),
]

for orden, (modulo, pantalla_id, tit, img, tiempo) in enumerate(LECCIONES, 1):
    raiz = pantalla(pantalla_id)
    abre_raiz = re.match(r'<section\b[^>]*>', raiz).group(0)
    abre_raiz = sin_hidden(abre_raiz)
    aria = re.search(r'aria-label="([^"]*)"', abre_raiz)

    pasos = [bloque_section(raiz, m.start()) for m in re.finditer(r'<section class="lesson-screen[^"]*" data-step="\d+"', raiz)]

    # modales que viven entre pasos (el de clasificacion de peligros de la leccion 1)
    extras = {}
    for m in re.finditer(r'<div class="hazard-modal"[^>]*>', raiz):
        ini = m.start()
        depth, j = 0, ini
        for t in re.finditer(r'<div\b|</div>', raiz[ini:]):
            depth += 1 if t.group(0) != '</div>' else -1
            if depth == 0:
                j = ini + t.end()
                break
        modal = raiz[ini:j]
        # se asocia al paso inmediatamente anterior
        previo = max(k for k, p in enumerate(pasos) if raiz.index(p) < ini)
        extras.setdefault(previo, []).append(modal)

    slides = []
    for k, paso in enumerate(pasos):
        abre = re.match(r'<section\b[^>]*>', paso).group(0)
        paso = sin_hidden(abre) + paso[len(abre):]
        extra = '\n'.join(extras.get(k, []))
        cuerpo = ('%s\n  <div class="m1-sig-root">\n%s\n%s\n  </div>\n</section>'
                  % (abre_raiz, paso, extra))
        cuerpo = conectar_navegacion(rutas_assets(cuerpo))
        n = k + 1
        escribir_slider(modulo, n, cuerpo, '%s-s%d' % (pantalla_id, n))
        slides.append({'id': 'slider%d' % n, 'path': './sliders/slider%d/slider%d.html' % (n, n), 'title': titulo(paso)})

    config[modulo] = {'orden': orden, 'subtitle': SUBT[modulo], 'title': tit, 'image': img, 'time': tiempo, 'slides': slides}

# ----------------------------------------------------------------------------
# Configuracion: modulos.json y sus 5 copias en linea
# ----------------------------------------------------------------------------
js = json.dumps(config, ensure_ascii=False, indent=2)
io.open(os.path.join(DST, 'modulos.json'), 'w', encoding='utf-8').write(js + '\n')

copias = 0
for rel in ['inicio/inicio.html'] + ['modulos/modulo%d/modulo%d.html' % (i, i) for i in range(4)]:
    p = os.path.join(DST, rel)
    s = io.open(p, encoding='utf-8').read()
    ini = s.index('window.MODULE_CONFIGS = {')
    fin = s.index('};', ini) + 2
    s = s[:ini] + 'window.MODULE_CONFIGS = ' + js + ';' + s[fin:]
    io.open(p, 'w', encoding='utf-8').write(s)
    copias += 1

print('MODULE_CONFIGS actualizado en modulos.json y en %d paginas' % copias)
for k, v in config.items():
    print('%s  "%s"  %s  (%d sliders)' % (k, v['title'], v['time'], len(v['slides'])))
    for s in v['slides']:
        print('    %-9s %s' % (s['id'], s['title']))
