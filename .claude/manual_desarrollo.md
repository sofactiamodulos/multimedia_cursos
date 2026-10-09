# Manual de desarrollo — courses_v2

**Generado:** 2026-08-12 · **Ampliado:** 2026-08-12 (inventario de cursos, contrato de página de
curso, i18n, mecanismo de URL pública, precisiones de BD, tabla de rutas) · **Rama:** `dev` ·
**Base del análisis:** código, configuración y BD local (`courses_demo`) existentes en el
repositorio a esa fecha.

Este documento describe **cómo está hecho el proyecto hoy**, no cómo debería estar hecho. Cuando
propone algo a futuro lo marca explícitamente como **Recomendación**. Cuando algo existe pero no
se pudo determinar con certeza, lo marca como **Requiere revisión**.

Regla que gobierna todo lo demás:

> **No crear por crear.** Primero buscar si ya existe. Reutilizar. Mantener la arquitectura, la
> estructura y las convenciones que ya están.

---

## 0. Aclaraciones previas (cosas que NO existen)

Estas tecnologías **no están en el proyecto**. Si una tarea las presupone, la premisa es falsa:

| Se preguntó por | Realidad |
|---|---|
| Laravel, Artisan, Eloquent | No existe. No hay `artisan`, ni `app/Models` de Eloquent, ni migraciones. |
| Vue, Livewire | No existe. No hay `.vue`, ni `package.json`, ni `node_modules`. |
| Migrations / Seeders / Jobs / Events / Listeners | No existen. Los cambios de esquema se documentan a mano en `app/sql/database_changes.sql` y se aplican con SQL. |
| Traits, Form Requests, API Resources | No existen. Los servicios son clases con **métodos estáticos**, no hay traits ni capa de validación declarativa. |
| API REST versionada | No existe. Hay un único front controller (`router.php`) con acciones tipo `dominio.accion`. |
| Tests automatizados | No existen (hallazgo B2 de `revision_seguridad.md`). |
| Carpeta `courses_content` | El nombre real es **`course_content`** (singular). |
| `cursosdev` | Es el **ambiente demo/desarrollo**. No aparece en el código: existe solo como entrada de DNS local. El tenant real se llama `cursos` → base `courses_demo`. Ver §12. |

**Stack real:** PHP 7.4 (destino) · CodeIgniter 3 aportado por el proyecto hermano
`amatia_capacitacion` · MySQL · jQuery + Bootstrap · Composer solo para `vlucas/phpdotenv`.

> ⚠️ **Entorno local ≠ destino.** El Apache de WAMP sirve con **PHP 8.3.28** y el `php` del PATH
> es 8.2, pero el proyecto apunta a **7.4**. Antes de dar algo por bueno:
> `c:/wamp64/bin/php/php7.4.33/php.exe -l <archivo>`. No usar `str_contains`, `match`, `?->`,
> `catch` sin variable ni promoción de constructor.

---

## 1. Mapa del proyecto

```text
courses_v2/
│
├── router.php              ← front controller único de acciones AJAX/gate
├── index.php  login.php  homember.php  error-404.php  logout.php
│                          ← entry points de URL pública: SHIMS de 2–7 líneas
├── config.php             ← entorno, $baseURL, test_input()
├── ci_instance.php        ← arranca CodeIgniter desde el proyecto hermano
├── functions_helpers.php  ← shim hacia app/helpers/ (cientos de require lo usan)
│
├── app/                   ← TODO el código propio (bloqueado por .htaccess)
│   ├── routes.php         ← tabla de acciones del router
│   ├── controllers/       ← 9 controladores (entrada/salida HTTP)
│   ├── services/          ← 8 servicios (lógica de negocio, métodos estáticos)
│   ├── models/            ← 3 modelos (acceso a tabla, únicos con estado)
│   ├── helpers/           ← funciones globales = fachada de los servicios
│   ├── views/             ← pages/ (login, homember, 404) y proctoring/
│   ├── bootstrap/env.php  ← carga .env
│   ├── config/            ← proctoring.php (credenciales AWS)
│   ├── public/            ← solo logout.php
│   └── sql/               ← changelog de esquema propio de courses_v2
│
├── widgets/sidenav.php    ← único "componente" reutilizable de vista
├── config/environments/   ← local.php / development.php / production.php
├── assets/                ← CSS/JS/imágenes compartidos + assets/S3 (helpers S3)
├── autoservicio/          ← 2 páginas públicas de consulta sin login
├── course_content/        ← CONTENIDO DE LOS CURSOS, por empresa
│   ├── arismarmato/   (7 cursos)  arissegovia/ (8)  cursos/ (4)
│   ├── emerald/  rekonecta/  tecnitanques/  transprensa/   ← VACÍAS: solo index.php
│   └── index.php
├── .script/baseline/      ← baseline.json: snapshot HTTP (status+sha256 por URL) del 2026-07-27,
│                            para detectar regresiones. Denegado por .htaccess.
├── vendor/                ← solo phpdotenv y dependencias
└── _backup/               ← código muerto histórico. NO tocar, NO importar de aquí.
```

El **proyecto hermano** `../amatia_capacitacion` es parte del sistema aunque no de este repo:
aporta CodeIgniter, la conexión a BD por subdominio, el SDK de AWS, los modelos de `training/` y
**el panel de administración donde se crean los cursos**.

---

## 2. Estructura carpeta por carpeta

### `/` (raíz)
- **Responsabilidad:** exponer las URLs públicas estables y el front controller.
- **Contiene:** `router.php` (real) y 5 shims (`index`, `login`, `logout`, `homember`,
  `error-404`) que hacen `require` de `app/`. Más `config.php`, `ci_instance.php` y el shim
  `functions_helpers.php`.
- **Cuándo usarla:** casi nunca. Solo si hay que exponer una URL nueva que no puede vivir bajo
  `router.php` (p. ej. porque decenas de archivos ya la referencian).
- **Qué NO poner:** lógica. Los shims explican en su comentario por qué siguen en la raíz (son
  destino fijo de `check_session()` y de ~40 referencias de cursos). Un archivo nuevo en la raíz
  es servible por HTTP y queda fuera del `.htaccess` de `app/`.

### `app/controllers/`
- **Responsabilidad:** traducir HTTP ↔ dominio. Leer entrada, llamar a un servicio, responder.
- **Contiene:** `AccessGateController`, `ActivityController`, `AdaptiveController`,
  `AutoservicioController`, `CompaniesController`, `DashboardController`, `ProctoringController`,
  `ProgressController`, `TrainingProgressController`.
- **Cuándo usarla:** cada acción nueva de `app/routes.php` apunta acá.
- **Qué NO poner:** SQL, reglas de negocio, HTML extenso. Si un controlador crece con lógica,
  esa lógica va a un servicio.

### `app/services/`
- **Responsabilidad:** la lógica de negocio y **todo el SQL**.
- **Contiene:** `AccessService`, `AdaptiveProfileService`, `AutoservicioService`,
  `CourseDashboardService`, `CourseModuleService`, `CryptoService`, `LoginThrottleService`,
  `SchemaService`.
- **Convención:** clases sin instanciar, **todos los métodos `public static`**, `$CI =& get_instance()`
  adentro cuando hacen falta BD o sesión.
- **Qué NO poner:** `echo`, `header()`, `exit` (excepción histórica: `AccessService` sí redirige,
  porque es el guard de acceso). Nada de HTML.

### `app/models/`
- **Responsabilidad:** acceso a una tabla concreta. Son las **únicas clases con estado**
  (constructor + `$CI`/`$db`).
- **Contiene:** `CourseProgressModel` (progreso público), `ProctoringPhotoModel`,
  `TrainingProgressModel`.
- **Nota:** la mayoría de los servicios **no** usan modelos, hablan con `$CI->db` directamente.
  Es la inconsistencia principal de la arquitectura. **Requiere revisión** — ver §16.

### `app/helpers/`
- **Responsabilidad:** exponer funciones globales que **delegan** en los servicios.
  `functions_helpers.php` es literalmente una fachada: ~45 funciones de 3 líneas.
- **Por qué existe:** cientos de archivos de `course_content/` hacen
  `require('.../functions_helpers.php')` y llaman `check_session()`, `progress_courses()`, etc.
  Renombrar o quitar esas funciones rompe cursos en producción.
- **Qué NO poner:** lógica nueva. Se añade el método al servicio y aquí solo el wrapper. **Y nunca
  un bloque `if(isset($_GET['x']))`** — convertiría en endpoint a toda página que haga require
  (esto ya pasó; ver el comentario del archivo, líneas 251-263).

### `app/views/`
- `pages/` → `login.php`, `homember.php`, `error-404.php`. `proctoring/` → `photo_capture.php`,
  `signature_capture.php`.
- Son PHP+HTML mezclados, con `<?= ?>` y bloques de lógica de presentación arriba.
- **Qué NO poner:** consultas SQL. Las vistas llaman a funciones del helper.

### `app/bootstrap/`, `app/config/`, `app/sql/`, `app/public/`
- `bootstrap/env.php`: carga `.env` con phpdotenv y define `env()`.
- `config/proctoring.php`: constantes AWS del proctoring (**distintas** de las de
  `assets/S3/s3_constants.php`, que son para fotos de perfil; el comentario lo advierte).
- `sql/database_changes.sql`: changelog **manual** de los cambios de esquema propios.
- `public/`: solo `logout.php` (los otros 10 archivos se eliminaron por muertos).

### `widgets/`
- Único componente de vista reutilizable: `sidenav.php`, incluido por `homember.php`.
- **Cuándo usarla:** un bloque de UI compartido por más de una vista.

### `config/environments/`
- `local.php`, `development.php`, `production.php` → `debug`, `display_errors`,
  `error_reporting`. `config.php` elige según `APP_ENV` del `.env`, y si no hay, infiere por
  `HTTP_HOST` cayendo a `production` (default seguro).

