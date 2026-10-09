---
description: Crea un curso nuevo copiando una plantilla existente de course_content, lo registra en la BD local y prepara su URL pública para revisión.
---

# /crear-curso

Crea un curso **a partir de una plantilla existente**, conservando su estructura, y lo deja listo
para revisión en local.

Contexto obligatorio: `.claude/manual_desarrollo.md` (§7 modelo de datos, §9 anatomía de
`course_content`, §10 plantillas, §11 URLs públicas). Léelo antes de ejecutar si no está ya en
contexto.

## Entrada

```text
/crear-curso
plantilla: <slug o ruta de la plantilla>
nombre:    <título del curso nuevo>
empresa:   <carpeta de course_content: arismarmato|arissegovia|cursos|emerald|rekonecta|tecnitanques|transprensa>
slug:      <nombre de carpeta del curso nuevo>   (opcional)
modulos:   <cantidad>                            (opcional)
sliders:   <cantidad por módulo>                 (opcional)
usuario:   <emp_unique_id del alumno>            (opcional)
publica:   si|no                                 (opcional, default no)
```

También válido en una línea: `/crear-curso plantilla=gaia-ambiental-v2 nombre="Curso Nuevo"`.

**Toma del contexto de la conversación cualquier dato ya mencionado.** No vuelvas a preguntar algo
que el usuario ya dijo.

### Valores por defecto
- `modulos` / `sliders` ausentes → **los de la plantilla**. No inventes cantidades.
- `slug` ausente → derívalo de `nombre`: minúsculas, sin tildes, espacios → `_`. Confírmalo en el
  resumen final.
- `empresa` ausente → si la plantilla vive en `course_content/<X>/`, propón `X` y dilo
  explícitamente.
- `publica` ausente → `no`.

### Cuándo parar y preguntar
- La plantilla indicada no existe o hay varias que coinciden.
- No hay `empresa` deducible.
- Se pidió asociar `usuario` y ese documento no existe en la BD local.
- El `slug` destino ya existe (**nunca** sobrescribas una carpeta existente).

## Procedimiento

### 1. Identificar y analizar la plantilla
- Localiza la carpeta. Determina la **generación** (§9 del manual): "plana" (`index.php`,
  `modulo.php`, `quiz.php`) o "modulos/" (`modulos/moduloN/sliders/`, `plugins/js/`).
- Cuenta módulos y sliders **en `MODULE_CONFIGS`, no con `ls`**. Localízalo con
  `grep -rn "MODULE_CONFIGS = " <curso>/plugins/js/` — es la **fuente única** de módulos, sliders y
  orden, y según el curso vive en `module-config.js` (gaia-ambiental-v2) o dentro de `main.js`
  (equsera-2026, aris_seguridad_vial_2026). No asumas el archivo.
- **La config y el disco pueden no coincidir** (en `equsera-2026` no coinciden). Manda la config: un
  slider no declarado no se carga. Si detectas la discrepancia, dilo en el resumen; no la
  "arregles" por tu cuenta.
- Anota el slug de contenido que la plantilla usa en sus PHP (llamadas
  `get_course_modules('<slug>')`, `is_previous_module_completed('<slug>', …)`).

### 2. Copiar
- Copia la carpeta **completa** a `course_content/<empresa>/<slug>/`.
- **No reorganices, no renombres, no "mejores" nada.** Misma estructura, mismos archivos.
- Verifica con `git status` que la plantilla original **no** aparece modificada.

### 3. Ajustar contenido

Qué hay que tocar, sin saltarse nada (§9 del manual, "Contrato de una página de curso"):

- **Slug de contenido** dentro de los PHP del curso: `get_course_modules('<slug>')`,
  `is_previous_module_completed('<slug>', …)`.
- **Título visible** de la portada → `nombre`.
- **Título, etiqueta y tiempo estimado de cada módulo**: son variables PHP hardcodeadas
  (`$module_title`, `$module_label`, `$estimated_time`) dentro de cada `modulos/moduloN/moduloN.php`.
  **No salen de la BD** — hay que editarlas archivo por archivo.
- **`MODULE_CONFIGS`**: la fuente única de módulos, sliders y orden.
- **`locales/`**: se copia entero. Revisa los `media.json` (global y los de cada slider): apuntan a
  rutas de archivos concretos y pueden quedar apuntando a media de la plantilla.

Qué **no** hay que tocar, aunque parezca mejorable:
- Las rutas relativas `../../../…` están **contadas por nivel de profundidad**. Copiar a la misma
  profundidad las conserva; cambiarla las rompe todas en silencio.
- Las dos grafías del `require` del helper conviven a propósito. Copia la de la plantilla.
- Las excepciones de nomenclatura (`slider6-actividad` con archivos `slider6.*`, `evaluacion1`,
  `rutaAprendizaje/ruta.php`) se conservan tal cual.

