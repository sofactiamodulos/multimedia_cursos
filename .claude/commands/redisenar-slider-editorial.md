---
description: Aplica el rediseño editorial de header compacto + contenido de slide (eyebrow dorado, headline con acento, foto circular con anillo, sin barra de progreso) sobre un módulo "generación B" (modulos/moduloN/sliders/sliderN). Úsalo para redisenar otro módulo/curso con el mismo lenguaje visual sin tener que reexplicarlo.
---

# /redisenar-slider-editorial

Aplica, sobre un módulo de un curso "generación B" (`modulos/<modulo>/index.html` +
`sliders/sliderN/sliderN.{html,css,js}`, framework EQUSERA — ver `.claude/manual_desarrollo.md`
§ "Contrato de una página de curso (generación B)"), el lenguaje visual editorial ya validado con
el cliente en `course_content/arissegovia/induccion_visitantes_segovia_2026/modulos/introduccion/`
(referencia visual original: headers de los cursos "gases del caribe" / "antioquia gold", mismo
framework, otra piel — léelos con `git show courses/gases_caribe/induccion_contratista_sst:...` /
`git show courses/antioquia_gold/induccion_sst:...`, **nunca hagas checkout** de esas ramas; si
necesitas verlos renderizados, `git archive <rama> -- course_content/<empresa> | tar -x -C
<carpeta fuera del repo servida por WAMP>`, mira, y borra la carpeta al terminar).

No crea módulos ni toca la base de datos. Se aplica módulo por módulo, sobre uno que ya existe.

## Entrada

```text
/redisenar-slider-editorial
curso: <ruta bajo course_content/, ej. arissegovia/induccion_visitantes_segovia_2026>
modulo: <carpeta bajo modulos/, ej. introduccion>
contenido: [opcional] ruta a un modulo.php/index.php "generación A" del que portar contenido
           literal a los sliders (ver paso 4) — si no se da, se mantiene el contenido actual y
           solo se aplica el estilo.
```

## Antes de tocar nada

1. **Ubica los scripts realmente cargados**, no asumas la carpeta. Este tipo de curso suele tener
   `plugins/js/*` y `plugins-html/js/*` a la vez — son copias que **divergen** (una queda stale).
   ```bash
   grep -n 'interactividad.js\|main.js\|module-config.js' modulos/<modulo>/index.html
   ```
   Edita **solo** la copia que ese `<script src>` referencia. La otra no se toca aunque exista.
2. **`MODULE_CONFIGS` vive embebido e inline, duplicado por página** (`modulos/<cada-modulo>/index.html`
   y a veces `ruta_de_aprendizaje/index.html`), no en un único archivo — aunque un comentario cercano
   diga que la fuente única es `modulos.json`, verifícalo (`grep -rln 'modulos.json' ...`, y si ningún
   `.php`/`.js` lo hace `fetch`, es un archivo muerto, no lo edites como si fuera la fuente real).
   **Solo edita la copia embebida en el `index.html` del módulo que estás rediseñando** — las
   páginas hermanas (otros módulos, el dashboard) solo leen `orden`/`title`/`image`/`time`/`entry`/
   `trackPrefix`/`isEvaluation` de los módulos *ajenos*, nunca el `.slides[]` ajeno, así que no hace
   falta replicar un cambio de slides en las demás copias.
3. Confirma con un `curl -s -o /dev/null -w '%{http_code}'` que el curso responde en local (WAMP)
   antes de empezar, para poder verificar con capturas reales al final (ver paso 6).

## Procedimiento

### 1. Header (una sola vez por curso, no por módulo)

El CSS del header vive en **un solo archivo compartido** por los módulos de un mismo curso
(`plugins/css/styles.css`, clase `.module-header` y vecinas) — tocarlo afecta a todos los módulos
que compartan esa plantilla (no a `evaluacion1` si usa un layout de cierre distinto; confirma con
`grep -c 'class="module-header"' modulos/*/index.html`, un 0 = no comparte esta plantilla). Si el
header de este curso **ya sigue este contrato**, no toques nada de esta sección.

