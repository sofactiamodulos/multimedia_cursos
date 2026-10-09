"""Convierte el styles.css de antioquia-gold-nuevo en un tema acotado a .ag-slide.

Cada selector S pasa a `.ag-slide :is(S)`. Con :is() el selector original se
evalua completo contra el documento, asi que reglas como
`[data-lesson] .is-green .next-btn` siguen funcionando cuando el marcado
original vive intacto dentro del envoltorio, y no alcanzan nada de fuera.
"""
import re, sys, io

SCOPE = '.ag-slide'


def strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def split_top(s, sep=','):
    """Divide por comas de primer nivel (respeta parentesis y corchetes)."""
    out, depth, cur = [], 0, []
    for ch in s:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        if ch == sep and depth == 0:
            out.append(''.join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append(''.join(cur))
    return [x.strip() for x in out if x.strip()]


def blocks(css):
    """[(cabecera, cuerpo)] de primer nivel."""
    i, n, res = 0, len(css), []
    while i < n:
        j = css.find('{', i)
        if j < 0:
            break
        head = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == '{':
                depth += 1
            elif css[k] == '}':
                depth -= 1
            k += 1
        res.append((head, css[j + 1:k - 1]))
        i = k
    return res


# Selectores de la pagina original que no existen dentro de un slider
DESCARTAR = ('html', 'body', '.topbar', 'body.is-lessons-open .topbar', '.brand-link img')


def scope_selector(sel):
    sel = sel.strip()
    if sel in ('html', 'body') or sel.startswith('body') or sel.startswith('.topbar') or sel.startswith('.brand-link'):
        return None
    if sel == ':root':
        return SCOPE
    pseudo = ''
    m = re.search(r'::[a-zA-Z-]+(\([^)]*\))?$', sel)
    if m:
        pseudo = sel[m.start():]
        sel = sel[:m.start()]
    if sel == '*':
        return '%s, %s *' % (SCOPE, SCOPE) if not pseudo else '%s *%s' % (SCOPE, pseudo)
    return '%s :is(%s)%s' % (SCOPE, sel, pseudo)


def a_contenedor(head):
    """@media que solo mira ancho/alto -> @container ag. Dentro de la estructura
    del curso el slider no ocupa la ventana: ocupa la zona entre cabecera y pie,
    y es esa zona la que tiene que decidir cuando compactar."""
    if not head.startswith('@media'):
        return head
    cond = head[len('@media'):].strip()
    feats = re.findall(r'\(\s*([a-z-]+)\s*:', cond)
    if feats and all(f in ('max-width', 'min-width', 'max-height', 'min-height') for f in feats):
        return '@container ag ' + cond
    return head


def transform(css, indent=''):
    out = []
    for head, body in blocks(css):
        if head.startswith('@media') or head.startswith('@supports') or head.startswith('@container'):
            inner = transform(body, indent + '  ')
            if inner.strip():
                out.append('%s%s {\n%s%s}\n' % (indent, a_contenedor(head), inner, indent))
        elif head.startswith('@keyframes') or head.startswith('@font-face'):
            out.append('%s%s {%s}\n' % (indent, head, body))
        elif head.startswith('@'):
            continue
        else:
            sels = [scope_selector(s) for s in split_top(head)]
            sels = [s for s in sels if s]
            decl = body.strip()
            if not sels or not decl:
                continue
            out.append('%s%s {\n%s  %s\n%s}\n' % (indent, (',\n' + indent).join(sels), indent,
                                                  re.sub(r'\s*\n\s*', '\n' + indent + '  ', decl), indent))
    return ''.join(out)


if __name__ == '__main__':
    src = io.open(sys.argv[1], encoding='utf-8').read()
    res = transform(strip_comments(src))
    cab = ('/* =========================================================\n'
           '   TEMA ANTIOQUIA GOLD — contenido de los sliders\n'
           '   Generado desde plantillas/antioquia-gold-nuevo/styles.css.\n'
           '   Cada regla va acotada a .ag-slide: no alcanza la estructura\n'
           '   del curso (cabecera, menu, navegacion) ni a Bootstrap.\n'
           '   ========================================================= */\n\n')
    io.open(sys.argv[2], 'w', encoding='utf-8').write(cab + res)
    print('reglas de entrada: %d llaves · salida: %d lineas' % (src.count('{'), res.count('\n')))
    print('llaves balanceadas:', res.count('{') == res.count('}'))