### `assets/`
- Compartido de todo el sitio: `css/`, `js/`, `images/`, `icon/`, `webfonts/`, `rs-plugin/`.
- `assets/S3/`: `s3_helper.php`, `cloud_file_helper.php`, `s3_constants.php` (fotos de perfil).

### `autoservicio/`
- Dos páginas **públicas sin login** (`autoservicio_marmato`, `autoservicio_segovia`): el alumno
  consulta sus cursos con la cédula. Consumen `router.php?action=autoservicio.coursesList`.
- **Regla:** todo lo que se pinte aquí pasa por `escapeHtml()` (ya definido en cada página) y el
  contacto llega **enmascarado desde el servidor**, nunca en claro.

### `course_content/` → ver §9, es el corazón del proyecto.

### `.script/`
- `baseline/baseline.json`: snapshot HTTP (status + sha256 por URL) tomado el 2026-07-27, para
  comparar antes/después de un refactor y detectar regresiones. Denegado por su propio `.htaccess`.
- **Requiere revisión:** las URLs del baseline apuntan a una ruta antigua (`amatia/sofactia_cursos/`),
  así que hay que regenerarlo antes de fiarse de una comparación.

### `_backup/`
- Código histórico. **No se lee, no se importa, no se "arregla".** Está fuera del alcance de todo.

---

## 3. Arquitectura y flujos reales

No hay un único flujo: hay **tres**, y hay que saber en cuál se está.

### Flujo A — Página navegable (el más común)
```text
Navegador → /homember.php (shim) → app/views/pages/homember.php
          → funciones del helper → Service → $CI->db → HTML
```
La vista es la que orquesta. No hay controlador.

### Flujo B — Acción AJAX / gate (el moderno)
```text
JS del curso → router.php?action=dominio.accion
             → app/routes.php (¿requiere sesión?)
             → Controller::accionAction()
             → Service (o Model) → $CI->db
             → JSON (echo json_encode) + exit
```
Es el flujo al que debe ir **toda funcionalidad nueva**.

### Flujo C — Página de curso en `course_content/`
```text
Navegador → course_content/<empresa>/<curso>/index.php
          → require('.../app/helpers/functions_helpers.php')
          → check_session() | resolve_course_access()
          → check_permission_employee_course($course_code)  ← decide el acceso
          → get_course_modules() / progress_courses() ...
          → HTML del curso; el JS persiste por router.php
```

### Dónde va cada cosa

| Qué | Dónde | Nunca en |
|---|---|---|
| Lógica de negocio | `app/services/` | vistas, `course_content/`, helper |
| SQL | `app/services/` (o `app/models/`) | vistas, controladores, JS |
| Validación de entrada | al inicio del método del controlador | el servicio asume datos ya tipados |
| Identidad del alumno | **siempre de la sesión** (`employee_data.user_id`) | nunca de `$_POST`/`$_GET` |
| Autorización a un curso | `check_permission_employee_course()` / `resolve_course_access()` | comprobaciones ad-hoc |
| Transformación para pintar | la vista, o un método `build*` del servicio | el modelo |
| Respuesta JSON | controlador (`header('Content-Type: application/json'); echo; exit;`) | servicio |
| Manejo de errores JSON | `ProctoringController::runJsonAction()` es el patrón de referencia | `error_reporting(0)` global |
| Lógica de front | `plugins/js/` del curso, o `assets/js/` si es global | inline en el PHP |

---

## 4. Catálogo de métodos (busca aquí ANTES de escribir uno nuevo)

Formato: **método** → qué hace · cuándo reutilizar · cuándo no.

### `AccessService` — acceso, matrícula, URLs públicas
| Método | Responsabilidad | Reutilizar / No usar |
|---|---|---|
| `hasSession()` | ¿hay sesión? Devuelve `bool`. | **Úsalo en endpoints JSON.** |
| `checkSession()` | Exige sesión; si no hay, `header(Location: login.php); exit;`. | Solo en **páginas navegables**. No en AJAX: mata el JSON con un 302. |
| `checkPermissionEmployeeCourse($code, $setcookie=true)` | Valida matrícula y devuelve `unique_course_id`; si no, redirige a `error-404?code_error=501`. | Es **el** control de acceso a curso. No reimplementar la consulta. |
| `getUniqueCourseIdForEmployee($code, $employee_id)` | Igual pero **sin redirigir**: devuelve `0`. | Cuando necesitas decidir sin cortar la ejecución (endpoints). |
| `resolveCourseAccess($code)` | Resuelve público vs privado. Devuelve `is_public, unique_course_id, user_id, fullname`. | **Punto de entrada estándar de una página de curso.** |
| `isCoursePublic($code)` | ¿`enable_public_url='yes'` y `code_public` coincide? Cacheado. | Antes de exponer nada sin login. |
| `buildPublicCourseUrl($url, $code_public, $enable)` | Arma la URL pública sustituyendo `{{course_code}}`. | **Única** forma válida de construir una URL pública. |
| `buildCourseAccessGateLink(...)` | Antepone el gate de proctoring/firma/perfilamiento. | Al enlazar un curso con esos requisitos. |
| `wrapWithSignatureGate($ucid, $code, $url)` | Envuelve una URL con el gate de firma. | Igual que el anterior. |
| `isSafeRedirectTarget($url)` | Evita open redirect. | **Siempre** antes de un `header('Location: '.$dato_del_usuario)`. |

### `CourseDashboardService` — listados y progreso del alumno
| Método | Responsabilidad | Notas |
|---|---|---|
| `getMyCoursesList()` | Cursos vigentes del alumno con progreso, imagen, categoría y enlaces. | Fuente de las tarjetas de `homember`. |
| `getEstadisticasGenerales()` | Panel de estadísticas del sidenav. | Una sola consulta; no llamar en bucle. |
| `getSessionCourseProgress($code)` | % del curso, alumno **desde sesión**. | Lo consume `dashboard.courseProgress`. |
| `getEvaluationProgressByCourse($CI,$ucid,$emp)` | Nota/avance de evaluación. **Memoizado**. | Reutilizar siempre esta, no la privada `compute*`. |
| `getProgressCourses($code,$module_id)` | Progreso por módulo. Devuelve fila sintética de ceros si no hay datos. | Ojo: “sin datos” y “cero real” se ven igual. |
| `getPorcentage($code)` | % mínimo de aprobación. `false` si no existe. | |
| `getSurveyLink()`, `getEvaluationLink($ucid)` | Enlaces de encuesta y evaluación. | |
| `imageProfile($code)` | Imagen del curso. | |
| `buildCourseAccessLink(array $course)` | Arma el enlace final de una tarjeta (gate incluido). | Reutilizar en cualquier listado nuevo. |
| `getCategoriesEnvironments()` | Categorías activas (§12). | Devuelve `[]` si la tabla no existe en el tenant. |

### `CourseModuleService` — módulos, orden y desbloqueo secuencial
| Método | Responsabilidad |
|---|---|
| `getCourseModules($course_code)` | Módulos del curso (BD y, si no, leyendo la carpeta de contenido). |
| `getModulePosition($code,$module_id)` | Posición del módulo en el orden. |
| `getModuleProgressValue($asis,$ucid,$module_id)` | % de un módulo. |
| `getProgressMap($code,$asis,$ucid,...)` | Mapa `modulo => estado` del alumno. |
| `getProgressMapPublic($code,...)` | Igual para invitado (tabla `training_progress_public`). |
| `isPreviousModuleCompleted(...)` / `...Public(...)` | **Bloqueo secuencial.** Reutilizar siempre; no reimplementar el criterio. |
| `getModuleImageDescription($idx)` | Imagen/descripción por índice. |
| `checkModuleProgressEntry($ucid,$modules)` | Garantiza filas de progreso. |

### `AdaptiveProfileService` — perfilamiento adaptativo (13 métodos)
Config por curso (`training_details.adaptive_profile_rules`), asignación por alumno
(`training_course_profile_assignment`) y progreso por slide (`training_slide_progress`).
Entrada estándar: **`getContext($course_code,$employee_id,$unique_course_id)`**.
Filtros: `getAllowedLessonIds()`, `getAllowedSlideKeys()`, `isModuleAllowedForEmployeeCourse()`.
Escritura: `saveProfileAssignment()`, `saveSlideProgress()`, `calculateSlideProgress()`.

### Servicios de apoyo
| Servicio | Métodos | Uso |
|---|---|---|
| `SchemaService` | `hasColumn()`, `hasTable()`, `selectOrDefault()` | **Obligatorio** antes de tocar una columna que no existe en todos los tenants. Cachea por request a propósito (un `ALTER` surte efecto en la petición siguiente). |
| `CryptoService` | `simpleCrypt($s,'e'\|'d')` | Ofusca ids en URLs (base64: **siempre** `rawurlencode()` al meterlo en una URL). No es seguridad. |
| `LoginThrottleService` | `isBlocked()`, `record()`, `minutesUntilRetry()` | Límite de intentos de login (5/documento, 30/IP, 15 min). |
| `AutoservicioService` | `getCoursesForEmployee()`, `maskEmail()`, `maskPhone()` | Autoservicio público. El enmascarado es **idempotente** a propósito. |

### Helpers globales (`app/helpers/functions_helpers.php`)
Son la fachada. Equivalencias más usadas: `check_session()`, `has_session()`,
`check_permission_employee_course()`, `resolve_course_access()`, `get_course_modules()`,
`progress_courses()`, `is_previous_module_completed()`, `get_my_courses_list()`,
`estadisticas_generales()`, `__my_simple_crypt__()`, `image_profile()`.
`proctoring_helpers.php`: `check_proctoring_photo()`, `check_proctoring_signature()`,
`create_proctoring_table()`.

