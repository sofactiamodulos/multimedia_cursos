---
description: Aplica grid real de Bootstrap 5 + tokens de color + video fluido + traducciones 100% manuales (sin API) + medios listos para Bunny, sobre un curso "generación A" ya creado con /crear-curso.
---

# /redisenar-curso-bootstrap

Aplica, sobre un curso "generación A" (`index.php`/`modulo.php`/`quiz.php`, ver §9 del manual)
**ya creado en disco y registrado en BD por `/crear-curso`**, cuatro convenciones de diseño e
i18n que no vienen por defecto en las plantillas antiguas de este repo. No crea cursos, no toca la
base de datos, no reemplaza a `/crear-curso` — se ejecuta después.

Contexto obligatorio: `.claude/manual_desarrollo.md` (§9 anatomía de `course_content`, §10
plantillas). Casos reales de referencia en este repo (léelos con `git show development:<ruta>`,
**nunca hagas checkout** de esa rama):
- Grid + tokens de color + video fluido: `development:course_content/cursos/aris_seguridad_vial_2026/modulos/modulo1/sliders/slider1/slider1.php`
  y `development:course_content/cursos/aris_seguridad_vial_2026/modulos/modulo0/modulo0.css`.
- Traducción 100% manual/offline (mismo script, sin backend de traducción):
  `development:course_content/antioquia_gold/induccion_sst_scorm/plugins/js/dom-translator.js`
  y `plugins/js/translations-en.js`.
- Caso ya aplicado en este repo, para copiar el patrón exacto:
  `course_content/arissegovia/induccion_visitantes_segovia_2026/` (grid, `plugins/css/variables.css`,
  `plugins/js/translations-en.js`, `locales/media.json`, `locales/audio-bunny-checklist.md`).

## Entrada

```text
/redisenar-curso-bootstrap
curso: <ruta bajo course_content/, ej. arissegovia/induccion_visitantes_segovia_2026>
```

El curso destino debe existir ya en disco (copiado por `/crear-curso`). Si no existe, para y pide
correrlo primero.

## Procedimiento

### 1. Grid y colores
- No agregues Bootstrap: en los cursos "generación A" de este repo ya está cargado
  (`assets/bootstrap/css/*`, ver `<head>` de `modulo.php`) pero sin usarse — solo hace falta usar
  sus clases.
- Detecta las clases de layout no-Bootstrap con `grep -n 'class="col-[0-9]\|col-inline\|bg-[a-z]*' modulo.php`
  y reemplázalas por `container-fluid`/`row`/`col-12 col-lg-N` (mobile-first: **siempre** con
  `col-12` como base — sin él, un `col-3`/`col-9`/`col-lg-3` de Bootstrap se queda angosto también
  en el celular, que es el bug real detrás de "no se ve bien el responsive"). No toques las clases
  de color/spacing (`bg-blanco`, `bg-petroleo`, `top-slide-10`, etc.) — solo las de ancho/columna.
- Crea `plugins/css/variables.css` con un bloque `:root` reusando las variables que ya existan en
  `assets/css/style.css` (no inventes una paleta nueva) más un token nuevo por cada color
  repetido >5 veces como hex crudo (`grep -c '#hexvalor' assets/css/style.css`) que no tenga ya
  variable — usa un nombre descriptivo del color, no genérico (`--petroleo`, no `--color1`).
  Enlázalo en el `<head>` de las 5 páginas, **antes** de `assets/css/style.css`.

### 2. Video (si el curso tiene videos de Bunny/mediadelivery)
- En `plugins/css/variables.css`:
  `.sf-video-player{width:100%;aspect-ratio:...}` con dos variantes `.sf-video-horizontal`
  (16/9) y `.sf-video-vertical` (9/16, `max-width:430px`) — nunca un `max-width` fijo en la
  tarjeta completa, eso es lo que hace que se vea chico en pantallas anchas.
- Si el curso ya carga el iframe de Bunny directo (sin overlay/portada custom encima), no
  reintroduzcas ningún componente de "click para reproducir" — eso se decide aparte, no es parte
  de este comando.

### 3. Traducciones 100% manuales (sin API)
- Copia tal cual, sin editar una sola línea: `plugins/js/dom-translator.js` y
  `plugins/js/language-switcher.js` desde cualquiera de los cursos "en vivo" ya migrados
  (`development:course_content/cursos/aris_seguridad_vial_2026/plugins/js/`).
