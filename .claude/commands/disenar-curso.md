---
description: Diseña las pantallas de un curso con el sistema visual de antioquia-gold-nuevo (generación C, estática), calibrado para adultos trabajadores con poco tiempo y baja lectura en móvil: color, tipografía, medios, navegación y los 8 momentos del curso.
---

# /disenar-curso

Produce el **diseño y el contenido de las pantallas** de un curso siguiendo el sistema de
`course_content/plantillas/antioquia-gold-nuevo`. Es la parte visual y editorial; la fontanería
(copiar carpeta, registrar en BD, URL pública) es `/crear-curso`.

Referencia: `course_content/plantillas/antioquia-gold-nuevo/`
(`index.html` 373 líneas · `styles.css` 2.090 · `app.js` 208).

> **No es generación A ni B** del manual (§9): sin PHP, sin `MODULE_CONFIGS`, sin tracking, sin
> `locales/`. HTML/CSS/JS plano. Trátala como **generación C**. Si el curso necesita progreso
> persistido o matrícula, el diseño sale de aquí y el armazón de `/crear-curso` sobre una plantilla B.

---

## Entrada

Forma corta:

```text
/disenar-curso
curso:     <título>
empresa:   <marca: nombre, logo, colores>
lecciones: <cantidad y título de cada una>   (opcional, default 4)
momentos:  <tipos por lección, ver §5>       (opcional)
```

Forma larga: **un brief pantalla por pantalla**, como el del anexo. Es el formato preferido — el
anexo reproduce el brief real que generó la plantilla de referencia y sirve de plantilla de entrada.

Toma del contexto lo que el usuario ya dijo. No vuelvas a preguntar.

**Cuándo parar y preguntar**
- No hay logo ni colores de marca y el curso no es de Antioquia Gold.
- Piden más de 6 lecciones o más de 5 ítems por pantalla (rompe la dosificación, §5).
- Piden scroll vertical dentro de una pantalla (rompe el esqueleto, §4).

---

## 0. El perfil del aprendiz manda sobre todo lo demás

Cuatro restricciones. Cuando una decisión de diseño choque con una de ellas, gana la restricción.

**Educación de adultos.** Trabajadores, no estudiantes. Nada de infantilizar: sin emojis, sin
felicitaciones exageradas, sin lenguaje escolar. El tono es de respeto profesional — *"Antes de
ingresar, reconoce el riesgo y decide seguro."* Las actividades plantean un **dilema laboral real**,
no una pregunta de memoria. El error se explica, no se castiga. Di siempre por qué importa, no solo
qué hacer.

**Poco tiempo.** El compromiso se promete en la portada (`10 min`) y se desglosa por lección
(`2 min`, `3 min`). Ninguna pantalla debe pedir más de ~40 segundos. El progreso (`04 / 10`) está
siempre visible para que sepa cuánto falta. Un curso que no se puede terminar en un descanso no se
termina.

**Bajo nivel de lectura.** Es la restricción que más diseño cambia:
- **Piso de 16px** en móvil para cualquier texto que haya que leer. Sin excepciones para las
  opciones de respuesta ni los subtítulos de lección.
- **Topes de longitud**: titular ≤ 4 palabras · frase de apoyo ≤ 14 palabras · opción de respuesta
  ≤ 8 palabras · descripción de tarjeta ≤ 6 palabras.
- **Imperativo, presente, voz activa, sin subordinadas.** *"Detengo la labor y reporto."*
- **Nunca solo texto.** Cada verificación lleva icono, cada lección número, cada opción letra, cada
  estado color. El texto es una de dos señales, jamás la única.
- Si un concepto necesita un párrafo, es audio o vídeo, no párrafo.

**Móvil primero.** Se diseña la pantalla de 390px y después se expande. El escritorio es la versión
cómoda, no la de referencia. Ver §8.

---

## 1. Color

Declara **todo** en `:root`. La plantilla define 8 tokens pero usa colores crudos en 57 sitios.

```css
:root {
  --c-primary:   #0e642e;  /* verde marca */
  --c-deep:      #124734;  /* TODOS los titulares sobre fondo claro */
  --c-accent:    #ae841f;  /* acento único */
  --c-on-accent: #211706;  /* texto sobre el acento */
  --c-badge:     #687d44;  /* etiqueta de contexto */
  --ink:         #1b211d;
  --paper:       #f5f4ef;
  --white:       #ffffff;
  --shell:       #081a12;  /* fondo del body */
  --muted:       #4d5b51;  /* UN gris de apoyo, no siete */

  --deep-04: rgba(18,71,52,.04);  --deep-08: rgba(18,71,52,.08);
  --deep-14: rgba(18,71,52,.14);  --deep-22: rgba(18,71,52,.22);
}
```

**Un solo acento.** El dorado dirige la atención: CTA, progreso, franja izquierda, numeración.
Si algo no es acción ni jerarquía, no lleva dorado.