**Desde `course_content/` se llaman las funciones del helper, no las clases.** Es la convención
real y mantiene los cursos desacoplados de los nombres de clase.

### Modelos — los tres únicos

| Modelo | Métodos | Nota |
|---|---|---|
| `TrainingProgressModel` | `find()`, `replaceRow()`, `getAdaptiveModuleAverage()`, `getOverallAverage()`, `updateCourseAsistenciaAverage()` | `replaceRow()` hace select→delete→insert (no es un `REPLACE` de MySQL). |
| `CourseProgressModel` | `getPublicProgress()`, `savePublicProgress()` | `savePublicProgress()` sí usa `REPLACE` atómico sobre `training_progress_public`. |
| `ProctoringPhotoModel` | `findExistingSignatureUrl()`, `updateSignatureUrl()`, `hasAnyRecord()`, `insertSignature()`, `insertUpload()` | |

### Dos métodos privados que conviene conocer

- `CourseDashboardService::resolveContentCodeFromUrl()` — deduce el slug de contenido desde
  `training_details.url` para calcular progreso ponderado multi-módulo. **Su regex solo casa
  `course_content/cursos/...`** (ver §16).
- `CourseModuleService::getModulesFromContentFolder()` — **fallback**: si un curso no tiene filas en
  `training_details_themes`, escanea `course_content/cursos/<slug>/modulos/moduloN/sliders/` en disco
  y sintetiza los módulos con `id = N+1`. Explica por qué un curso puede "funcionar" sin estar bien
  registrado en BD — y por qué eso engaña al revisar.

### Tabla de rutas — las 18 acciones de `router.php`

Míralas antes de crear un endpoint: puede que ya exista. Fuente: `app/routes.php` (cada `false` lleva
en el archivo un comentario que lo justifica; léelo antes de cambiarlo).

| Acción | Controlador::método | Sesión |
|---|---|---|
| `activity.updateProgress` | `ActivityController::updateProgressAction` | sí |
| `activity.reinforcement` | `ActivityController::reinforcementAction` | sí |
| `companies.regions` | `CompaniesController::getRegions` | no |
| `dashboard.courseProgress` | `DashboardController::courseProgressAction` | no |
| `autoservicio.coursesList` | `AutoservicioController::coursesListAction` | no (público por diseño) |
| `adaptive.context` | `AdaptiveController::contextAction` | no |
| `adaptive.slideContext` | `AdaptiveController::slideContextAction` | no |
| `adaptive.diagnostic` | `AdaptiveController::diagnosticAction` | **sí** (es una página) |
| `proctoring.saveSignature` | `ProctoringController::saveSignatureAction` | no (comprueba dentro) |
| `proctoring.upload` | `ProctoringController::uploadAction` | no (comprueba dentro) |
| `proctoring.photoCapture` | `ProctoringController::photoCaptureAction` | **sí** (es una página) |
| `proctoring.signatureCapture` | `ProctoringController::signatureCaptureAction` | **sí** (es una página) |
| `access.preEvaluationGate` | `AccessGateController::preEvaluationGateAction` | no |
| `access.courseGate` | `AccessGateController::courseAccessGateAction` | no |
| `progress.get` / `progress.update` | `TrainingProgressController::getAction` / `updateAction` | no |
| `progress.getPublic` / `progress.updatePublic` | `ProgressController::getPublicAction` / `updatePublicAction` | no (curso público) |

El patrón está claro: **`true` = página navegable** (sin sesión debe ir a `login.php`), **`false` =
endpoint JSON** que comprueba la sesión adentro con `has_session()` y responde JSON. Respétalo.

### Del proyecto hermano — lo que hay que conocer

No se toca desde aquí, pero es donde se crean los cursos
(`amatia_capacitacion/application/modules/training/`):

| Método | Archivo | Para qué |
|---|---|---|
| `Training::CapacitacionesDetalles()` | `controllers/Training.php:276` | CRUD de `training_details`: escribe `url`, `category_id`, `enable_public_url`, `code_public`. |
| `Training::extract_public_code()` | `Training.php:236` (privado) | Deriva `code_public` del `url` (3.er segmento). Ver §11. |
| `Training::create_event_and_schedule()` | `Training.php:1867` | Crea la fila de `training_course_details` y **genera el `course_code`**. |
| `Training_model::getTrainingModules()` | `models/Training_model.php` | Los módulos que consume `CourseModuleService` de este repo. |
| `Category::saveCategory()` / `is_tenant_allowed()` | `controllers/Category.php` | Categorías; el segundo es el candado a `courses_demo` (§12). |

---

## 5. Dónde crear cada cosa nueva

| Necesito… | Dónde | Cómo nombrarlo | Reutilizar antes | Evitar |
|---|---|---|---|---|
| Endpoint AJAX | línea en `app/routes.php` + método en un controlador | acción `dominio.accion` (camelCase); método `accionAction()` | ¿ya hay una acción parecida? | crear un `.php` suelto en la raíz o en `course_content/` |
| Lógica de negocio | `app/services/XxxService.php` | `PascalCase` + sufijo `Service`; métodos `public static` en `camelCase` | los 8 servicios de §4 | poner la lógica en la vista o en el controlador |
| Acceso a una tabla nueva con estado | `app/models/XxxModel.php` | sufijo `Model` | mirar si un servicio ya consulta esa tabla | crear un modelo por consulta suelta |
| Función global para cursos | wrapper en `app/helpers/functions_helpers.php` | `snake_case` | ver la lista de §4 | meter la lógica en el helper |
| Página navegable | `app/views/pages/` + shim de 7 líneas en la raíz **solo si** la URL debe ser estable | `kebab` o palabra simple | `homember.php` como referencia | crear la vista directamente en la raíz |
| Componente de UI compartido | `widgets/` | `snake_case.php` | `sidenav.php` | duplicar el bloque en dos vistas |
| Estilos/JS globales | `assets/css/`, `assets/js/` | — | — | CDN sin `integrity` (ver M8) |
| Estilos/JS de un curso | `<curso>/plugins/js/`, `<curso>/plugins/css/` | igual que los existentes | `main.js`, `tracking.js` | tocar `assets/` global por un curso |
| Cambio de esquema | SQL a mano + entrada en `app/sql/database_changes.sql` | — | — | asumir que todos los tenants tienen la columna: usar `SchemaService` |
| Curso nuevo | `course_content/<empresa>/<slug>/` copiando una plantilla | ver §9-§10 | **siempre una plantilla** | inventar una estructura nueva |

---

## 6. Convenciones reales del proyecto

**Así se hace hoy** (no son propuestas):

- **Clases:** `PascalCase`, un archivo por clase, sufijo `Service` / `Controller` / `Model`.
- **Métodos de servicio:** `public static function camelCase()`.
- **Acciones de controlador:** `camelCaseAction()`. La ruta se llama `dominio.accion`.
- **Funciones de helper:** `snake_case()`. Son wrappers.
- **Variables:** `snake_case` en helpers/vistas/cursos (`$course_code`, `$unique_course_id`),
  `camelCase` puntual en código nuevo de controladores. Predomina `snake_case`.
- **Archivos de curso:** carpeta en `snake_case` o `kebab-case` (conviven ambos; ver §9), y dentro
  `modulos/moduloN/`, `sliders/sliderN/sliderN.php`.
- **Tablas:** prefijo `training_` para el dominio de cursos. Campos en `snake_case` inglés
  (`unique_course_id`, `id_employee`) con **excepciones en español** (`category_es`, `estatus`,
  `borrado`). Estados: `status`/`estatus` con `'1'`/`'activo'`; borrado lógico con
  `borrado='0'` o `deleted_at IS NULL` según la tabla — **no son uniformes, hay que mirar cada una**.
- **Idioma:** comentarios y textos de UI en español. Nombres de código, mezcla.
- **Comentarios:** el proyecto documenta **el porqué**, sobre todo cuando algo parece un error y
  no lo es. Mantén ese estilo: si tomas una decisión no obvia, explícala en el archivo.

---

## 7. Módulo de cursos — modelo de datos

Cadena real (`training_master → training_details → training_course_details → asistencia`):

| Tabla | Es | Claves |
|---|---|---|
| `training_master` | **Tema** del catálogo | `id`, `category_es`, `estatus`, `borrado` |
| `training_details` | **Definición del curso** (el contenido) | `id`, `course_title`, **`url`**, `theme_id`, `category_id`, `percentage` (% mínimo), `enable_proctoring`, `enable_signature`, `enable_public_url`, `code_public`, `enable_adaptive_profile`, `adaptive_profile_rules` |
| `training_details_themes` | **Módulos** del curso | `training_id` → `training_master.id`, `sub_theme_id` → `training_category_master.id` |
| `training_category_master` | Catálogo de nombres de módulo | `id`, `option_es` |
| `training_course_details` | **Instancia/convocatoria** | `unique_course_id` (PK), **`course_code`**, `id_training_detail`, `startdate`, `enddate`, `status` |
| `training_course_asistencia` | **Matrícula** (alumno ↔ instancia) | `unique_course_id`, `id_employee`, `final_percentage` |
| `training_progress` | Progreso por módulo del alumno | `asistencia_id`, `unique_course_id`, `module_id`, `progress`, `progress_object`, `progress_modulo` |
| `training_progress_public` | Progreso de invitados (compartido, sin alumno) | `course_code`, `module_id`, `progress`, **`UNIQUE(course_code, module_id)`** |
| `training_activity_results` | Resultado de actividades | `user_id`, `course_id`, `module_id`, `activity_id`, `result` |
| `progress_reinforcement_activities` | Quizzes de refuerzo | `user_id`, `course_id`, `module_id`, `activity_id`, `total_cuestions`, `correct`, `percentage` |
| `training_slide_progress` | Progreso por slide (adaptativo) | `asistencia_id`, `course_code`, `slide_key` |
| `training_course_profile_assignment` | Perfil adaptativo asignado | `employee_id`, `unique_course_id`, `profile_codes_json` |
| `training_course_category_environment` | **Categorías** (§12) | `id`, `key_string`, `category_es`, `estatus`, `deleted_at` |
| `course_slide_catalog` | Catálogo de slides | `course_url_key`, `capsula_key`, `slide_key`, `slide_order` |
| `proctoring_photos` | Evidencia de foto/firma | `employee_id`, `course_id`, `image_url`, `signature_url` |
| `employee_master` | Alumno | `id` (=`id_employee`), `emp_unique_id` (documento), `nivel1` (empresa), `cellphone_no` (**es la contraseña**) |