- **No crees `translate.php`** en el curso. En el `<script>` de `dom-translator.js` deja
  `data-endpoint="translate.php"` **tal cual, aunque el archivo no exista** — es un detalle no
  obvio del script: `courseBase` se calcula recortando literalmente la substring `translate.php`
  del valor de `data-endpoint` (`endpoint.replace(/translate\.php.*$/, '')`), así que cualquier
  otro nombre (`"offline.php"`, `"ninguno.php"`) rompe el cálculo de la ruta relativa y
  `locales/media.json` deja de cargar. Tampoco uses `data-endpoint="offline"` ni ningún valor sin
  `.php`: eso activa el modo `OFFLINE` del script, que también desactiva la carga de
  `locales/media.json` — y ese archivo sí debe cargar (es JSON propio del curso, no la API).
- Extrae **todo** el texto visible de las 5 páginas ya reescritas (h1-h6, p, span, li, button,
  `alt`, `aria-label`, `title`) a `plugins/js/translations-en.js` (`window.TX_EN = {...}`),
  traducido a mano. No copies el diccionario de otro curso — el texto es distinto.
- Verifica cobertura antes de dar por terminado (ejemplo de chequeo con Node, ajusta rutas):
  ```js
  global.window = {}; require('./plugins/js/translations-en.js');
  // extraer texto entre `>...<` de cada .php, normalizar espacios, comparar contra Object.keys(window.TX_EN)
  ```
  Los únicos "faltantes" esperables son texto dentro de `<script>`/`<style>` (dom-translator.js
  los ignora igual) y cualquier bloque marcado `data-no-translate`.

### 4. Medios listos para Bunny (imágenes con texto, audio, video)
- Marca con `data-i18n-media="clave"` el tag real (`<img>`, `<audio>`, `<video>` o `<iframe>` —
  **nunca** un `<div>` que lo envuelva, `dom-translator.js` solo mira `el.tagName`) y registra la
  clave en `locales/media.json`: `{"clave": {"es": "ruta-o-url"}}` (agrega `"en"` solo si ya existe
  esa versión; si falta, el script cae a `"es"` solo).
- Si algún audio se dispara hoy desde un `<div data-audio="...">` (patrón viejo, no es un tag real
  de audio), reestructúralo a un `<audio data-i18n-media="..."><source></audio>` real dentro del
  disparador, y ajusta el JS que lo consumía para leer `elemento.querySelector('audio source')` en
  vez del atributo `data-audio` — es el único cambio de comportamiento JS que este comando permite.
- Genera un checklist `.md` en `locales/` con cada clave de audio/video que no tenga `"en"` todavía
  y su ruta local actual, para que el cliente pegue ahí las URLs de Bunny cuando las tenga. **No
  inventes URLs de Bunny.**

### 5. Verificar
- `php7.4.33 -l` (y de ser posible una versión moderna) en las 5 páginas y cualquier `.js` tocado.
- Cobertura de `TX_EN` (paso 3) y de `media.json` (cada `data-i18n-media` del HTML tiene su
  entrada, `grep -o 'data-i18n-media="[^"]*"' *.php | sort -u` vs. las claves del JSON).
- Confirmar con `ls translate.php` que **no existe** ese archivo en el curso.
- Si hay acceso local a la base, curso abre sin warnings de PHP con un `course_code` válido.

## Entrega

Resume: qué clases de layout se reemplazaron (con conteo), qué tokens de color se agregaron, si
había video y qué patrón se aplicó, cuántas entradas tiene `TX_EN` y si la cobertura dio 100%,
cuántas claves de medios quedaron pendientes de URL de Bunny (y dónde quedó el checklist), y
cualquier decisión tomada por defecto para que el usuario pueda corregirla.

## Prohibido

- Crear `translate.php` o cualquier endpoint de traducción en vivo.
- Usar `data-endpoint` con un valor que no contenga literalmente `translate.php` (rompe el cálculo
  de ruta relativa de `dom-translator.js`) o que no termine en `.php` (activa `OFFLINE` y desactiva
  `locales/media.json`).
- Inventar URLs de Bunny.
- Migrar la arquitectura de un curso "generación A" a `modulos/sliders/` (generación B).
- Tocar la carpeta de la plantilla original ni crear/registrar cursos (eso es trabajo de `/crear-curso`).