**Cero azul.** Restricción explícita de marca: ninguna barra, botón, indicador, enlace ni estado en
azul. Ojo con los defectos del navegador — `<a>` sin color, `<progress>`, `accent-color` en inputs y
el `:focus` nativo entran en azul si no los pisas. Todo va en verde / dorado / blanco.

**Piedra `#C4BEB6` y tierra `#4B3D2A`** están en la paleta de marca pero la plantilla los declara y
no los usa nunca. O les das un rol (separadores, fondos de estado neutro) o no los declares.

**Contraste — regla dura.** `#ae841f` sobre blanco = **3,43:1**. Vale para texto ≥24px, bordes y
rellenos; **falla AA en texto pequeño**. La plantilla lo usa a 13px en kickers y tiempos: es un
defecto. Microtexto en `--c-deep` (10,6:1). Sobre dorado, texto en `--c-on-accent`.

**Color como segunda señal, nunca como única.** Con baja lectura y pantallas al sol, el color solo
refuerza: la tarjeta siguiente es dorada **y** dice el tiempo; la bloqueada está atenuada **y** dice
"se activa al terminar".

---

## 2. Tipografía, sección por sección

`Roboto, "Segoe UI", Arial, sans-serif`. **Sin `@font-face`, sin Google Fonts** — cero peticiones de
red por tipografía. Dos pesos: **900** (titulares, etiquetas, botones, microtexto) y **800**. No
introduzcas 400/500/600.

Titulares con `line-height` **menor que 1** (.94–.98) y `clamp()`. Esa compresión es la firma.

### Escala real de la plantilla, con la corrección obligatoria en móvil

| Sección | Elemento | Escritorio | ≤840px | ≤420px | Corrección |
|---|---|---|---|---|---|
| **Portada** | badge | 14 | 12 | 11 | → **13** mín. |
| | h1 | `clamp(50,5.8vw,78)` | `clamp(38,11.8vw,54)` | `clamp(34,11.4vw,46)` | ok |
| | frase | `clamp(20,2.4vw,28)` | 18 | 18 | ok |
| | dato fuerte | 21 | 17 | 16 | ok |
| | dato pequeño | 13 | 11 | 11 | → **13** mín. |
| **Lecciones** | h2 | `clamp(42,7vw,74)` | `clamp(34,10.5vw,48)` | — | ok |
| | párrafo | 22 | 17 | — | ok |
| | título tarjeta | 23 | 18 | 18 | ok |
| | descripción tarjeta | 15 | **13** | 13 | → **16** mín. |
| | tiempo | 13 | 13 | 13 | → 13 en `--c-deep`, no dorado |
| **Contenido** | h2 | `clamp(60,7vw,65)` | `clamp(38,11vw,52)` | `clamp(35,10.5vw,44)` | clamp roto: 60→65 es rango nulo, usa `clamp(42,6vw,68)` |
| | lead | `clamp(21,2.2vw,28)` | 18 | 16 | ok |
| | título verificación | 20 | 16 | 15 | → **17** mín. |
| | detalle verificación | 15 | 13 | **12** | → **16** mín. |
| **Video-caso** | h2 | `clamp(52,7vw,80)` | `clamp(38,11vw,52)` | — | ok |
| | párrafo | `clamp(21,2.1vw,28)` | 18 | — | ok |
| **Actividad** | pregunta | `clamp(20,2vw,26)` | 19 | — | ok |
| | **opción de respuesta** | 16 (heredado) | **14** | 14 | → **17** mín. — es la decisión del curso |
| **Audio** | kicker | 13 | 11 | 11 | → **13** mín. |
| | h2 | `clamp(52,6.6vw,80)` | `clamp(36,10vw,48)` | — | ok (quita el `font-weight:500` muerto) |
| | meta | 13 | 12 | 12 | ok (es redundante) |
| **Evaluación** | h2 | `clamp(52,7vw,70)` | `clamp(38,11vw,52)` | — | ok |
| | párrafo | `clamp(21,2.1vw,28)` | 18 | — | ok |
| **Transversal** | progreso interno | 12 | **10** | 10 | → **12** mín.; va con barra, es redundante |
| | volver | 14 | **12** | 12 | → **14** mín. |

**La regla que resume la tabla:** el salto de 52px (titular) a 14px (opción de respuesta) en la
misma pantalla móvil es demasiado. Con baja lectura, **el texto que exige una decisión no puede ser
el más pequeño de la pantalla.**

---

## 3. Ritmo claro / oscuro

**Una foto de fondo (`fondo_seccion.webp`, 30 KB) + cuatro velos = cuatro ambientes.**