**Dos códigos que se confunden constantemente:**
- `training_course_details.course_code` → código de **matrícula** (`MM2323-346`, `ARIS-00088`).
  Se genera como inicial-mes-inicio + inicial-mes-fin + día-inicio + día-fin + `-` + `unique_course_id`
  (`Training.php:1898`); las de forma `ARIS-000NN` vienen de altas manuales (`way_created='Manual'`).
- `training_details.code_public` → código de la **URL pública**, normalmente **igual al slug de
  la carpeta** del curso. Es el que viaja en el enlace sin login.

**`training_details.url`** es la unión con el disco. Formato real:
`course_content/<empresa>/<slug>/index.php?course_code={{course_code}}`.
El placeholder `{{course_code}}` lo sustituye el código al armar el enlace (§11).

### Cosas del modelo que sorprenden y hay que saber

**No hay ninguna columna de empresa en las tablas de curso.** La separación por empresa es *una base
de datos por empresa*, elegida por subdominio (§13). Dentro de un tenant, la dimensión
empresa/regional vive en el **usuario**: `employee_master.nivel1` → `siso_regionales.id`. La carpeta
`course_content/<empresa>/` es solo convención de archivos. Si necesitas filtrar "cursos de la
empresa X", el filtro va por el usuario, no por el curso.

**No hay claves foráneas.** La única `FOREIGN KEY` real en todo el esquema versionado es
`training_attachments.training_id → training_details.id ON DELETE CASCADE`. Todo lo demás son
relaciones lógicas con índices sueltos: nada impide dejar filas huérfanas, y **nada las borra en
cascada**. Al insertar a mano, el orden correcto lo garantizas tú.

**`training_progress.asistencia_id` contiene el id del EMPLEADO**, no `asistencia_unique_id` pese al
nombre. Se ve en `checkPermissionEmployeeCourse()` y en `getMyCoursesList()`, que le pasan
`$id_employee`. Es la trampa más cara del esquema.

**`training_progress_public` tiene `UNIQUE(course_code, module_id)`**: una sola fila por curso y
módulo, sin identidad de visitante. Todos los invitados comparten y se pisan el progreso. Es
intencional, no un bug.

**La cadena de joins que usa todo el proyecto** (`getMyCoursesList`, `checkPermissionEmployeeCourse`,
`AutoservicioService`), cópiala tal cual en cualquier consulta nueva:

```text
training_master tm
  → training_details td            (td.theme_id = tm.id)
  → training_course_details tcd    (tcd.id_training_detail = td.id)
  → training_course_asistencia lca (lca.unique_course_id = tcd.unique_course_id)
  → training_progress tp           (tp.unique_course_id = tcd.unique_course_id
                                    AND tp.asistencia_id = <id_employee>)
filtrado por: tcd.startdate <= hoy AND tcd.enddate >= hoy
              AND tcd.status = '1' AND td.borrado = '0'
```
Olvidar el filtro de fechas es la causa habitual de "el curso no me aparece en homember".

### De dónde sale el esquema (y qué no está)

No hay dump ni migraciones. Las fuentes son:
- `amatia_capacitacion/application/modules/training/sql/training-tables.sql` — los `CREATE`.
- `.../training/database_changes.sql` y `courses_v2/app/sql/database_changes.sql` — los changelogs.

> ⚠️ `training-tables.sql:762` contiene una versión **obsoleta** de `training_progress` (MyISAM, con
> `schedule_id`). La forma viva es la de `training/database_changes.sql` más los `ALTER` posteriores.
> No tomes ese `CREATE` como referencia.

**Tablas sin `CREATE TABLE` en ningún repositorio** — sus columnas están inferidas de las consultas
y **solo se confirman con `DESCRIBE`**: `training_slide_progress`,
`training_course_profile_assignment`, `training_activity_results`,
`progress_reinforcement_activities`, `employee_master`, `siso_regionales`, `profile_photo_course`.
`proctoring_photos` y `login_attempts` se crean **en tiempo de ejecución**
(`proctoring_helpers.php:71` y `LoginThrottleService.php:31`).

---

## 8. Ciclo de vida de un curso

1. **Contenido** — carpeta en `course_content/<empresa>/<slug>/` (copiada de una plantilla).
2. **Definición** — fila en `training_details` con `url` apuntando a esa carpeta, `%` mínimo,
   y los flags (`enable_*`).
3. **Módulos** — filas en `training_details_themes` (una por módulo), cada una apuntando a un
   `training_category_master`.
4. **Instancia** — fila en `training_course_details` con fechas de vigencia y `course_code`.
5. **Matrícula** — fila en `training_course_asistencia` por alumno.
6. **Progreso** — lo escribe el JS del curso vía `router.php` en `training_progress`
   (o `training_progress_public` si es invitado).
7. **Publicación** — `enable_public_url='yes'` + `code_public` (§11).

Los pasos 2-5 se hacen **desde el panel de `amatia_capacitacion`** (módulo `training`). Este
repositorio solo **consume** esos datos. Insertar a mano en la BD local es válido para pruebas,
pero es un atajo, no el flujo de producto.

---

## 9. `course_content/` — anatomía real

```text
course_content/<empresa>/<slug_del_curso>/
```
- **Empresa** = carpeta de primer nivel. Hay 7, pero **solo 3 tienen cursos**: `arismarmato` (7),
  `arissegovia` (8) y `cursos` (4). `emerald`, `rekonecta`, `tecnitanques` y `transprensa` contienen
  **únicamente `index.php`** — están preparadas pero vacías. `cursos` es el ambiente
  demo/desarrollo (§12).
- **La carpeta de empresa es solo convención de sistema de archivos.** No hay ninguna columna de
  empresa en las tablas de curso: la separación real es *una base de datos por empresa* (§13). Nada
  en el código deduce la empresa a partir de esta carpeta.
- **Curso** = carpeta de segundo nivel; su nombre es el **slug** que aparece en
  `training_details.url` y es también `code_public` (§11 explica por qué: se deriva del `url`).
- Cada carpeta de empresa tiene el mismo `index.php` (490 bytes) que redirige a `homember.php` si
  hay sesión. `arismarmato/` y `arissegovia/` tienen además un `upload.php` — ver el aviso de §16.
- Escala: **~7.700 archivos, ~1,5 GB**. Casi todo es media (1.828 png, 1.276 webp, 995 mp3, 936 jpg);
  solo **185 archivos PHP** en los 20 cursos.

### Inventario real de cursos

| Empresa | Curso | Gen. | Módulos · sliders |
|---|---|---|---|
| `arismarmato` | `MineriaSuperficie` | A | `modulo.php` de **355 KB** (el mayor) |
| | `aris-sagrilaft-ptee-qhs-segovia` | A | |
| | `aris_marmato_sagrilaft_ptee` | A | |
| | `aris_marmato_seguridad_vial` | A | 108 MB |
| | `aris_mining_sagrilaft_ptee_marmato` | A | 96 MB / 754 archivos |
| | `induccion_visitantes_foto_perfil` | A | sin `introduccion.php` |
| | `induccionvisitantes` | A | sin `introduccion.php` |
| `arissegovia` | `aris_riesgo_electrico` | A | **solo `index.php`** (sin js/css propios) |
| | `aris_sagrilaft_ptee_segovia` | A | 92 MB / 758 archivos — plantilla legado de referencia |
| | `aris_segovia_induccion_qhs_sst` | A | |
| | `aris_segovia_sagrilaft_ptee` | A | |
| | `aris_segovia_seguridad_vial` | A | 109 MB |
| | `induccionV3` | A | sin `introduccion.php` |
| | `induccion_visitantes_segovia_2024` | A | con `introduccion2.php` |
| | `induccion_visitantes_segovia_2025` | A | con `introduccion2.php` |
| `cursos` | `aris_segovia_seguridad_vial` | A | copia legado, 132 MB / 407 archivos |
| | `aris_seguridad_vial_2026` | **B** | modulo0-4 → 3 · 4 · 2 · 1 · 1 |
| | `equsera-2026` | **B** | modulo0-3 → 7 · 14 · 1 · **0** |
| | `gaia-ambiental-v2` | **B** | modulo0-3 → 3 · 12 · 1 · **0**, + `evaluacion1` |

Lo que hay que leer de esta tabla: **la generación B son 3 cursos y todos viven en `cursos`.** Los
otros 17 son generación A. Un "curso moderno" fuera de `cursos/` no existe todavía — y §16 explica
por qué eso importa (`resolveContentCodeFromUrl()` solo casa `course_content/cursos/`).

Los `modulo3` de `equsera-2026` y `gaia-ambiental-v2` **no tienen carpeta `sliders/`**: son módulos
declarados con un `.php` pelado. No es un error de copia, es su estado real.

### Existen DOS generaciones de curso. Hay que identificar cuál se está tocando.

