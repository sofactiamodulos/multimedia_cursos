---
description: Une dos plantillas de curso en una nueva — la estructura (generación B, gases_caribe: módulos, sliders por fetch, seguimiento, bloqueo) con el diseño y contenido de otra (generación C, antioquia-gold-nuevo) — sin tocar las originales, sin scroll y verificado en escritorio y teléfono.
---

# /plantilla_union_diseño

Crea una **plantilla nueva** que toma:

| De la plantilla **estructura** (generación B) | De la plantilla **diseño** (generación C) |
|---|---|
| `modulos/moduloN/moduloN.html` + `#sliders-container` | Todo lo visible: pantallas, cabeceras, botones, colores, tipografía |
| `sliders/sliderN/sliderN.{html,css,js}` cargados por `main.js` | Contenido (textos, audios, imágenes, quizzes) |
| `MODULE_CONFIGS` (5 copias en línea + `modulos.json`) | Interacciones de `app.js` |
| `interactividad.js`: `nextSection()` / `prevSection()` / CapsuleManager | |
| Seguimiento y bloqueo secuencial (`ProgresoLecciones`, `inicio.js`) | |

Caso de referencia (septiembre 2026):
- **Estructura:** `course_content/gases_caribe/induccion_contratista_sst`.
- **Diseño:** `course_content/plantillas/antioquia-gold-nuevo`.
- **Resultado:** `antioquia_induccion_sst_nuevo` (v1, con la interfaz de Gases) y `antioquia_induccion_sst_nuevo_v2`, la versión buena, sin interfaz de Gases.
- **Ubicación actual:** la usuaria movió ambas a `Documents\3.Sofactia\antioquia_gold\`. Antes de nada, pregunta o busca dónde están.

Diseño de pantallas: `/disenar-curso`. Registro en BD y URL: `/crear-curso`.

Herramientas guardadas en `.claude/herramientas/plantilla_union_diseno/`:
- **Tienen rutas fijas** (`SRC`, `DST`, `BASE`): cámbialas antes de usarlas.
- **Generación:**
  - `css_scope.py`: acota el CSS del diseño.
  - `build_slides_v2.py`: genera los sliders y `MODULE_CONFIGS`.
- **Verificación:** `v2_solapes.py`, `v2_medir_todo.py`, `v2_probar_interacciones.py`, `v2_navegacion.py`, `v2_imagenes.py`.
- **Captura:** `v2_shoot.py`.

---

## 0. Reglas de la usuaria (no se negocian)

1. **No tocar nada existente.** Se crea una carpeta nueva; las dos plantillas de origen quedan intactas.
   Si hay que iterar, se hace **otra versión** (`_v2`, `_v3`) copiando la anterior.
2. **No inventar contenido.** Lo que falta se marca como pendiente, visible:
   `<div class="pending"><span class="pending-tag">Pendiente</span><p>…</p><span class="pending-src">Excel f39</span></div>`.
   Audios que faltan: reproductor con `--:-- / --:--` y comentario `<!-- PENDIENTE: assets/xxx.mp3 -->`.
3. **Sin scroll.** Ninguna pantalla desplaza, en ningún tamaño. Si no cabe, se compacta
   (decorativo primero, espaciado después); nunca se baja el texto de 14px ni los toques de 44px.
4. **No hacer commit, `git add`, push ni cambiar de rama** salvo que lo pida.
5. Nunca editar `.env`. BD: escritura solo en `courses_demo`.
6. Peso del curso **≤ 50 MB** (objetivo real: < 10 MB).

---

## 1. Qué quiere la usuaria del resultado (v2, no v1)

La v1 metía las pantallas de diseño **dentro** de la interfaz de Gases y **no gustó**. La v2 es la correcta.

**Se retira** de `modulos/moduloN/moduloN.html`:
- `<aside class="route-sidebar collapsed">` (menú lateral).
- `<header class="module-header">`.
- `<nav class="module-nav-footer">` y sus botones.
- `<div id="bottom-nav-container">` y el `<script>` de `navegacion.js`.
- En `inicio/inicio.html`: la maqueta de ruta de Gases, `route-layout.js` y `navegacion.js`.

**Se conserva** la cabecera y los botones propios de cada pantalla del diseño, **conectados** a la estructura.

"La idea es llevarse todo el diseño": la portada (`index.html`) y la ruta (`inicio/inicio.html`) también son las del diseño.

Tras quitar elementos, **protege los JS que los buscaban**:
- `var b = document.getElementById('backButton'); if (b) b.addEventListener(…)`.
- Revisa `interactividad.js`, `main.js`, `route-layout.js` y `language-switcher.js`; todos deben tolerar `null`.

---

## 2. Procedimiento

### Paso 1 — Extraer las fuentes sin cambiar de rama

La plantilla de diseño puede existir solo en otra rama (`development`). Extrae una copia de solo lectura al scratchpad:

```bash
git archive development course_content/plantillas/antioquia-gold-nuevo | tar -x -C "$SCRATCH/fuente"
```

### Paso 2 — Copiar la estructura a la carpeta nueva

- Copia la plantilla de estructura completa.
- Borra sus sliders de contenido; deja la maquinaria: `plugins/`, `inicio/`, `modulos/moduloN/moduloN.html` y `.js`.
- Copia al curso nuevo los assets del diseño:
  - Imágenes en `assets/img/` (carrusel incluido).
  - Audios en `assets/audio/`.

### Paso 3 — CSS del diseño acotado (`css_scope.py`)

`styles.css` del diseño → `plugins/css/antioquia-theme.css`:
- **Selectores:** cada selector `S` pasa a `.ag-slide :is(S)`.
  - Los pseudo-elementos quedan fuera: `.ag-slide :is(S)::before`.
  - `:root` pasa a `.ag-slide`.
  - Se descartan `html`, `body`, `.topbar` y `.brand-link`.
- **Consultas de tamaño:** los `@media` que solo miran ancho o alto pasan a `@container ag (…)`. Dentro del módulo, la pantalla no es la ventana.
- **Rutas:** las `url()` pasan a `../../assets/img/…` (relativas al CSS en `plugins/css/`).
- **Verifica** que las llaves estén balanceadas.

Con `:is()`, el marcado original se mantiene **intacto** dentro del envoltorio `<section class="module-slide ag-slide" data-ag="…">`.

### Paso 4 — Sliders + configuración (`build_slides_v2.py`)

**Cortes:**
- **Momento 0:** 1 pantalla del diseño = 1 slider.
- **Lecciones:** cada `section.lesson-screen[data-step]` = 1 slider, envuelto en su raíz (`<section data-lesson …><div class="m1-sig-root">…`).
- **Modales entre pasos** (p. ej. `.hazard-modal`): van con el paso anterior.

**Transformaciones:**
- Quitar `hidden` de la `<section>`.
- Rutas: los mp3 van a `../../assets/audio/` y el resto a `../../assets/img/` (relativas a `moduloN.html`, que es quien hace el fetch).

**`sliderN.js`:**
```js
window.initSliderN = function () {
  var root = document.querySelector('[data-ag="CLAVE"]');
  if (root && window.AG) window.AG.init(root);
};
```

**Configuración:**
- `MODULE_CONFIGS` se escribe en `modulos.json` **y** en las 5 copias en línea: `inicio.html` + `modulo0-3.html`.
- Cada módulo: `title`, `subtitle` (≤ 6 palabras, para la tarjeta de la ruta), `image`, `time` y `slides[{id,path,title}]`.

**Conexión de botones.** Regex en este **orden exacto**:
```python
frag = re.sub(r'\sdata-go="m[0-9]-[a-z-]+"\s+data-lesson-done="\d+"', ' data-ag-next', frag)  # 1 cierre de lección
frag = re.sub(r'\sdata-lesson-done="\d+"', '', frag)
frag = re.sub(r'(class="primary-action"[^>]*?)\sdata-go="[^"]*"', r'\1 data-ag-next', frag)  # 2 pie Momento 0
frag = re.sub(r'(class="back-button"[^>]*?)\sdata-go="[^"]*"', r'\1 data-ag-prev', frag)
frag = re.sub(r'\sdata-prev(?=[\s>])', ' data-ag-prev', frag)                               # 3 pie lecciones
frag = re.sub(r'\sdata-next(?=[\s>])', ' data-ag-next', frag)
frag = re.sub(r'\sdata-go="(?:cover|m0-ruta)"', ' data-ag-ruta', frag)                        # 4 volver a la ruta
```
> ⚠ Si "volver a la ruta" se aplica antes, el botón final de un módulo salta a la ruta **sin completarlo**
> y el siguiente queda bloqueado para siempre. Comprueba: todos los pies = [prev|ruta] + [next].

### Paso 5 — `plugins/js/antioquia-interactions.js`

Porta `app.js` del diseño con **delegación de eventos**, porque el contenido llega por fetch después de cargar la página. Incluye:
- **Datos y controles:** QUIZ (copiado literal), audio con onda y tiempo reales, carruseles, modal, tarjetas y casos.
- **Arranque:** `window.AG.init(root)`, idempotente.
- **Navegación:**
  ```js
  if (t.closest('[data-ag-next]')) nextSection();          // en la última pantalla completa el módulo y abre el siguiente
  if (t.closest('[data-ag-prev]')) { cm.currentIndex > 0 ? prevSection() : irRuta(); }
  if (t.closest('[data-ag-ruta]')) irRuta();               // ../../inicio/inicio.html?course_code=…
  ```
- **Cabecera** (`pintaCabecera`): calcula el progreso real a partir del slider activo:
  - `pct = round((i+1)/n*100)`.
  - Escribe `NN % confirmado`, `NN / TT` y el ancho de la barra.
  - **Solo escribe si el valor cambió**; si no, el MutationObserver entra en bucle.
- **MutationObserver** (childList + subtree + class): llama a `AG.init` y `pintaCabecera`.

### Paso 6 — Portada y ruta

- **`index.html`:** la portada del diseño con `button.primary-action#btn-start`; el JS existente abre `inicio`.
- **`inicio/inicio.html`:** la pantalla de ruta del diseño (`.ag-route > section.lessons-screen`).
- **`inicio.js`:** pinta las `button.lesson-card` desde `MODULE_CONFIGS`:
  - **Estados:** `is-next`, `is-locked` (con `aria-disabled`) e `is-done`.
  - **Al seleccionar:** cambia la imagen, y el botón dice el destino ("Comenzar momento 02" / "Repasar…").
  - **Tarjeta bloqueada:** abre el modal existente.
  - **Progreso global:** módulos completados / total.