| Pantalla | Fondo | Texto | CTA |
|---|---|---|---|
| Portada | foto + 2 degradados oscuros (90° protege el texto, 180° asienta) | blanco | dorado |
| Lecciones | `linear-gradient(180deg,#fff,var(--paper))` | `--ink` / `--c-deep` | dorado |
| Contenido · video-caso · audio | foto + velo blanco 88–98 % | `--c-deep` | dorado |
| Actividad · evaluación | foto + `linear-gradient(135deg, deep .98, primary .94)` | blanco | **blanco / texto verde** |

**La inversión del CTA es obligatoria.** Sobre verde, el botón pasa a blanco con texto verde y al
hover se vuelve dorado. El acento nunca compite consigo mismo. Igual el `back-button`, la barra de
progreso y el enlace de volver.

El salto claro→oscuro **es** la señal de "aquí te toca a ti". No es decorativo.

---

## 4. Esqueleto: sin scroll, se pagina

Cada pantalla es una `<section class="screen">` de `min-height:100svh` con shell de tres filas:

```css
.shell {
  min-height: 100svh;
  width: min(100%, 1180px);
  margin: 0 auto;
  display: grid;
  grid-template-rows: auto minmax(0,1fr) auto;  /* cabecera · escenario · pie */
  gap: clamp(18px, 3vw, 36px);
}
```

Si el contenido no cabe, **se parte en dos pantallas**; no se alarga la sección. Con poco tiempo y
baja lectura, el scroll esconde y desanima.

**Escenario: dos columnas asimétricas.** Texto izquierda, visual derecha, `align-items:center`,
`gap: clamp(28px,5vw,74px)`. **Nunca 50/50** — la simetría mata la tensión:

```text
lecciones   .78fr / 1fr     (invertido: visual izq, contenido der)
contenido   .96fr / .82fr
video-caso  .86fr / .56fr
actividad   .78fr / .82fr
evaluación  .82fr / .58fr
```

`minmax(0,Xfr)` en texto, `minmax(360px,Yfr)` en visual.

**Geometría: cero radios.** Botones, tarjetas, badges y paneles a 90°. El redondeo solo donde
representa un objeto: círculo del icono, círculo de play, píldora del ecualizador, marco del
teléfono. Esa rectangularidad **es** el tono industrial.

**Franja izquierda dorada** en todo bloque de contenido; el grosor codifica el peso:

| 3px | 4px | 5px | 6px |
|---|---|---|---|
| datos rápidos | verificaciones, tiras de decisión | paneles (video-caso, actividad) | columna visual |

En rejillas de tarjetas la franja va **arriba**.

---

## 5. Los ocho momentos del curso

Todas las pantallas repiten el mismo **acorde de cuatro**:

```text
1. etiqueta de contexto (uppercase, 900, verde oliva, sangrada al margen)
2. h2 imperativo, 2–4 palabras, CON PUNTO FINAL
3. UNA frase de apoyo (≤14 palabras)
4. UNA sola pieza interactiva
```

**Nunca dos piezas interactivas en la misma pantalla.** Y la regla de dosificación, que depende de
la **forma**, no solo del número:

| Forma | Tope | Por qué |
|---|---|---|
| Lista vertical (verificaciones, opciones, tiras) | **3** | cada ítem lleva frase larga; a la cuarta se pierde |
| Rejilla 2×2 (lecciones, verbos, citas cortas) | **4** | se leen como bloque, no como secuencia |
| Datos de portada | **2** | son el contrato, no un resumen |

Si un bloque necesita 5, son dos pantallas. Y si la fuente trae 4 ítems irrenunciables (los cuatro
verbos de una política, por ejemplo), va en rejilla 2×2 numerada — el mismo componente que las
tarjetas de lección —, nunca en lista vertical.

### 5.1 Entrada al curso

Portada a pantalla completa: foto de contexto real (gente trabajando, no stock genérico) + capa
recortada de personas flotando sobre el degradado. Encima: etiqueta, título en dos líneas
(`<span>` por línea), promesa en una frase, **dos datos** y **un solo botón**.

Los dos datos son el contrato: **cuánto tiempo** (`10 min`) y **qué se exige** (`80% para aprobar`).
Se prometen antes de entrar, no se descubren a mitad.

Un CTA y nada más. Sin menú, sin índice, sin "saber más". La topbar con el logo solo existe aquí: al
entrar, `body.is-lessons-open` la oculta y el logo pasa a la cabecera de lecciones.

### 5.2 Entrada a las lecciones

La ruta completa visible de un vistazo: rejilla de tarjetas numeradas 2×2 en escritorio, 1 columna
en móvil. Cada tarjeta: **número · título · descripción de 6 palabras · tiempo**.

Tres estados, no más:

| Estado | Señal visual | Señal de texto |
|---|---|---|
| `is-next` | borde dorado, fondo crema | el tiempo (`2 min`) |
| `is-selected` | borde verde + sombra | — |
| `is-locked` | `opacity:.62` | "se activa al terminar la ruta" |