**Generación A — "plana" (legado, la mayoría)**
```text
<curso>/
├── index.php          ← portada: check_session + check_permission_employee_course
├── introduccion.php   modulo.php   quiz.php
└── assets/{js,css,img,audio,doc,actividades,bootstrap,cdn}
```
JS: `interactividad.js`, `trackingmanagern3.js`. Persisten por
`../../../router.php?action=dashboard.courseProgress`.
Ejemplos: `arissegovia/aris_sagrilaft_ptee_segovia`, `arismarmato/*`.

**Generación B — "modulos/" (moderna)**
```text
<curso>/
├── index.php  config.php  ci_instance.php  course_access.php
├── inicio/          ← dashboard del curso (inicio.php/.js/.css)
├── modulos/
│   ├── modulo0/ … moduloN/
│   │   ├── moduloN.php  moduloN.js  moduloN.css
│   │   └── sliders/
│   │       ├── slider1/{slider1.php,.js,.css,img/}
│   │       └── actividadN/{actividadN.php,.js,.css}
│   └── evaluacion1/evaluacion1.php
├── rutaAprendizaje/  glosario/  quiz/  navegacionInferior/
├── locales/{media.json, en/{auto.json,manual.json}, README.md}
├── plugins/{js,css,libs,partials}
└── assets/{img,audio,video,svg}
```
JS de `plugins/js/`: `main.js` (arma el módulo), `tracking.js` (persiste por
`router.php?action=progress.get/update` y `progress.getPublic/updatePublic`),
`spa-navigation.js`, `dom-translator.js` + `language-switcher.js` (traducciones),
`activity-*.js`, `accessibility-widget.js`.

### Contrato de una página de curso (generación B)

Esto es **lo que hay que replicar al copiar una plantilla**, y lo que se rompe si se toca sin
entenderlo. No está impuesto por ningún framework: es convención, y por eso hay que respetarla a
mano.

**`index.php` (portada del curso)**
1. `require` del helper. Conviven **dos grafías** según el curso — `'../../../functions_helpers.php'`
   (el shim de la raíz) y `'../../../app/helpers/functions_helpers.php'` (directo). Ambas funcionan;
   copia la de la plantilla, no la "unifiques" de paso.
2. `$access = resolve_course_access($course_code)` a partir de `?course_code=` → devuelve
   `is_public`, `unique_course_id`, `user_id`, `fullname`.
3. Título del curso desde `get_course_modules($course_code)[0]`; progreso vía
   `get_read_progress_user()`.
4. HTML de portada + `<select>` de idioma, y un `<script src=".../dom-translator.js"
   data-endpoint=".../translate.php">`.
5. Un IIFE al final escribe la **identidad de tracking en `localStorage`** y "COMENZAR" navega a
   `inicio/inicio.php?course_code=…`.

**`modulos/moduloN/moduloN.php` (página de módulo)** — las cinco piezas obligatorias:

| Pieza | Qué es | Si falta… |
|---|---|---|
| Globals en `<head>` | `window.SOFACTIA_BASE_URL`, `CURRENT_COURSE_CODE`, `CURRENT_MODULO` (literal `'moduloN'`), `CURRENT_SLIDE_KEY` | `main.js` y `tracking.js` no saben qué módulo es |
| `<div id="sliders-container">` **vacío** | dónde `main.js` inyecta los sliders | la página queda en blanco |
| Bloque `localStorage` | `COURSE_CODE`, `USER_ID`, `COURSE_ID`, `MODULE_ID`, `FULLNAME` | el tracking no persiste (cae en el modo "ni servidor ni público") |
| Orden de scripts **fijo** | jquery → bootstrap → `tracking.js` → `sessvars.js` → `lumi-plugin.js` → `audio-reader.js` → `main.js` → `interactividad.js` → `cap.js` → `route-layout.js` → `navegacion.js` → `moduloN.js` | errores de "undefined" difíciles de diagnosticar |
| `plugins/partials/route-sidebar.php` | incluido con `$sidebarBase` / `$activeNav` / `$sidebarCollapsed` | se pierde la navegación lateral |

Referencia viva: `course_content/cursos/equsera-2026/modulos/modulo1/modulo1.php`
(globals en líneas 28-31, contenedor en la 93, `localStorage` en 171-175, scripts en 155-168).

> **El título, la etiqueta y el tiempo estimado del módulo son variables PHP hardcodeadas**
> (`$module_title`, `$module_label`, `$estimated_time`) dentro de cada `moduloN.php`. **No vienen de
> la base de datos.** Al copiar un curso hay que editarlas archivo por archivo; no hay un sitio
> único donde cambiarlas.

### `MODULE_CONFIGS` — la fuente única de módulos y sliders

Declara módulos, sliders y orden. `main.js` recorre `MODULE_CONFIGS[moduloN]` y trae cada
`sliderN.php` por `fetch` hacia `#sliders-container`. **No hay ninguna tabla de sliders en la BD.**

**No siempre vive en el mismo archivo:**

| Curso | `MODULE_CONFIGS` en | Forma | `course_access.php` |
|---|---|---|---|
| `cursos/gaia-ambiental-v2` | `plugins/js/module-config.js:12` | objeto rico: `orden`, `time`, `slides[]` con `title`, `isActivity`, `evaluationNumber`, `init`; + `getOrderedModuleKeys()` | sí |
| `cursos/equsera-2026` | `plugins/js/main.js:12` | array plano de `{id, path}` | no |
| `cursos/aris_seguridad_vial_2026` | `plugins/js/main.js:13` | array plano de `{id, path}` | no |

`gaia-ambiental-v2` es el único que extrajo la config a su propio archivo, el único con `orden`
explícito y el único con `course_access.php`. Por eso es la plantilla de referencia (§10).
**Antes de tocar módulos o sliders, localiza `MODULE_CONFIGS` con un grep, no asumas el archivo:**

```bash
grep -rn "MODULE_CONFIGS = " course_content/cursos/*/plugins/js/
```

> ⚠️ **`MODULE_CONFIGS` puede estar desincronizado del disco.** En `equsera-2026` el disco tiene 7
> sliders en `modulo0` y 14 en `modulo1`, pero la config declara 5 y 12 (con `slider2` comentado), y
> `modulo2`/`modulo3` **no aparecen en absoluto** pese a existir sus carpetas. **Manda la config, no
> el disco**: un slider que no esté declarado sencillamente no se carga. Al copiar una plantilla,
> cuenta los sliders en `MODULE_CONFIGS`, no con `ls`.

### Nomenclatura real, con sus excepciones

La regla es "repite el nombre de la carpeta en sus archivos", pero hay excepciones que existen y no
se van a corregir. Conócelas para no "arreglarlas" al copiar:

| Elemento | Convención | Excepciones reales |
|---|---|---|
| Empresa | minúsculas, una palabra, sin separadores | — |
| Curso | `snake_case` mayoritario | `kebab-case` en `equsera-2026`, `gaia-ambiental-v2`, `aris-sagrilaft-ptee-qhs-segovia`; sin separador en `induccionvisitantes`; `induccionV3`; **PascalCase** en `MineriaSuperficie` |
| Módulo | `modulos/moduloN/` con **N desde 0**, y `moduloN.php` + `.js` + `.css` | `modulos/evaluacion1/evaluacion1.php` rompe el patrón `moduloN` |
| Slider | `sliders/sliderN/sliderN.{php,js,css}`, **N desde 1**, sin cero a la izquierda | `actividad1/actividad1.*`; y `slider6-actividad/` cuyos archivos **siguen llamándose `slider6.*`** (carpeta ≠ archivo) |
| Carpeta de sección | minúsculas | `rutaAprendizaje/` contiene `ruta.php`; `navegacionInferior/` contiene `navegacion.html` (carpeta camelCase, archivo distinto) |
| Media | mezcla `kebab-case` y `snake_case` | typos conservados a propósito (`m0-sld1-metedologia.mp3`) |

Que los sliders no lleven cero a la izquierda significa que **el orden lexicográfico no es el orden
real** (`slider10` va antes que `slider2` al listar). El orden lo manda `MODULE_CONFIGS`, no `ls`.

**Assets por slider.** Cada slider puede llevar sus propios `img/`, `audio/`, `pdf/`, `iconos/`
dentro de su carpeta — no en el `assets/` del curso. Al copiar un slider se copia su carpeta entera.
Algunos sliders llevan además su propio pack de traducción (`manual.json` + `media.json`); ver §14.1.

### Reglas de `course_content/`
- **Un curso = una carpeta.** Nada compartido entre cursos salvo lo que ya está en `assets/`
  global y en `app/`.
- Los `sliders` **no se declaran en la BD**: se declaran en `MODULE_CONFIGS[moduloN].slides[]`
  (con `id`, `path`, `title` y, si es actividad, `isActivity`/`evaluationNumber`/`init`). El HTML
  del slider vive **solo** en `sliders/sliderN/sliderN.php` y `main.js` lo trae por `fetch`.
- El **orden** de los módulos es el campo `orden` de `MODULE_CONFIGS`. Reordenar = cambiar
  números ahí, nada más.
- La identidad de contenido que se pasa a `get_course_modules('<slug>')` es **fija** (el slug),
  no el `course_code` de la matrícula, que cambia por convocatoria.
- **Qué NO agregar a una carpeta de curso:** credenciales, `.sql`, endpoints propios que dupliquen
  `router.php`, copias de `functions_helpers.php`, `node_modules`, backups (`*_old.php`).

---

## 10. Plantillas de curso y `/crear-curso`

**No existe una carpeta llamada `plantilla/` ni `template/`.** Las plantillas son cursos reales
que se copian. Referencias por generación:

| Generación | Plantilla de referencia | Notas |
|---|---|---|
| B (moderna, recomendada) | `course_content/cursos/gaia-ambiental-v2` | La más completa: `course_access.php`, `MODULE_CONFIGS` extraído a `module-config.js` **con `orden` explícito**, `locales/`, actividades y `evaluacion1` como entrada de primer nivel. modulo0-3 (3 · 12 · 1 · 0 sliders). |
| B (variante) | `course_content/cursos/aris_seguridad_vial_2026` | modulo0-4 (3 · 4 · 2 · 1 · 1). `MODULE_CONFIGS` dentro de `main.js`, **sin** `course_access.php` (no cubre "curso público + alumno con sesión") y **sin** `config.php` ni `ci_instance.php`. |
| A (legado) | `course_content/arissegovia/aris_sagrilaft_ptee_segovia` | Solo para cursos que deban parecerse a los antiguos. Todo el contenido va en un `modulo.php` monolítico. |

**No uses `equsera-2026` como plantilla**: su `MODULE_CONFIGS` está desincronizado del disco y su
`tracking.js` apunta a archivos que no existen (§16). Sirve como referencia de traducciones
(`locales/README.md`), no como base.

### Procedimiento obligatorio al copiar
1. **Copiar la carpeta completa** a `course_content/<empresa>/<slug_nuevo>/`.
2. **No reorganizar nada**: mismos nombres de carpeta, mismos archivos, misma estructura. Eso
   incluye no "corregir" las excepciones de nomenclatura ni unificar la grafía del `require`.
3. Ajustar módulos/sliders **solo** si se pidió: crear/eliminar `modulos/moduloN/` y
   `sliders/sliderN/` y **reflejarlo en `MODULE_CONFIGS`** (es la fuente única, y no siempre está en
   el mismo archivo — §9).
4. Sustituir dentro de los PHP del curso, **archivo por archivo**:
   - el slug de contenido: `get_course_modules('<slug>')`, `is_previous_module_completed('<slug>', …)`;
   - el **título, la etiqueta y el tiempo estimado** de cada `moduloN.php` (`$module_title`,
     `$module_label`, `$estimated_time`) — están hardcodeados, no salen de BD;
   - el título visible de la portada.
5. Comprobar que se conserva el **contrato de página de curso** (§9): globals `window.*`,
   `<div id="sliders-container">` vacío, bloque de `localStorage` y orden de scripts.
6. Registrar en BD: `training_details` (con `url` apuntando a la carpeta nueva),
   `training_details_themes` (un módulo por fila), `training_course_details` y
   `training_course_asistencia` para el alumno indicado.
7. Si se pidió URL pública: `enable_public_url='yes'` + `code_public=<slug_nuevo>` (que es lo que
   `extract_public_code()` derivaría del `url`; §11).
8. **La plantilla original queda intacta.** Si hace falta cambiarla, se pide autorización aparte.

> **Las rutas relativas están contadas por nivel de profundidad**
> (`../../../../../app/helpers/functions_helpers.php` desde un `moduloN.php`). Copiar un curso a la
> misma profundidad las conserva; moverlo un nivel arriba o abajo las rompe todas en silencio.
> Si cambias la profundidad, hay que recontar cada `require` y cada `src`.

El comando `/crear-curso` está definido en `.claude/commands/crear-curso.md` y automatiza este
procedimiento. Ver §18.

---

## 11. URLs públicas y privadas

Ambas nacen del **mismo campo**: `training_details.url`, cuyo valor canónico es

```text
course_content/<empresa>/<slug>/index.php?course_code={{course_code}}
```

Lo único que cambia es **por qué se sustituye el placeholder `{{course_code}}`**. Ese es todo el
mecanismo.

**Privada (por defecto).** `{{course_code}}` → `training_course_details.course_code` (el de la
matrícula, tipo `MM0808-371`). `CourseDashboardService::buildCourseAccessLink()` además le añade
`&uid=<unique_course_id>&mid=<sub_theme_id>`. Exige sesión + matrícula (`check_session()` →
`check_permission_employee_course()`) y puede llevar gate de proctoring/firma/perfilamiento por
delante (`buildCourseAccessGateLink()`).

**Pública.** `{{course_code}}` → `training_details.code_public`. Controlada **solo por BD**, sin
tocar código:
- `enable_public_url = 'yes'` habilita; `'no'` revoca al instante.
- Se arma con `AccessService::buildPublicCourseUrl()` (`AccessService.php:265`) — **no construir la
  URL a mano**. Devuelve `''` si `enable_public_url !== 'yes'`, y aplica `rawurlencode()` al código.
  Lo consume `homember.php:280` para pintar el icono de compartir de cada tarjeta.
- Se valida en `AccessService::isCoursePublic()` (`AccessService.php:229`):
  `WHERE enable_public_url='yes' AND code_public=? AND borrado='0'`. **No hay ruta pública
  dedicada**: valida el propio `index.php` del curso al llamar a `resolve_course_access()`.
- El invitado entra como `unique_course_id = 0`, `user_id = 0`, `fullname = 'Invitado'`, **sin**
  gate y **sin** `uid`/`mid`. Su progreso va a `training_progress_public`, **compartido entre todos
  los invitados** del mismo curso.
- `course_access.php` (solo `gaia-ambiental-v2`) cubre el caso mixto: curso público + alumno **con**
  sesión y matrícula → `gaia_resolve_student_access()` recupera sus ids reales para que el progreso
  sí se guarde a su nombre.

> **La confusión que hay que evitar.** El código que viaja en un enlace público es `code_public`
> (**el slug de la carpeta**: `gaia-ambiental-v2`), no el `course_code` de matrícula
> (`MM0808-371`). Ambos llegan por el mismo parámetro `?course_code=` y `resolve_course_access()`
> los distingue. Confundirlos produce un 404 o un acceso que "a veces funciona".

**Cómo se genera `code_public`.** No se escribe a mano: `Training::extract_public_code($url)`
(proyecto hermano, `Training.php:236`) toma `training_details.url`, le quita esquema y query, y
devuelve el **tercer segmento de la ruta** truncado a 100 caracteres —
`course_content/cursos/aris_seguridad_vial_2026/index.php?...` → `aris_seguridad_vial_2026`. Se
**recalcula en cada guardado** del curso desde el panel. Las filas antiguas se rellenaron con un
`UPDATE ... SUBSTRING_INDEX(...)`. Consecuencia práctica: **si cambias la carpeta del curso, cambia
la URL pública**; y si escribes un `code_public` a mano, el próximo guardado desde el panel te lo
pisa.

**Hay dos constructores de enlace público, independientes.** No están unificados:

| Dónde | Método | Qué produce |
|---|---|---|
| Panel de administración | `Training_model::getIdCapacitacion()` | campo de solo lectura "URL pública": `<url sin query> . '?course_code=' . urlencode(code_public)` |
| Portal del alumno (este repo) | `AccessService::buildPublicCourseUrl()` | `base_url()` + `url` con el placeholder sustituido |

En `courses_v2` **solo aplica el segundo**. Si algún día divergen, esta es la razón.

**Qué NO tiene este mecanismo** (verificado como ausente, no como "no encontrado"): **no hay token,
ni hash, ni UUID, ni caducidad, ni tabla de compartidos, ni contador de accesos**. La URL pública es
adivinable si se conoce el slug. La única protección es el flag en BD.

**Revocar corta también el tracking:** los endpoints `progress.getPublic` / `progress.updatePublic`
revalidan `isCoursePublic()` en cada llamada y devuelven 403 si el flag está en `'no'`.

**Seguridad asociada:** si las columnas no existen en un tenant, `hasPublicUrlColumns()` hace que
`isCoursePublic()` devuelva `false` (ningún curso es público: default seguro, pero las URLs públicas
de ese tenant no funcionan hasta aplicar el `ALTER`).

---

## 12. Categorías — y qué es `cursosdev`

> **`cursosdev` es el nombre con el que se habla del ambiente demo/desarrollo.** No es una carpeta,
> ni una clase, ni una base de datos. En el código no aparece nunca. Lo único literal que existe con
> ese nombre es una entrada de DNS local:
> `127.0.0.1 cursosdev.amatia.local` en `C:\Windows\System32\drivers\etc\hosts` (líneas 65-66).
>
> Esa entrada está **colgada**: no hay `ServerName`/`ServerAlias` que la declare en
> `httpd-vhosts.conf`, así que cae en el vhost por defecto; y `get_subdomain()` devolvería
> `'cursosdev'`, que **no tiene `case`** en `application/config/local/database.php` → `$database = ''`
> → sin conexión. Entrar por ese host hoy no funciona.
>
> **El ambiente que sí es "cursosdev" en la práctica** es el tenant `cursos` (alias
> `sofactiacursos`, `capacitaciondev`, `capacitacioncursos`, `localhost`) → base **`courses_demo`**.
> Es el único que tiene la tabla de categorías, y la carpeta `course_content/cursos/` es su
> contenido. Cuando alguien dice "esto es de cursosdev", se refiere a esto.

**Qué son.** Agrupadores de las tarjetas de "Mis cursos" en `homember.php`. Tabla
`training_course_category_environment` (`id`, `key_string`, `category_es`, `category_en`,
`estatus`, `deleted_at`). Filas actuales: `aris_marmato`, `aris_segovia`, `emerald`, `rekonecta`,
`tecnitanques`, `transprensa`, **`desarrollo`**.

**Dónde viven y quién hace qué:**
- **Se crean y editan en el proyecto hermano**: `amatia_capacitacion/application/modules/training/`
  → `controllers/Category.php` + `models/Category_model.php`. `key_string` es un slug único
  generado a partir de `category_es` (`build_key_string()`).
- **`courses_v2` solo las lee**: `CourseDashboardService::getCategoriesEnvironments()` (helper
  `get_categories_environment()`), y `getMyCoursesList()` hace el `LEFT JOIN` por
  `training_details.category_id`.

**Por qué es "de un solo ambiente".** Dos candados independientes, y hay que conocer los dos:

1. **De escritura, explícito y hardcodeado.** `Category::is_tenant_allowed()` del proyecto hermano es
   literalmente `$this->db->database === 'courses_demo'`. Los cuatro métodos (`index`,
   `getCategories`, `saveCategory`, `deleteCategory`) salen por ahí. En cualquier otro tenant el CRUD
   de categorías **no existe**, aunque la tabla estuviera creada.
2. **De lectura, por esquema.** La tabla `training_course_category_environment` solo existe en la
   base `courses_demo`. En el resto `getCategoriesEnvironments()` devuelve `[]` gracias a
   `SchemaService::hasTable()`, todos los cursos caen sin categoría y `homember` los pinta en una
   sola grilla — exactamente el layout anterior a la funcionalidad.

**Esa es la funcionalidad "exclusiva de `cursosdev`"**: vive solo en el ambiente demo/desarrollo. Si
algún día se lleva a otro tenant hay que tocar **los dos** candados, no uno.

**Relación con los cursos: FK lógica, no real.** `training_details.category_id INT NULL` →
`training_course_category_environment.id`. Hay índice (`idx_category_id`) pero **no hay
`FOREIGN KEY`**; el propio SQL lo comenta como "FK logica". Borrar una categoría es borrado suave
(`deleted_at`) precisamente porque nada impide dejar cursos apuntando a ella.

**`key_string` es la llave estable, `id` no.** Se genera al **insertar** desde `category_es`
(`build_key_string()` → `slugify()`: "Aris Marmato" → `aris_marmato`, y ante colisión `_2`, `_3`…) y
**nunca se regenera al editar**. Renombrar una categoría no cambia su `key_string`: eso es
intencional, porque `homember.php` agrupa por `category_key`.

**No asumir** que la funcionalidad aplica a otros tenants: cualquier código nuevo que use
categorías debe pasar por `SchemaService::hasTable()` igual que el existente.

---

## 13. Base de datos — cómo trabajar sin romper nada

- **Multi-tenant por subdominio.** `amatia_capacitacion/application/config/local/database.php`
  mapea subdominio → base: `cursos`/`localhost`/`capacitaciondev` → `courses_demo`;
  `arismarmato` → `courses_arismarmato`; `arissegovia` → `courses_arissegovia`. **Las bases no
  tienen el mismo esquema.**
- **Regla de oro:** antes de leer una columna que no esté en todas las bases →
  `SchemaService::hasColumn()` / `hasTable()`. Precedente: `enable_public_url`, `code_public`,
  `category_id`, `training_course_category_environment`.
- **Consultas siempre preparadas.** `$CI->db->query($sql, array($a, $b))`. Interpolar
  `$course_code` en SQL fue una vulnerabilidad crítica real (C3). El Query Builder de CI3
  (`->where()`) también escapa; ambos estilos conviven.
- **Nunca** confiar en el body para la identidad: el alumno sale de la sesión.
- **Cambios de esquema:** aplicar el SQL y **documentarlo en `app/sql/database_changes.sql`** con
  fecha y motivo, indicando que hay que aplicarlo en cada tenant.
- **Borrado lógico:** no uniforme. `borrado='0'`, `estatus='activo'`, `deleted_at IS NULL`,
  `status='1'` según la tabla. Copiar el criterio de la consulta vecina.
- Hay **decenas de tablas de backup** (`*_22_apr_2021`, `*_old`, `*_temp`). No consultarlas.

---

## 14. Frontend

- **jQuery + Bootstrap.** Sin build, sin bundler, sin framework SPA. Los cursos de generación B
  tienen navegación SPA propia (`spa-navigation.js`), hecha a mano.
- **Bootstrap convive en 4 versiones** (3.0.0 en `error-404`, 4.5.2 en autoservicio, 5.0.2 en
  `photo_capture`, 5.3.3 en `signature_capture`). **Recomendación:** unificar; hoy no lo está.
- **AJAX:** `$.ajax` con `dataType: 'json'` contra `router.php?action=...`. Siempre `POST` para
  escrituras (el router exige `Origin`/`Referer` del mismo host en POST).
- **Escapado:** en PHP `htmlspecialchars($v, ENT_QUOTES, 'UTF-8')`; en JS que inyecta HTML,
  `escapeHtml()` (definida en cada página de autoservicio). Hubo XSS almacenado real por no
  hacerlo (A3, N2).
- **CDN:** todo recurso externo con `integrity` + `crossorigin` (M8). Si se carga por inyección
  dinámica de `<script>`, el SRI va por propiedad (`script.integrity`).
- **Traducciones (generación B):** subsistema completo, ver §14.1.
- **Componentes reutilizables:** `widgets/sidenav.php` (PHP) y, dentro de un curso,
  `plugins/partials/` y `plugins/libs/components/`.

### 14.1 Traducciones (i18n) — solo generación B

Es un subsistema propio, hecho a mano, y **vive dentro de cada curso**: no hay nada centralizado.
Un curso sin `locales/` sencillamente no es traducible.

**Cómo funciona.** `dom-translator.js` recorre el DOM y traduce; lo que no sabe traducir se lo pide
al `translate.php` **del propio curso** (Google Translate, usa `GOOGLE_TRANSLATE_API_KEY` del `.env`)
y cachea el resultado. `language-switcher.js` es el `<select>` ES/EN. Funciona también sobre
contenido inyectado por AJAX — importante, porque los sliders llegan por `fetch`.

**Cuatro fuentes, con esta precedencia:**

| Archivo | Qué contiene | Se edita a mano |
|---|---|---|
| `locales/en/manual.json` | `{"texto ES exacto": "texto EN"}`. **Gana a Google**: si un texto está aquí, ni se consulta. | **sí** — es donde se corrige una traducción |
| `locales/en/auto.json` | Caché que escribe `translate.php`. | no; solo borrar una entrada mala para que se re-traduzca |
| `locales/media.json` | Medios alternativos por idioma para elementos marcados `data-i18n-media`. Rutas relativas a la raíz del curso. Si falta el idioma, cae a `es`. | **sí** |
| `<slider>/manual.json` y `<slider>/media.json` | Pack local de un slider. Rutas **relativas a la carpeta del slider**. | **sí** |

**Packs por slider.** Un slider puede llevar todas sus traducciones dentro de su carpeta: se marca
su `<section>` raíz con `data-i18n-pack="modulos/modulo1/sliders/slider10"` y `dom-translator` carga
los dos JSON al insertarse. Ejemplos reales: `equsera-2026/modulos/modulo1/sliders/slider10` y
`slider11`. Convención: prefijar las claves de media por slider (`s10-video-desktop`) para que no
choquen.

**El texto español debe coincidir EXACTO** (sin espacios sobrantes) con lo que hay en la página. Es
la causa número uno de "no me traduce esa frase".

**Documentación de referencia, mantenida y más detallada que este manual:**
`course_content/cursos/equsera-2026/locales/README.md`. Léela antes de tocar traducciones.

**Al copiar una plantilla:** `locales/` se copia entero. Si cambian los textos del curso nuevo, las
entradas de `manual.json` que ya no casen quedan muertas (inofensivas) y `auto.json` se irá
repoblando solo. Los `media.json` **sí** hay que revisarlos: apuntan a rutas de archivos concretos.

---

## 15. Reglas obligatorias

1. **Buscar antes de crear.** El catálogo de §4 primero; `grep` después.
2. **Reutilizar el control de acceso.** `check_permission_employee_course()` /
   `resolve_course_access()`. Nunca una consulta propia de matrícula.
3. **La identidad viene de la sesión**, jamás de `$_POST`/`$_GET`.
4. **`hasSession()` en JSON, `checkSession()` en páginas.** Mezclarlos rompe el AJAX con un 302.
5. **Consultas preparadas siempre.**
6. **`SchemaService` antes de tocar columnas que no están en todos los tenants.**
7. **Endpoints nuevos solo por `router.php`** + línea en `app/routes.php`, con el comentario que
   justifique el `requiere_sesión`.
8. **Nada de `if(isset($_GET[...]))` en helpers** — convierte en endpoint a todo el sitio.
9. **Nada de `error_reporting(0)`.** Patrón correcto: `runJsonAction()` de `ProctoringController`.
10. **`header(...); exit;`** explícito. Nunca `header(...) or die(...)`.
11. **No tocar la plantilla original** al crear un curso derivado.
12. **No mover archivos de `course_content/` sin buscar referencias**: `training_details.url`
    apunta a rutas literales y cientos de archivos hacen `require` con rutas relativas contadas
    en niveles (`../../../../../app/helpers/...`).
13. **No renombrar funciones del helper**: son API pública para los cursos.
14. **No añadir dependencias.** Composer tiene una sola y a propósito.
15. **Diferenciar lo global de lo de un ambiente** (categorías: solo `courses_demo`).
16. **PHP 7.4.** Lintar con `php7.4.33` antes de dar algo por terminado.

---

## 16. Anti-patrones