### Paso 7 — `plugins/css/antioquia-shell.css` (la costura)

Enlázalo **después** de `antioquia-theme.css` en las 6 páginas. Contenido mínimo:

```css
.layout-route, .route-main.module-page { height: 100svh; }
.module-content-scroll > .sf-app, .module-content-scroll #sliders-container { width:100%; height:100%; }
.content-section.active:has(> .ag-slide) { width:100%; height:100%; container-type:size; container-name:ag; }
.ag-slide > section,
.ag-slide :is(.m1-sig-root,.screen,.lesson-screen,.lesson-slide-screen,.lessons-screen),
.ag-slide :is(.lesson-slide-shell,.shell,.lessons-shell) { height:100% !important; min-height:0 !important; }
.ag-slide :is(.stage,.slide-stage,.activity-stage,.audio-stage,.evaluation-stage) { align-items:safe center; align-content:safe center; }
.ag-cover, .ag-route { height:100svh; container: ag / size; overflow:hidden; }
```

**Choques con la estructura (todos ocurrieron):**

| Síntoma | Causa | Arreglo |
|---|---|---|
| Títulos a 28px y párrafos planos a 16px en todo el curso | `styles.css`: `#sliders-container .module-slide h1/p` (selector de **id**, gana a todo el tema) + `p{color;margin-bottom}` global | En `styles.css` de la copia: `.module-slide:not(.ag-slide) h1/p`. En shell: `.ag-slide :where(h1,h2,h3,h4,p){color:revert;font-size:revert;font-weight:revert;line-height:revert;margin-top:revert;margin-bottom:revert}` |
| Texto oscuro sobre fondo verde | el mismo `p{color:#102015}` | la regla `revert` de arriba |
| `h1` centrados | `h1{text-align:center}` global | `.ag-slide :is(h1,h2,h3,h4){text-align:inherit}` |
| Progreso de la cabecera aplastado a 6px | Bootstrap `.progress` | `.ag-slide .progress{height:revert;overflow:revert;display:revert;font-size:revert;background-color:revert;border-radius:revert;box-shadow:revert}` |
| Textos finos | Bootstrap `.lead` peso 300 | `.ag-slide .lead{font-size:revert;font-weight:revert}` |
| Etiquetas redondeadas | Bootstrap `.badge` | revert de padding, font, color, align, white-space y border-radius |
| Pantallas +195px de alto | reglas de lección con más especificidad midiendo `100svh` | `!important` en los altos (bloque de arriba) |
| Contenido cortado por arriba | centrado normal desborda hacia arriba | `safe center` |
| Iframe de video con 404 "Error response" | `main.js › limpiarRecursosAnteriores` hace `setAttribute('src', null)` en iframes sin src | en la copia: `if (!src) return;` antes de blanquear |
| `.sf-app` con ancho 0 | `display:flex` en `.module-content-scroll` | usar width/height 100%, no flex |