Al seleccionar: cambia la imagen de apoyo con fade de 120 ms **y el botón dice el destino**
("Comenzar lección 02", vía `data-lesson-title`). Nunca "Siguiente" a secas cuando se puede nombrar.

Progreso global arriba a la derecha: barra corta + porcentaje. **Los dos deben decir lo mismo**
(en la plantilla la barra está al 12% y la etiqueta dice 0%).

### 5.3 Manejo de imágenes de apoyo

La imagen **acompaña, no decora**: es el contexto real de la tarea. Dos modos en un mismo
contenedor, vía `data-lesson-image-mode`:

| `cutout` | recorte de personas sangrado al 122 %, apoyado en el borde inferior, sin velo |
|---|---|
| `photo` | foto completa, `object-fit:cover` + velo verde encima |

Reglas: todas las imágenes decorativas llevan `alt=""` + `aria-hidden="true"` +
`pointer-events:none`. Los recortes llevan `drop-shadow` para despegarlos del fondo. Nunca texto
dentro de la imagen — no se traduce, no se lee al sol, no escala.

**Formato:** todo `.webp`, originales guardados en `.assets/` (oculta, no servida). En la plantilla
el hero pasa de 2,3 MB a 186 KB. Y `<picture>` con **arte distinto en móvil**, no la misma imagen
recortada:

```html
<source srcset="hero-mobile.webp" media="(max-width: 680px)">
```

### 5.4 Manejo de video-casos

**El vídeo es vertical: marco 9:16 dentro de una carcasa de teléfono.** No 16:9 panorámico. Es
contenido pensado para consumo tipo reel, que es como este público ve vídeo.

A la izquierda, el panel de texto con franja dorada de 5px: etiqueta, titular, una frase y la **tira
de decisión** — tres palabras clave (`Riesgo visible` · `Acción segura` · `Reporte oportuno`) que le
dicen **qué mirar antes de darle play**. Sin eso el vídeo se ve pasivamente.

Reglas técnicas:
- `src` diferido en `data-video-src`; el iframe **se monta al entrar** a la pantalla, no al cargar
  la página. `loading="lazy"`.
- Al salir, `removeAttribute('src')` — se desmonta, no se pausa.
- `autoplay=false` siempre. Nunca arranques audio sin que lo pidan.
- **Máximo 90 segundos.** Si el caso necesita más, son dos casos.

### 5.5 Actividades interactivas

Pregunta + **tres** opciones en panel blanco sobre fondo verde. Cada opción es `letra + texto`
(`A` / `B` / `C` en cuadro dorado de 42px). La letra es la segunda señal para quien lee poco.

La pregunta es un **dilema laboral concreto**, no un "¿cuál de las siguientes...?":
*"Antes de ingresar al área, falta una autorización. ¿Qué haces?"* Las tres respuestas son plausibles
— la incorrecta es lo que la gente de verdad hace por las prisas, no un absurdo.

**Lo que la plantilla NO hace y hay que diseñar:**
- La clase `is-correct` está en el HTML y **no existe en el CSS**: no hay feedback. Hay que diseñar
  el estado acierto / error.
- La respuesta correcta se lee en el inspector. Sácala del atributo de clase.
- El feedback explica **por qué**, en una frase. Sin regañar. Es educación de adultos.
- La opción de respuesta a 17px mínimo en móvil (hoy 14px).

### 5.6 Audios

Momento de pausa, pantalla clara. Etiqueta, kicker, titular grande, símbolo de auriculares al fondo
en verde al 18 % y un reproductor de una sola fila: **botón circular de play de 64px** + ecualizador
+ metadatos.

El audio es la vía para lo que no se puede leer: matices, tono, testimonio. Con bajo nivel de
lectura, **lo que importa emocionalmente va en audio**, no en párrafo.

Reglas:
- `preload="none"`, nunca `autoplay`.
- El play alterna a pausa por clase (`is-playing`), y el `ended` lo devuelve a play.
- **Máximo 60 segundos.**
- Se detiene en **toda** transición de pantalla.

**Lo que la plantilla NO hace y hay que diseñar:**
- La duración `0:00 / 0:45` **está escrita a mano y nunca se actualiza**. El mp3 real dura **12 s**.
  Engancha `timeupdate`/`loadedmetadata` o quita el dato.
- El ecualizador es **decorativo puro**: alturas fijas por `nth-child`, sin `@keyframes` en toda la
  hoja. No se mueve al reproducir. Anímalo o sustitúyelo por una barra de avance real.
- No hay forma de retroceder ni de saber cuánto falta. Con audio de 60s es tolerable; por encima, no.

### 5.7 Manejo de avatares (interacción)

Los avatares recortados (`avatar-actividad.webp`, `avatar_evaluacion.webp`) aparecen **solo en los
dos momentos de exigencia**: actividad y evaluación. Es deliberado — la figura humana acompaña
cuando se pide algo, no cuando se explica.