### Problemas realmente encontrados en el código (no hipótesis)
| Problema | Dónde | Estado |
|---|---|---|
| Lógica duplicada entre servicios y `$CI->db` directo; los modelos casi no se usan | `app/services/*` vs `app/models/*` | vivo — **Requiere revisión** |
| Mismo bloque de portada copiado en 16 `index.php` de curso | `course_content/*/*/index.php` | vivo; dos de ellos tenían el bug `Undefined variable $module` (corregido 2026-08-12) |
| `module-config.js` de `gaia-ambiental-v2` con encabezado "EQUSERA 2026": el bloque se extrajo del `main.js` de equsera y no se actualizó el comentario | `cursos/gaia-ambiental-v2/plugins/js/module-config.js:2` | vivo — cosmético pero engañoso |
| `course_content/arissegovia/upload.php`: sin verificación de sesión, toma `course_code`/`module_id` de `$_POST` y depende del proyecto **antiguo** `amatia/courses/S3/` | ese archivo | vivo — **riesgo, requiere revisión** |
| Tracking de `equsera-2026` apunta a `progreso.php`/`update_progress.php` inexistentes | `cursos/equsera-2026/plugins/js/tracking*.js` | vivo (A4 pendiente) |
| `CONTENT_CODE = 'gaia-ambiental-v2'` hardcodeado | `TrainingProgressController:15` | vivo; bloquea A4 |
| Shims temporales de endpoints | `functions_helpers.php:282-290` | vivos, a borrar cuando roten las cachés |
| 4 versiones de Bootstrap conviviendo | vistas y autoservicio | vivo |
| **`MODULE_CONFIGS` desincronizado del disco**: `modulo0` declara 5 sliders y hay 7; `modulo1` declara 12 (con `slider2` comentado) y hay 14; `modulo2` y `modulo3` **no están declarados** aunque sus carpetas existen | `cursos/equsera-2026/plugins/js/main.js:12` | vivo — el contenido no declarado sencillamente no se carga |
| `resolveContentCodeFromUrl()` regexea `course_content/cursos/([^/?&]+)` — **solo casa la empresa `cursos`**. Un curso de generación B en otra empresa no calcularía progreso ponderado | `CourseDashboardService` (privado) | vivo; hoy no se nota porque los 3 cursos modernos están en `cursos/` |
| Dos grafías del `require` del helper conviviendo entre cursos (`.../functions_helpers.php` vs `.../app/helpers/functions_helpers.php`) | `course_content/cursos/*` | vivo; ambas funcionan — **no unificarlas de paso al copiar** |
| Un slider con su propio `download.php`: endpoint fuera de `router.php` | `cursos/equsera-2026/modulos/modulo1/sliders/slider4/download.php` | vivo — **requiere revisión** |
| `evaluacion1` cuelga de `modulos/` como si fuera un módulo, pero no sigue el patrón `moduloN` | `cursos/gaia-ambiental-v2/modulos/evaluacion1/` | vivo — intencional, pero rompe cualquier bucle que asuma `moduloN` |

### Prácticas a evitar (preventivas)
- URLs de curso construidas a mano en vez de `buildPublicCourseUrl()` / `buildCourseAccessLink()`.
- Un `.php` nuevo en la raíz o dentro de un curso haciendo de endpoint.
- Cambiar una función global para resolver el caso de un solo curso.
- Copiar un curso y "mejorarle" la estructura de paso.
- Consultar `_backup/` o las tablas de respaldo como si fueran fuente.
- `?>` final seguido de espacios en archivos incluidos (rompe `header()`).

---

## 17. Si eres nuevo en el proyecto

**Orden de lectura sugerido (1 hora):**
1. `router.php` y `app/routes.php` — cómo entra una petición.
2. `app/services/AccessService.php` — cómo se decide quién ve qué.
3. `app/helpers/functions_helpers.php` — el catálogo de funciones que usan los cursos.
4. `app/views/pages/homember.php` — cómo se pinta el listado del alumno.
5. `course_content/cursos/gaia-ambiental-v2/` — un curso moderno completo. Empieza por su
   `plugins/js/module-config.js` y por `modulos/modulo1/modulo1.php`: ahí está el contrato de §9.
6. `course_content/cursos/equsera-2026/locales/README.md` — el sistema de traducciones (§14.1).
7. `.claude/revision_seguridad.md` — qué se arregló, qué sigue abierto y por qué.

**Para buscar si algo ya existe:** `grep` por el nombre del concepto en `app/services/` y
`app/helpers/`; casi todo lo transversal está en uno de esos dos sitios.

**Errores típicos de quien llega:** usar `check_session()` en un endpoint JSON; construir la URL
pública a mano; interpolar `$course_code` en SQL; asumir que una columna existe en todos los
tenants; crear un archivo nuevo en la raíz; editar la plantilla al copiar un curso.

---

## 18. Comandos del proyecto

### `/crear-curso` (definido en `.claude/commands/crear-curso.md`)
Crea un curso nuevo copiando una plantilla existente, respetando su estructura, lo registra en la
BD **local**, lo asocia al alumno indicado y prepara la URL pública para revisión.

```text
/crear-curso
plantilla: gaia-ambiental-v2
nombre: Seguridad Industrial 2026
empresa: cursos
modulos: 5        (opcional → si falta, la cantidad de la plantilla)
sliders: 8        (opcional → si falta, la de la plantilla)
usuario: 12345678 (emp_unique_id del alumno)
publica: si       (opcional)
```
También admite una sola línea: `/crear-curso plantilla=gaia-ambiental-v2 nombre="Curso Nuevo"`.

### Comandos recomendados (NO existen todavía)
- **`/verificar-curso <slug>`** — comprobaría carpeta ↔ `training_details.url` ↔ módulos ↔
  matrícula ↔ URL pública. Hoy es manual y es donde más fallos aparecen.
- **`/lint74`** — pasar `php7.4.33 -l` sobre los archivos modificados. Hoy se hace a mano.

---

## 19. Matriz de decisión

| Necesidad | Dónde hacerlo | Qué revisar primero | Reutilizar | Crear nuevo si… |
|---|---|---|---|---|
| Nuevo método | `app/services/XxxService.php` | §4 completo | el servicio del mismo dominio | ningún servicio cubre el dominio |
| Nueva función global | wrapper en `app/helpers/functions_helpers.php` | lista de wrappers existentes | el método del servicio | la usan páginas de `course_content/` |
| Nuevo componente | `widgets/` o `plugins/partials/` del curso | `widgets/sidenav.php` | el widget existente | lo comparten ≥2 vistas |
| Nueva ruta | `app/routes.php` + controlador | acciones ya registradas | el controlador del dominio | el dominio no existe aún |
| Nueva URL pública | BD: `enable_public_url` + `code_public` | `AccessService::isCoursePublic()` | `buildPublicCourseUrl()` | **nunca** a mano |
| Nuevo curso | `course_content/<empresa>/<slug>/` | §9 y §10 | una plantilla existente | **nunca** desde cero |
| Copiar plantilla | `/crear-curso` | qué generación es la plantilla | la estructura íntegra | — |
| Nuevo módulo | `modulos/moduloN/` + `MODULE_CONFIGS` + fila en `training_details_themes` | dónde vive `MODULE_CONFIGS` en ESE curso (§9) | el `moduloN` vecino | — |
| Nuevo slider | `modulos/moduloN/sliders/sliderN/` + entrada en `MODULE_CONFIGS[moduloN].slides` | `slider1` del mismo módulo | su `.php/.js/.css` | — |
| Nueva categoría | **proyecto hermano**: `training/controllers/Category.php` | §12 y si el tenant tiene la tabla | `Category_model` | — |
| Cambio de esquema | SQL + `app/sql/database_changes.sql` | qué tenants lo necesitan | `SchemaService` para el guard | — |

---

## 20. Checklists

### Cualquier funcionalidad nueva
- [ ] ¿Busqué en §4 y con `grep` si ya existía?
- [ ] ¿Reutilicé el servicio/función existente en vez de duplicar?
- [ ] ¿El archivo está en la carpeta que le toca (§5)?
- [ ] ¿Respeté las convenciones de nombres (§6)?
- [ ] ¿Las consultas van preparadas y la identidad sale de la sesión?
- [ ] ¿Usé `SchemaService` si toco columnas no universales?
- [ ] Si es endpoint: ¿está en `app/routes.php` con su comentario de `requiere_sesión`?
- [ ] ¿Escapé todo lo que se pinta (PHP y JS)?
- [ ] ¿Pasa `php7.4.33 -l`?
- [ ] ¿Probé que no rompí `homember.php` ni la página del curso afectado?

### Curso creado desde plantilla
- [ ] Plantilla correcta y de la generación adecuada.
- [ ] **La plantilla original quedó intacta** (`git status` no la muestra modificada).
- [ ] Misma estructura de carpetas y archivos que la plantilla.
- [ ] Cantidad de módulos correcta, y reflejada en `MODULE_CONFIGS` **y** en
      `training_details_themes`.
- [ ] Cantidad de sliders correcta, y reflejada en `MODULE_CONFIGS` (**contada en la config, no con
      `ls`**).
- [ ] Slug de contenido sustituido dentro de los PHP del curso.
- [ ] Títulos/etiquetas/tiempos de cada `moduloN.php` actualizados (están hardcodeados en PHP).
- [ ] Contrato de página intacto: globals `window.*`, `#sliders-container` vacío, bloque
      `localStorage`, orden de scripts (§9).
- [ ] Rutas relativas `../../../` intactas (el curso quedó a la misma profundidad).
- [ ] `locales/`: `media.json` global y de cada slider revisados (no apuntan a media de la plantilla).
- [ ] `training_details` creado con `url` correcta.
- [ ] `training_course_details` (instancia) con fechas vigentes y `course_code`.
- [ ] `training_course_asistencia` creada para el alumno indicado.
- [ ] Empresa correcta (carpeta y, si aplica, `category_id`).
- [ ] URL pública: `enable_public_url` + `code_public`, y probada sin sesión.
- [ ] Recursos presentes: imágenes, audios, vídeos, `locales/`.
- [ ] Tracking apuntando a `router.php` (no a archivos sueltos).
- [ ] Curso abierto en local sin warnings de PHP.

---

## 21. Documentos relacionados

- `.claude/revision_seguridad.md` — auditoría de seguridad, estado de cada hallazgo y decisiones
  tomadas. **Leerlo antes de tocar acceso, login, proctoring o autoservicio.**
- `app/sql/database_changes.sql` — cambios de esquema propios de este repositorio.
- `.claude/commands/crear-curso.md` — procedimiento operativo del comando.