Y verifica que el contrato de página sigue intacto: globals `window.SOFACTIA_BASE_URL` /
`CURRENT_COURSE_CODE` / `CURRENT_MODULO` / `CURRENT_SLIDE_KEY`, `<div id="sliders-container">`
**vacío**, bloque de `localStorage` (`COURSE_CODE`, `USER_ID`, `COURSE_ID`, `MODULE_ID`, `FULLNAME`)
y el orden fijo de scripts.
- Si se pidió otra cantidad de **módulos**: crea/elimina `modulos/moduloN/` copiando el módulo
  vecino como base y actualiza `MODULE_CONFIGS` (entradas `moduloN` con su `orden`).
- Si se pidió otra cantidad de **sliders**: crea/elimina `sliders/sliderN/` (con su `.php`, `.js`,
  `.css`) y actualiza el array `slides[]` del módulo en `MODULE_CONFIGS`.
- No dupliques HTML de slider fuera de `sliders/sliderN/sliderN.php`: `main.js` lo carga por fetch.

### 4. Registrar en la base de datos **local**
Usa la estructura existente (§7 del manual). No inventes tablas ni columnas; inspecciona una fila
real de la plantilla como referencia antes de insertar.

1. `training_master` — tema, si no existe uno reutilizable (`category_es`, `estatus='activo'`,
   `borrado='0'`).
2. `training_details` — la definición:
   `course_title` = `nombre`;
   `url` = `course_content/<empresa>/<slug>/index.php?course_code={{course_code}}`
   (respeta el placeholder literal);
   `theme_id` = el `training_master.id`; `percentage` = el de la plantilla;
   `enable_proctoring` / `enable_signature` / `enable_adaptive_profile` = los de la plantilla
   salvo indicación contraria; `status='1'`, `borrado='0'`.
3. `training_details_themes` — **una fila por módulo**, con `sub_theme_id` apuntando a un
   `training_category_master` (reutiliza los existentes o crea los que falten).
4. `training_course_details` — la instancia: `id_training_detail`, `startdate`/`enddate` vigentes,
   `status='1'`, y `course_code`. El formato real es inicial-mes-inicio + inicial-mes-fin +
   día-inicio + día-fin + `-` + `unique_course_id` (ver `Training.php:1898` del proyecto hermano).
5. `training_course_asistencia` — solo si se indicó `usuario`: resuelve
   `employee_master.id` a partir de `emp_unique_id` y crea la matrícula con ese
   `id_employee` y el `unique_course_id` recién creado.

Todo en la base **local** que corresponda al tenant (`courses_demo` para `cursos`/`localhost`).
No toques bases remotas.

### 5. URL pública (solo si `publica: si`)
- `training_details.enable_public_url = 'yes'` y `code_public = <slug>`.
- `code_public` **no se inventa**: es lo que `Training::extract_public_code()` derivaría del `url`,
  es decir el **tercer segmento** de la ruta = el nombre de la carpeta del curso. Si no coincide con
  el slug, el enlace público no resolverá.
- La URL **no se escribe a mano**: es la que produce
  `AccessService::buildPublicCourseUrl($url, $code_public)`. Calcúlala con ese método o
  reprodúcela exactamente (base + `url` con `{{course_code}}` → `code_public`).
- Si la URL depende de vhost/dominio/HTTPS que no puedes verificar, dilo explícitamente en el
  resumen en vez de prometer un enlace que quizá no resuelva.

### 6. Verificar antes de entregar
- La carpeta nueva existe con la misma estructura que la plantilla.
- `php7.4.33 -l` sin errores en los PHP creados o modificados.
- Cantidades de módulos y sliders correctas, en disco **y** en `MODULE_CONFIGS`.
- Las filas de BD están creadas y relacionadas (`training_details` ↔ `training_course_details` ↔
  `training_course_asistencia`).
- La página del curso abre en local sin warnings de PHP.
- Si es pública, abre sin sesión; si es privada, con el alumno indicado.
- **La plantilla original sigue intacta.**
- Recursos presentes: imágenes, audios, vídeos, `locales/`.

## Entrega

Resume en la respuesta:
- Ruta de la carpeta creada y plantilla usada.
- Módulos y sliders resultantes (y si se tomaron de la plantilla o se ajustaron).
- Filas insertadas, con sus ids (`training_details.id`, `unique_course_id`, `course_code`).
- Alumno asociado, si lo hubo.
- URL de revisión (pública o privada), o la razón por la que no se puede garantizar.
- Cualquier decisión que hayas tomado por defecto, para que el usuario pueda corregirla.

## Prohibido

- Inventar una estructura de curso nueva.
- Modificar la plantilla original.
- Sobrescribir una carpeta de curso existente.
- Construir URLs públicas a mano ignorando `buildPublicCourseUrl()`.
- Insertar en bases remotas o en un tenant distinto del local.
- Dar por creado algo que no se verificó.