Reglas:
- `object-fit:contain` + `drop-shadow` + `aria-hidden="true"` + `alt=""`. Es presencia, no
  información.
- En escritorio la evaluación le da mucho espacio (`min(100%,760px)`, hasta 720px de alto); en
  actividad es más contenido (`min(80%,330px)`, anclado `left bottom`).
- En móvil se encoge a ~220px y se centra (`object-position:center bottom`) — pasa de protagonista a
  acompañante.
- **Mirada y postura hacia el texto**, nunca hacia fuera del encuadre.
- No es un tutor que habla: no lleva bocadillo, no tiene nombre, no interrumpe. Baja la tensión de
  la pantalla donde se evalúa.

### 5.8 Manejo de evaluación

Fondo verde (el mismo ambiente de exigencia que la actividad). Texto a la izquierda, avatar grande a
la derecha. Etiqueta, titular, y la frase que **repite el umbral prometido en la portada**:
*"Necesitas 80% para aprobar."* El contrato se cierra donde se abrió.

Baja la tensión antes de empezar: *"Responde con calma."* El CTA es blanco sobre verde.

En la ruta, la evaluación es la tarjeta 4 y está `is-locked` hasta terminar. **Ojo:** en la plantilla
el candado es decorativo — se llega igual por el flujo lineal. Si prometes un bloqueo, impleméntalo.

**Falta y hay que diseñarlo:** el botón `Finalizar` no tiene manejador. No hay pantalla de resultado,
ni aprobado/reprobado, ni reintento, ni cierre. Un curso sin cierre no se siente terminado.

---

## 6. Cómo se pasa de pantalla

```js
// Una <section class="screen" data-screen="…" hidden> por pantalla.
// Navegar = alternar hidden. Sin router, sin scroll, sin URL.
```

**Recorrido lineal**, siempre hacia adelante, con salida lateral:

```text
portada → lecciones → contenido → video-caso → actividad → audio → evaluación
             ↑___________|__________|___________|__________|__________|
                      "Volver a lecciones" desde cualquier pantalla
```

Tres controles y no más: **Anterior** (izquierda del pie), **Continuar** (derecha del pie) y
**Volver a lecciones** (arriba a la izquierda, con `<` dorado como `::before`). El pie está siempre
en el mismo sitio — con poco tiempo, buscar el botón es fricción.

**Sin menú hamburguesa**, sin índice desplegable, sin migas de pan. La ruta de lecciones **es** el
menú, y se llega a ella con un enlace visible desde cualquier pantalla. Un menú oculto obliga a
descubrirlo; este público no lo busca.

### Header interno estándar

Todas las pantallas internas llevan la misma cabecera, sin variar de sitio:

```text
izquierda                     derecha
< Volver a lecciones          nombre de sección · % confirmado · 01 / 10
                              ────────────────────────────────  barra 3px
```

La barra va en dorado sobre base translúcida: verde al 16 % sobre fondo claro, blanco al 22 % sobre
fondo verde. En móvil el nombre de la sección salta a su propia línea (`grid-column: 1 / -1`).

### Progreso en tres niveles

1. **Curso** — `progress-pill` en la ruta: barra + porcentaje.
2. **Lección** — cabecera de cada pantalla, tres datos en una línea + barra de 3px:
   `strong` bloque · `span` "40% confirmado" · `em` "04 / 10".
3. **Pie** — Anterior / Continuar fijos.

El `04 / 10` es lo que sostiene la promesa de tiempo: dice cuánto falta en cada pantalla.

### Contrato que no se negocia

1. **Foco tras cada transición**: `screen.querySelector('h2')?.focus?.()` sobre un `h2
   tabindex="-1"`. Sin esto el lector de pantalla no anuncia nada y el patrón deja de ser accesible.
2. **`stopVideo()` y `stopAudio()` en TODA transición.** Ningún medio suena fuera de su pantalla.
3. **Los medios se montan al entrar**, no al cargar la página.
4. **Tap targets ≥ 44px** en todo lo pulsable, incluido "Volver" (hoy 34px en móvil).
5. `:focus-visible { outline: 3px solid var(--c-accent); outline-offset: 4px }`.

### Lo que hay que añadir para este público

- **Persistencia.** Hoy recargar devuelve a la portada y se pierde todo. Con poco tiempo, el curso
  se hace en dos ratos: guarda la pantalla alcanzada (`localStorage` como mínimo).
- **Los porcentajes están escritos a mano** en el HTML (`width:10%`, `40%`, `60%`…) y el contador
  promete `/ 10` pasos cuando solo existen 6. Deben calcularse.
- **Swipe lateral en móvil** — es el gesto que este público ya tiene automatizado.
- **Sin navegación por teclado** (flechas). Añádela.

---

## 7. Móvil no es el escritorio estrechado

Breakpoints: **840px** y **420px**. Recomposición real:

- Rejillas de 2 columnas → 1 columna.
- **Texto primero, imagen después** (`order:1` / `order:2`). En escritorio la imagen acompaña; en
  móvil estorbaría antes del mensaje.
- El velo de la portada **gira 90°**: horizontal en escritorio (protege el texto a la izquierda),
  vertical en móvil (oscurece abajo).
- Las figuras recortadas se salen del encuadre a propósito (`right:-78px`, `max-height:42svh`).
- Titulares a `vw` puro: `clamp(38px, 11.8vw, 54px)`.
- `max-width:330px` en h2 y párrafos: el texto se rompe en líneas cortas y deja ver la imagen.
- Pies `position:sticky; bottom:0` con fondo opaco — el CTA nunca se pierde.
- Lo decorativo sobrante **se oculta, no se encoge**
  (`.audio-wave i:nth-child(n+19){display:none}`).
- **Y el piso tipográfico de §2.** Es la diferencia entre que se lea o no.

---

## 8. Deuda verificada — NO la propagues

Contado en el código actual, no estimado:

| Dónde | Qué pasa |
|---|---|
| 57 declaraciones | colores crudos `rgba(18,71,52,.x)` en vez de tokens con alfa |
| 7 grises de texto | uno por uso: `#4d5b51 #5c665f #445247 #46544a #59645c #48534b #334139` |
| 3 tokens | `--agd-green`, `--agd-earth`, `--agd-stone` declarados y nunca referenciados (§1) |
| `.course-badge` de portada | `translateX(-clamp(22px,5vw,76px))` lo saca al margen; **el brief pedía que se alineara con el título y no se saliera del contenido**. El `.lesson-badge` sí cumple (`transform:none`) |
| `.course-badge span:first-child` | `color:#ffff` — 5 dígitos, inválido, se ignora |
| `.audio-stage h2` | `font-weight:500` pisado por `900` dos líneas después |
| `.lesson-one-copy h2` | `clamp(60px,7vw,65px)` — rango de 5px, clamp inútil |
| `.slide-progress` | bloque duplicado (líneas 767 y 787) |
| `body[data-cover="…"]` | apunta a `.png` cuando el HTML usa `.webp` — reglas muertas |
| 8 selectores huérfanos | `.cover-picker .route-section .route-grid .proposal-tabs .slide-photo .lesson-top-progress .lesson-progress .activity-progress` |
| `.activity-options .is-correct` | está en el HTML, **no existe en el CSS** — sin feedback, y la respuesta se lee en el inspector |
| `.lesson-card.is-locked` | `aria-disabled` pero enfocable y clicable; el candado es decorativo |
| `progress-pill` | CSS al 12 %, etiqueta al 0 % — se contradicen en pantalla |
| `.audio-meta` | `0:00 / 0:45` a mano; el mp3 dura **12 s** y el dato nunca se actualiza |
| `.audio-wave` | ecualizador estático: **cero `@keyframes` en toda la hoja** |
| Progreso interno | `10%`, `40%`, `60%`, `80%`, `100%` y `01/10`…`10/10` escritos a mano; solo hay 6 pantallas |
| Botón `Finalizar` | sin manejador — el curso no tiene cierre |
| Lecciones 2, 3 y 4 | no navegan; solo la 1 tiene pantallas |
| Dorado a 13px sobre claro | 3,43:1 — falla AA |
| Móvil a 10–14px | progreso, badges, descripciones y **opciones de respuesta** bajo el piso legible |
| Sin `prefers-reduced-motion` | y `color-scheme: light dark` declarado sin tema oscuro |
| Sin persistencia | recargar pierde todo el avance |

---

## 9. Verificar antes de entregar

**Perfil**
- Ningún texto legible por debajo de 16px en móvil; opciones de respuesta ≥17px.
- Ningún titular supera 4 palabras; ninguna frase de apoyo, 14; ninguna opción, 8.
- Toda señal de estado se da por color **y** por texto o icono.
- Tiempo prometido en portada y desglosado por lección; ninguna pantalla pide más de ~40s.
- Vídeos ≤90s, audios ≤60s.

**Sistema**
- Cada pantalla cabe en `100svh` sin scroll, a 1440px y a 390px.
- Acorde de cuatro en todas; ninguna con dos piezas interactivas; ninguna lista vertical de más de
  3 ni rejilla de más de 4.
- El CTA se invierte a blanco sobre fondo verde.
- Nada menor de 24px va en dorado sobre fondo claro.
- Cada bloque de contenido tiene su franja izquierda del grosor que le toca.
- Ningún token sin usar; ningún color crudo repetido.

**Comportamiento**
- Al cambiar de pantalla el foco aterriza en el `h2` y todo medio anterior se detiene.
- Los medios se montan al entrar y se desmontan al salir.
- Los porcentajes se calculan, no se escriben.
- La actividad da feedback y explica el porqué; la respuesta no está en el HTML.
- La evaluación tiene pantalla de cierre.
- Tap targets ≥44px, "Volver" incluido.
- Móvil: texto antes que imagen, pie sticky, titulares en `vw`.
- Imágenes en `.webp`, con `<picture>` donde el arte móvil difiere.