**Teléfono** (`@container ag (max-width: 480px)`). Lo que hizo falta para que todo quepa en 390×740:

- **Espacio de la pantalla:**
  - **Cabecera compacta:** padding superior 8px, `gap` del shell 8px, cabecera en 2 columnas (volver | progreso), `progress-meta` a 12px con el nombre de la sección en una línea con elipsis, y "Volver" con `min-height:44px`.
  - **Pie compacto:** `min-height:0; padding:8px 16px`. Los botones mantienen 44px.
  - **Escenario:** `grid-template-rows:none; grid-auto-rows:auto; align-items:start; align-content:start` (con `!important`) y `row-gap:8px`.
  - **Filas del escenario:** `.stage > * { min-height:auto }`. **Clave:** el `min-height:0` del tema dejaba encoger la fila y el bloque siguiente **se montaba encima** (el video tapaba el texto).
  - **Red de seguridad:** `overflow-y:auto` en el escenario. No debe llegar a usarse; las pruebas deben dar 0 desplazamiento.
- **Qué ceder:**
  - `.visual-card` oculta.
  - Nodos SIG en horizontal.
  - Carrusel PHVA con rejilla `44px 1fr 44px`.
  - **Pista PHVA con `min-height:320px`:** las tarjetas son absolutas y con 0 desaparecen.
  - **11 reglas:** 2 columnas, icono al lado, 14px, **nunca `overflow-wrap:anywhere`** (partía "Trabaj/o").
  - Reglas m2/m3: 1 columna.