Contrato final (todo en `plugins/css/styles.css`):
- `.module-header`: `display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap;
  padding:10px 20px 11px; position:relative;` — una sola línea: `.module-header-top` (volver +
  nombre del slide) a la izquierda, `.module-progress-card` (contador + acceso directo) a la derecha.
- `.module-title` = **nombre del slide activo**, no el nombre del módulo. Ya viene resuelto por
  `CapsuleManager.updateSlideTitle()` en `interactividad.js` (lee `section.dataset.slideTitle`, que
  sale de `MODULE_CONFIGS[...].slides[i].title`) — solo hay que darle estilo de eyebrow chico:
  `text-transform:uppercase; font-size:.76rem; font-weight:800; color:var(--color-dark);`.
- `.module-meta` ("Módulo N | Tiempo estimado"): `display:none`. Es información del módulo completo,
  no de la pantalla activa; sobra repetida en cada slide y no está en la referencia.
- `.mp-percent` ("X% completado"): `display:none`. **Sin porcentaje visible, nunca** — decisión
  explícita del cliente en más de una vuelta de feedback, no lo reintroduzcas "por consistencia".
- Línea de progreso real: **no es un elemento decorativo nuevo**, es `.module-progress-track` +
  `.module-progress-fill` que ya existen en el HTML y que `CapsuleManager.updateProgress()` ya
  actualiza (`this.progressBar.style.width = pct + '%'`) — solo hay que reposicionarlos y
  redimensionarlos, no ocultarlos ni duplicar la lógica:
  ```css
  .module-progress-track{position:absolute;left:20px;right:20px;bottom:0;height:3px;
    background:var(--sf-border);}
  .module-progress-fill{height:100%;background:var(--sf-gold);}
  ```
- `.mp-screen`: texto corto **"Pantalla X de Y"**, no "En la pantalla X de Y" — si el JS todavía
  arma la frase larga, edita el template string en `interactividad.js` (`updateIndicator()`).
- Accesos directos, **dos mecanismos, uno por tamaño de pantalla, no los dos a la vez**:
  - Escritorio: `.section-indicator`/`.screen-step` (ya existen, reactívalos si están en
    `display:none`) como puntos **chicos** — `width/height:17px`, borde 1.5px, sin el tamaño
    original de 25px. Si el módulo tiene muchos slides, no dejes que ensanchen el header:
    `.section-indicator{max-width:150px;overflow-x:auto;}`.
  - Móvil: `.module-screens-btn` (ícono que abre el modal "Ir a pantalla" con buscador,
    `CapsuleManager.openScreensMenu()`) — **mobile-only a propósito**
    (`display:none` por defecto, `.is-mobile-device .module-screens-btn{display:flex}`). No lo
    muestres en escritorio: ya está cubierto por los puntos, y mostrar los dos juntos fue feedback
    negativo del cliente.
- **Centrado vertical del slide activo** (feedback del cliente: "más centrado, no hacia arriba", y
  "si hay scroll que se vea bien"): reglas en `plugins/css/styles.css` justo debajo de
  `.module-content-scroll .sf-app` — cadena flex (`.module-content-scroll` → `.sf-app` /
  `#sliders-container` → `.content-section.active`) y `margin-block:auto` sobre
  `.content-section.active > .module-slide`, más `padding-block:12px 24px` para que con scroll no
  quede pegado al header ni al nav. Usa `margin-block:auto`, **no** `justify-content:center` (este
  último recorta el tope de un contenido más alto que el área y no se puede scrollear hasta ahí).
  Van scopeadas con `body:not(.lesson-cover-active) .route-main.module-page:not(.cover-mode)` para
  no tocar las portadas a pantalla completa. Si `.sf-app` queda más angosto que el slide, es su
  `margin:0 auto` dentro de un contenedor flex — ya se corrige con `width:100%`.