## Entrega

- Pantallas creadas, con su momento de §5 y por qué ese tipo.
- Decisiones de color, tipografía y contraste; dónde te apartaste de la plantilla y por qué.
- Deuda de §8 corregida y la que quedó igual, con motivo.
- Lo asumido por defecto, para que el usuario lo corrija.

## Prohibido

- Un segundo color de acento.
- Redondear botones, tarjetas o paneles.
- Tipografías externas.
- Scroll dentro de una pantalla en lugar de partirla en dos.
- Rejillas 50/50 en el escenario.
- Dorado sobre fondo claro en texto pequeño.
- Texto legible por debajo de 16px en móvil.
- Dos piezas interactivas en una pantalla.
- Un medio sonando al cambiar de pantalla.
- Autoplay de audio o vídeo.
- Texto dentro de las imágenes.
- Infantilizar: emojis, felicitaciones exageradas, lenguaje escolar.
- Copiar la deuda de §8 porque "así está en la plantilla".
- Modificar `course_content/plantillas/antioquia-gold-nuevo/`: se lee, no se toca.

---

## Anexo — brief de referencia

Este es el brief real que produjo `antioquia-gold-nuevo`. Sirve para dos cosas: es la **forma de
entrada preferida** (cópialo y sustituye), y explica varias decisiones del código que sin él
parecerían errores. Pídele al usuario un brief con este nivel de detalle antes de diseñar.

### Qué enseña este brief

1. **El brief manda sobre la plantilla, no al revés.** Donde el código contradice al brief, gana el
   brief. El badge de portada sangrado al margen **incumple** la instrucción "debe alinearse con el
   título, no salirse del contenido": es una desviación de la implementación, no un patrón a copiar.
2. **Tres reglas negativas que no se ven en el código.** "Evitar azul", "no usar menú hamburguesa" y
   "no usar autoplay" solo existen aquí. Sin el brief se pierden y alguien las reintroduce.
3. **Varias reglas muertas del CSS son correcciones, no basura.** `.lesson-one-visual::before` y
   `.lesson-one-screen::before/::after` están en `display:none` porque el brief pidió *"sin doble
   círculo ni borde adicional; la imagen debe mostrarse tal cual"*. Igual el botón "Leer el mensaje",
   que el brief manda quitar. Bórralas del todo al copiar, pero sabiendo por qué estaban.
4. **El drift de formato de imagen tiene origen aquí.** El brief lista `.png` / `.jpg` / `.jpeg`; la
   implementación convirtió todo a `.webp` y dejó reglas apuntando a los `.png` viejos
   (`body[data-cover="…"]`). Al copiar: **una sola lista de assets, en `.webp`**, con los originales
   en `.assets/`.

### El brief, íntegro