- **Componentes:**
  - **Avisos pendientes:** padding 8px 10px. La nota `.lesson-audio + .pending-src` ("Falta …mp3") se oculta solo en teléfono.
  - **Reproductor:** play de 44px y onda de 24px de alto.
  - **Video-caso:** `.copy{display:contents}`, rejilla `1fr 124px`, y el teléfono del video en la columna 2 **al lado del aviso**, no debajo.
  - **Tareas de alto riesgo:** botones a 14px (no 13) y panel del caso con padding 10px 14px.
  - **Emergencias:** tarjeta compacta, número a 30px y correos con `overflow-wrap:anywhere`.

---

## 3. Verificación (obligatoria antes de decir "listo")

**Servidor:** `python -m http.server 8767 --bind 127.0.0.1` en la carpeta del curso, en segundo plano. **Apágalo al terminar.**

**Chrome headless:**
- No acepta ventanas de menos de 500px. Usa un **iframe puente** del tamaño exacto y user-agent de iPhone para teléfono.
- **Desactiva animaciones** antes de medir o capturar (`*{animation:none!important;transition:none!important}`); si no, las capturas salen desplazadas o desvaídas.
- En `--screenshot` usa **ruta absoluta de Windows** (`cygpath -w`); con ruta relativa no escribe el archivo.
- La franja blanca inferior de las capturas es del puente (ventana h+40), no del curso.