- `.module-nav-footer`/`.module-nav-btn`: enlaces de texto plano, no botones rellenos —
  `background:transparent; border:none;`. El texto del botón "siguiente" lo arma
  `CapsuleManager.updateGlobalNav()` en JS (no el HTML estático, que se sobreescribe al cargar):
  usa **"Continuar"**, no "Siguiente" (el id del botón en el HTML ya es `btn-continue`, es la grafía
  correcta). Deja intactas las variantes de último slide ("Siguiente módulo" / "Ir a inicio").

### 2. Componentes de contenido reutilizables (no los reinventes)

Antes de escribir CSS nuevo para un slide, revisa si ya existe algo global en `plugins/css/styles.css`:
- `.audio-card` / `.audio-card--light`: tarjeta con el `<audio controls>` **nativo** del navegador
  estilizado — rápido de usar, pero el control nativo no combina con este lenguaje visual editorial.
- **Reproductor de audio custom con onda animada** (pedido explícito del cliente, con referencia
  puntual: "usa el mismo diseño que `antioquia_gold/.../modulos/introduccion/sliders/slider2`,
  clases `.audio-player`"), ya migrado a este curso en
  `modulos/introduccion/sliders/slider3/{slider3.html,slider3.css,slider3.js}` — cópialo de ahí en
  vez de rehacerlo (**no** reuses los nombres de clase bare `audio-player`/`audio-play`, ya
  significan otra cosa en `plugins/css/styles.css` — usa el prefijo `sliderN-`). Es un botón
  circular de play/pausa (triángulo que se convierte en dos barras via `.is-playing`, sin SVG,
  solo `border`) + un visualizador de ~28 barras (`<i>` con alturas por `nth-child`) que se
  "encienden" en `var(--sf-gold)` progresivamente según `currentTime/duration` (no una barra de
  progreso plana ni un `<input type="range">`), + el tiempo `cur / dur` como texto simple debajo.
  En pantallas angostas se ocultan las últimas barras (`nth-child(n+19){display:none}`) y el JS
  calcula el ratio solo sobre las visibles (`matchMedia('(max-width:767px)')`), igual que el
  original. La lógica (`pintaOnda`/`pintaTiempo`, sobre `timeupdate`/`pause`/`ended`) vive en
  `initSliderN()`, que `main.js` ya llama solo al entrar a ese slide.
  Fue una segunda iteración: la primera versión (más simple, con `<input type="range">`) se hizo
  copiando el patrón de "gases del caribe" antes de que el cliente señalara esta referencia
  puntual — si en otro curso el cliente no da una referencia exacta, confirma cuál de las dos
  quiere en vez de asumir.
  **Bug ya resuelto, no lo reintroduzcas:** si el `<audio>` usa `preload="metadata"`, el evento
  `loadedmetadata` puede disparar *antes* de que `initSliderN()` alcance a hacer el
  `addEventListener` (el elemento ya estaba en el DOM), y la duración se queda en "0:00"/"--:--"
  para siempre — hay que chequear `audio.readyState >= 1` justo después de enlazar y pintar la
  duración ahí también si ya está disponible.
- **Al mover assets entre carpetas de slider (paso 4 más abajo), revisa el resultado con un
  listado de archivos, no solo con el `mv`.** Ya pasó una vez en este módulo: tras mover los
  assets de "golden" de `slider2/` a `slider3/` y los de "momentos" de `slider3/` a `slider2/`,
  una vuelta posterior de trabajo dejó **copias duplicadas en ambas carpetas** (probablemente por
  un `cd` a una ruta ya usada como base relativa en una sesión de shell distinta). Nada se rompió
  visualmente porque cada `sliderN.html` seguía apuntando a su propia ruta relativa correcta, pero
  quedaron ~6 archivos huérfanos sin ninguna referencia. Antes de dar por cerrada una
  reorganización de assets: `find sliders -type f | sort` y compara contra un
  `grep -o 'src="[^"]*"\|url([^)]*)' sliders/*/sliderN.html` de cada slider — cualquier archivo que
  no aparezca en ningún grep se borra.
- `.sf-card` / `.sf-card-dark`: contenedor base claro/oscuro ya usado en el resto del curso.
- `.color-light`: span de acento de color para una palabra dentro de un título.
- Iconos: Bootstrap Icons (`bi-*`, ya cargado por CDN en el `<head>`) o Font Awesome — nunca generes
  ni pidas un SVG/PNG nuevo solo para un ícono.
- Mascota/fotografía: revisa qué personajes ya existen en `assets/img/personajes-*` (grep por
  `personaje` o el nombre de la mascota del curso) antes de pedir un asset nuevo — normalmente ya
  hay una pose que sirve.

### 3. Patrón visual por slide (clases nuevas, con prefijo `sliderN-`)

Cada slide define sus propias clases en su propio `sliderN.css` (con prefijo `sliderN-` para no
chocar con las de otros sliders del mismo módulo, que cargan todos a la vez en la misma página).
Piezas ya validadas, cópialas tal cual y ajusta solo el contenido:

```css
.sliderN-eyebrow{display:inline-block;background:var(--sf-gold);color:#fff;text-transform:uppercase;
  font-size:.72rem;font-weight:800;letter-spacing:.08em;padding:6px 14px;margin-bottom:16px;}
.sliderN-headline{color:var(--color-dark);font-size:2.1rem;font-weight:900;line-height:1.15;margin:0;}
.sliderN-rule{width:64px;height:3px;background:var(--sf-gold);margin:18px 0 20px;}
```
Acento de color dentro del título: `<span class="color-light">…</span>` sobre una frase corta, no
la palabra suelta.

Foto circular con anillo (para un hero de mascota/persona): contenedor cuadrado (`::before{content:"";
display:block;padding-top:100%;}` para el aspect-ratio), un `<svg>` con dos `<circle>` parciales
(`stroke-dasharray`/`stroke-dashoffset`, uno en `var(--sf-gold)`, otro en `var(--color-light)`)
`position:absolute;inset:-16px;`, y la imagen `position:absolute;inset:0;object-fit:contain;`
encima. Es el mismo patrón en los tres sliders ya migrados de este módulo — cópialo del más
parecido (`sliders/slider0/slider0.html` o `slider1/slider1.html`) en vez de rehacerlo.

Sin barra ni porcentaje de progreso **dentro** del contenido del slide tampoco (mismo criterio que
el header) — si el contenido original traía algo así, no lo migres.

### 4. Si hay que portar contenido literal desde una versión "generación A" (parámetro `contenido`)

1. Lee el `modulo.php`/`index.php` de origen y localiza los sliders exactos a portar (por comentario
   `<!-- sliderNN nombre -->` si los hay).
2. **Antes de reusar una imagen del curso destino**, ábrela y mírala — no asumas por el nombre de
   archivo qué contiene. Un PNG pensado para superponerse sobre un panel oscuro (texto blanco
   "quemado" en la imagen) se vuelve invisible sobre el fondo claro de este patrón editorial; en ese
   caso no lo actives con un div oscuro solo para ese gráfico — reemplázalo por texto real (mismo
   contenido, en un `<p>`) o descártalo si el titular ya lo dice.
3. Si el contenido a portar no encaja 1:1 en el número de sliders ya existentes en el destino
   (p. ej. la fuente tiene 2 pantallas y el destino tiene 1 slot), **no fuerces** — pídele al
   usuario cómo repartirlo en vez de inventar una estructura.
4. **Reordenar contenido entre carpetas de slider = mover también sus assets.** Si el slider que
   pasa a ser "Golden" tiene su audio/imágenes en la carpeta de otro slider (porque una migración
   previa los dejó mal ubicados), muévelos con `mv` a la carpeta del slider correcto — no los
   referencies con una ruta relativa cruzada (`sliders/slider2/img/...` desde `slider3.html`), queda
   confuso para el próximo que edite. Después de mover, `grep -rn` el nombre del archivo movido por
   todo el módulo para confirmar que no quedó ninguna referencia rota a la ruta vieja, y borra
   cualquier asset que quede sin ningún HTML que lo referencie (no dejes archivos huérfanos).
5. Al agregar o reordenar slides en `MODULE_CONFIGS[...].slides[]`, dale a **cada** entrada un
   `"slideKey"` explícito (no dependas del valor por defecto `modKey + '_slider' + (posición+1)`,
   que se calcula por posición en el array) — si no, reordenar desplaza las claves de progreso ya
   guardadas de los slides que no cambiaron de contenido, solo de posición.

### 5. Textos y títulos

El `title` de cada slide en `MODULE_CONFIGS[...].slides[]` es lo que se muestra en el eyebrow del
header y en el modal "Ir a pantalla" — que describa el contenido real de *ese* slide (no dejes el
título de una versión anterior del contenido, ni dos slides con el mismo título literal: el modal de
búsqueda se vuelve ambiguo).

### 6. Verificar (no lo des por terminado solo leyendo el código)

Playwright ya está instalado globalmente en esta máquina pero `npx playwright` solo resuelve el
CLI, no el módulo — en un script Node hay que requerirlo por ruta absoluta:
```js
const { chromium } = require('C:\\Users\\<usuario>\\AppData\\Roaming\\npm\\node_modules\\playwright');
```
Con el curso servido por WAMP en `http://localhost/...`:
1. Captura a ~1400px de ancho y a ~390px con un user-agent de iPhone real (`.is-mobile-device` en
   este framework se decide por user-agent + tamaño, no solo por media query).
2. Haz clic en "Continuar"/"Anterior", en un punto de acceso directo y en el ícono de menú móvil —
   confirma que el contador cambia y que el punto/tarjeta correspondiente queda marcado.
3. Revisa `page.on('pageerror', ...)` y las respuestas no-2xx (`page.on('response', ...)`) — descarta
   los 404/403 que ya existían antes de tu cambio (compara contra una corrida en la rama sin tocar
   si hay dudas) de los que sí introdujiste tú.
4. Si el header es compartido, repite el check en al menos otro módulo del mismo curso que no hayas
   tocado el contenido, para confirmar que el cambio de header no rompió nada ahí.

## Entrega

Resume: qué módulo(s) se tocaron, si el cambio de header fue a nivel de curso (afecta a otros
módulos) o quedó local, qué sliders cambiaron de contenido y de dónde salió ese contenido, qué
assets se movieron o se borraron por quedar huérfanos, y el resultado de la verificación en
escritorio/móvil (con qué no se pudo probar, si algo quedó pendiente de datos reales de servidor).

## Prohibido

- Editar `plugins/js/interactividad.js` cuando el curso carga `plugins-html/js/interactividad.js`
  (o viceversa) sin haber confirmado con grep cuál referencia el `<script src>` real.
- Reintroducir el porcentaje visible o una barra de progreso rellena dentro de una tarjeta —ya se
  probó y el cliente lo rechazó explícitamente dos veces.
- Mostrar `.module-screens-btn` en escritorio o los puntos `.section-indicator` en móvil a la vez —
  es uno u otro según tamaño de pantalla, a propósito.
- Reusar una imagen de una versión anterior sin abrirla primero para confirmar que su fondo/contraste
  funciona sobre el nuevo layout claro.
- Dejar archivos de imagen/audio sin ninguna referencia en el HTML después de reorganizar contenido
  entre sliders.
- Replicar un cambio de `slides[]` en las copias de `MODULE_CONFIGS` de módulos que no estás
  rediseñando — no lo necesitan y es una fuente más de desincronización.