```markdown
Crear una plantilla HTML/CSS/JS responsive para el curso "Inducción SST para Contratistas"
de Antioquia Gold LTD.

OBJETIVO
Diseñar interfaces tipo curso e-learning para adultos, con poco tiempo disponible y bajo
nivel de lectura. Todo debe ser claro, visual, con textos cortos, botones grandes y
navegación simple. La versión mobile es prioritaria, pero en desktop no debe aparecer
scroll: cada pantalla debe caber completa en el viewport.

IDENTIDAD VISUAL
- Verde institucional: #0E642E
- Verde profundo:      #124734
- Dorado:              #AE841F
- Blanco:              #FFFFFF
- Piedra/gris claro:   #C4BEB6
- Tierra:              #4B3D2A
Tipografía: Roboto o similar sans-serif.
Evitar azul en barras, botones o indicadores. Todo en verde/dorado/blanco.

ESTRUCTURA GENERAL
El curso funciona por pantallas internas, no como página larga. Cada pantalla se
muestra/oculta con JS. No usar menú hamburguesa.
- Botón "Iniciar curso" en portada.
- Botón "Volver a lecciones" en pantallas internas.
- Footer fijo/visible con "Anterior" y "Continuar".
- Al cambiar de pantalla, pausar audio/video.

HEADER INTERNO ESTÁNDAR (todas las pantallas internas)
- Izquierda: "< Volver a lecciones"
- Derecha, trazabilidad: nombre de sección · porcentaje confirmado · contador 01 / 10 ·
  barra fina de progreso.
- La barra usa dorado #AE841F sobre base verde o blanca translúcida según el fondo.

BADGE DE SECCIÓN
Badge horizontal verde con punta derecha, estilo etiqueta. Fondo verde oliva/institucional,
texto blanco en mayúsculas. Debe alinearse con el título, no salirse del contenido.
Ej.: "ANTES DE INGRESAR", "VIDEO-CASO", "ACTIVIDAD",
     "ESCUCHA - UNA PAUSA PARA CUIDARTE", "EVALUACIÓN".

PANTALLA 1 — PORTADA
Fondo fotográfico minero. Logo Antioquia Gold blanco arriba. Personas/contratistas
sobrepuestas a la derecha. Título grande "Inducción SST para Contratistas". Texto corto
"Antes de ingresar, reconoce el riesgo y decide seguro." Indicadores "10 min", "80%".
Botón "Iniciar curso" dorado; hover fondo blanco y texto dorado.

PANTALLA DE LECCIONES
Fondo claro/blanco. Logo a color. Barra de progreso inicial 0%. Cuatro lecciones en
grilla 2x2 desktop / una columna mobile:
  1. Antes de ingresar   2. Reconoce el área   3. Video-caso   4. Evaluación
Al hacer clic en cada lección cambia la imagen de apoyo. Botón "Comenzar lección 01".

LECCIÓN 1 — ANTES DE INGRESAR
Fondo claro con `fondo_seccion.webp`. Header interno estándar. Badge "ANTES DE INGRESAR".
Título "Primero verifica." Texto "Antes de entrar al área de trabajo, confirma tres puntos
clave." Lista vertical con iconos: 1. Documentos vigentes 2. EPP completo
3. Autorización de la labor. Imagen `foto-mobile-portada.webp` a la derecha, sin doble
círculo ni borde adicional; la imagen debe mostrarse tal cual. Footer "Anterior"/"Continuar".

PANTALLA VIDEO-CASO
Fondo claro con `fondo_seccion.webp`. Header interno estándar. Badge "VIDEO-CASO".
Izquierda: título "Observa la situación.", texto "Mira el caso y piensa qué harías antes
de continuar.", puntos "Riesgo visible", "Acción segura", "Reporte oportuno".
Derecha: video en mockup tipo celular, vertical 9:16, desde Bunny:
https://player.mediadelivery.net/play/737399/796de072-70c2-49c0-b6c9-b8e0893b0815
No cargar el iframe hasta entrar a la pantalla. Al salir, eliminar el `src` para detener
video y audio. No usar autoplay.

PANTALLA ACTIVIDAD
Toda la pantalla en verde profundo, incluyendo header y footer. Header interno estándar con
texto blanco/dorado. Izquierda: badge, título "Elige la acción segura.", texto "Revisa la
situación y selecciona qué debe hacerse antes de iniciar la labor.", y avatar
`avatar-actividad.webp` debajo del texto.
Derecha: tarjeta clara con la pregunta "Antes de ingresar al área, falta una autorización.
¿Qué haces?" y opciones grandes:
  A. Ingreso rápido y aviso después.
  B. Detengo la labor y reporto.
  C. Pido prestado el permiso de otro equipo.
Botón Continuar sobre verde debe contrastar: blanco con texto verde. Footer verde integrado.

PANTALLA AUDIO / ESCUCHA
Fondo claro con `fondo_seccion.webp`. No usar dos columnas rígidas; composición amplia.
Header interno estándar. Badge "ESCUCHA - UNA PAUSA PARA CUIDARTE".
Kicker "LA VOZ DE LA PREVENCIÓN". Título "Escuchar también es una forma de cuidarte."
Icono grande lineal de audífonos como apoyo visual. Reproductor ancho abajo: botón play,
onda visual, tiempo, texto "Audio de inducción". Archivo `assets/factor_1.mp3`.
Quitar botón "Leer el mensaje". Al cambiar de pantalla, pausar y reiniciar el audio.

PANTALLA EVALUACIÓN
Fondo verde profundo igual que Actividad. Header interno estándar con contraste
blanco/dorado. Badge "EVALUACIÓN". Título "Confirma lo aprendido." Texto "Responde con
calma. Necesitas 80% para aprobar esta inducción." Avatar `avatar_evaluacion.webp`.
Botón "Iniciar evaluación". Footer "Anterior"/"Finalizar". Botones sobre verde deben
contrastar.

COMPORTAMIENTO JS
- Mostrar/ocultar pantallas con `hidden`.
- Variable de pantalla actual o funciones claras para navegar.
- Al entrar al video-caso: asignar `src` desde `data-video-src`.
- Al salir: remover `src` del iframe Bunny.
- Al salir del audio: `pause()`, `currentTime = 0`, quitar estado visual de reproducción.
- En mobile, botones grandes y legibles.
- En desktop, evitar scroll vertical: header, contenido y footer dentro de `100svh`.

ASSETS ESPERADOS
logo-agd · white-logo-agd · exploracion · personas-portada · personas-antiquioa ·
fondo_seccion · foto-mobile-portada · avatar-actividad · avatar_evaluacion · factor_1.mp3
(todos en `assets/`, servidos en .webp; originales en `.assets/`)
```