**Tamaños:** `1440x900 1366x768 390x740`.

| Herramienta | Qué comprueba | Resultado esperado |
|---|---|---|
| `v2_medir_todo.py` | scroll y recortes fuera de la ventana | "Todas las pantallas caben, sin scroll ni recortes." |
| `v2_solapes.py` | contenido bajo el pie o sobre la cabecera, **bloques montados unos sobre otros**, y escenario desplazable | "Ningún contenido queda tapado…" y ninguna línea `(desplazable)` |
| `v2_probar_interacciones.py` | audio, quizzes, carruseles, modal, tarjetas, casos | "Todas las interacciones funcionan." |
| `v2_navegacion.py` | sin interfaz de Gases; Continuar/Anterior/Volver; cierre de módulo desbloquea el siguiente; estados y % de la ruta; errores JS | "Navegación correcta." |
| `v2_imagenes.py` | cada `img`, `source` y `url()` de `assets/img` carga | "Imágenes rotas: 0" |
| `v2_shoot.py` | captura de un slider concreto | **mírala**: las métricas no ven todo |

Ojo con los falsos resultados, que ya ocurrieron:
- **La medición de "cabe" no detecta solapes internos.** Por eso existe `v2_solapes.py`; aun así, revisa capturas de las pantallas más densas en teléfono.
- **"Cabe" con 3px de margen no es cabe:** deja holgura.
- **Aviso esperado en M0 slider 2:** `v2_solapes.py` marca el SVG de audífonos sobre el kicker, pero es el adorno de fondo de la plantilla.
- **`v2_navegacion.py` antiguo** contaba `ERRORES_JS=ninguno` como fallo; ya está corregido (`'ERROR '`).

---

## 4. Imágenes y peso

**Listado:** por cada imagen, peso, dimensiones (leídas de la cabecera del archivo; no hay PIL), formato, si tiene transparencia (WebP `VP8X`/`VP8L` con bit alfa) y si se usa.

**Referencia (septiembre 2026):** 9 PNG pesaban 15,5 MB (carrusel de 1254² a 2 MB cada uno, portada de teléfono 2,2 MB). La usuaria los convirtió a WebP y el curso pasó de **20 MB a 6 MB** (imágenes: 16,65 → 2,7 MB).

**Tras una conversión:**
1. Busca referencias al nombre viejo en `index.html`, `antioquia-theme.css`, sliders (`src`, `srcset` y `style="--key-bg:url(…)"`), `modulos.json` y `MODULE_CONFIGS`, y cámbialas a `.webp`.
2. Busca referencias rotas: toda `assets/img/…` debe existir.
3. Ejecuta `v2_imagenes.py` y captura la portada y una pantalla con recorte.
4. Los recortes (avatares, personas, logos) deben conservar la transparencia.

**Conocido:** `glosario/index.html` apunta a 2 imágenes inexistentes de `portada-videos/`, heredadas de Gases. El glosario no tiene acceso sin menú lateral.

---

## 5. Informe final a la usuaria

Breve y en español. Incluye:
- Qué se retiró y qué se conectó.
- El resultado de las 5 pruebas en los 3 tamaños.
- Los arreglos hechos, con el porqué en una frase.

Y siempre estos avisos:
- **Accesos perdidos:** sin menú lateral no hay acceso al glosario, la ayuda, la accesibilidad ni el idioma (los archivos siguen en la carpeta).
- **Contenido pendiente:** audios que faltan (`l2-equipo`, `l2-cierre`, `l3-cierre`), videos y contenidos marcados.
- **Tiempos:** los tiempos por módulo son estimados (M0 = 3 min) frente a los 10 min de la portada.
- **Peso** actual del curso.
- **Git:** que no hubo commit, add, push ni cambio de rama.
