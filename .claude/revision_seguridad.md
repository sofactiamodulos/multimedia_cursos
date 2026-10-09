# Revisión de seguridad y calidad — courses_v2

**Fecha:** 2026-08-10
**Rama:** `dev`
**Alcance:** raíz del proyecto, `app/` (controladores, servicios, helpers, vistas), `widgets/`,
`autoservicio/` y los `plugins/js` de los cursos. No se auditó `vendor/`, `_backup/` ni el
proyecto hermano `amatia_capacitacion`.

**Método:** lectura de código con verificación puntual contra la BD local (`courses_demo`) y
ejecución de peticiones reales contra `router.php`. Cada hallazgo indica si se **verificó
ejecutando** o si se sustenta solo en lectura de código. No se realizó explotación real ni
pruebas contra entornos remotos.

---

## Resumen ejecutivo

La arquitectura ha mejorado (router único, servicios, controladores), pero el código legacy
arrastra fallas críticas de autenticación e inyección SQL **explotables sin sesión**.

Existe una **cadena completa de toma de cuentas**: un endpoint público entrega el teléfono de
cualquier empleado a partir de su cédula (C2), y ese teléfono **es** la contraseña del login
(A1). Además, cualquiera puede subir archivos al bucket S3 y fabricar evidencia de proctoring
a nombre de otro empleado (C1).

| Severidad | Cantidad |
|---|---|
| 🔴 Crítico | 3 |
| 🟠 Alto | 5 |
| 🟡 Medio | 8 |
| 🔵 Bajo | 4 |

---

## 🔴 CRÍTICO

### C1 — Subida de archivos y evidencia de proctoring sin autenticación ni validación

- **Ubicación:** `app/controllers/ProctoringController.php:174-260` · `app/routes.php:23`
- **Estado:** ✅ **CORREGIDO** (2026-08-10)
- **Verificación:** ejecutando. Una petición sin sesión atraviesa el router y llega a la lógica
  del controlador (responde `No se recibieron archivos`, es decir el rechazo fue por falta de
  archivo, no por falta de sesión).

**Problema.** `uploadAction()` no llama a `check_session()` — es el único método del controlador
que no lo hace (`saveSignatureAction` sí, línea 60) — y su ruta está registrada con
`requiere_sesión = false`. La identidad se toma de `$_POST['emp_unique_id']`, no de la sesión.
Tampoco hay validación de tipo, tamaño ni extensión: `$file['tmp_name']` se pasa directo a
`putObject` con `ContentType: image/png` forzado, sea lo que sea el archivo.

**Riesgo.** Cualquiera en internet puede:
1. Subir archivos arbitrarios al bucket S3 (coste, almacenamiento de contenido ilícito y un
   `ContentType` mentiroso que puede volverse XSS almacenado si alguna vista sirve esos objetos).
2. Fabricar la foto y la firma de proctoring de cualquier empleado. El no repudio que persigue
   el diseño (ver comentario de la línea 215) deja de existir.

**Corrección propuesta:**
```php
public function uploadAction() {
    if (!check_session()) { $this->json(false, 'Sesión no válida'); }

    // La identidad SIEMPRE de la sesión, nunca del body (mismo criterio que ya
    // aplica ActivityController::sessionEmployee()).
    $emp_unique_id = (int) $this->CI->session->userdata('employee_data')['user_id'];

    // La matrícula se valida, no se acepta la que mande el cliente:
    $unique_course_id = check_permission_employee_course($course_code, false);

    $mime = finfo_file(finfo_open(FILEINFO_MIME_TYPE), $file['tmp_name']);
    if (!in_array($mime, ['image/png', 'image/jpeg'], true)) { $this->json(false, 'Formato no permitido'); }
    if ($file['size'] > 5 * 1024 * 1024) { $this->json(false, 'Archivo demasiado grande'); }
```
Y en `app/routes.php`, cambiar la ruta `proctoring.upload` a `true`.

---

### C2 — Endpoint público que entrega credenciales + inyección SQL

- **Ubicación:** `app/helpers/functions_helpers.php:307-326`
- **Consumidores:** `autoservicio/autoservicio_marmato/index.php:372`,
  `autoservicio/autoservicio_segovia/index.php:371`
- **Estado:** ✅ **CORREGIDO** (2026-08-10)
- **Verificación:** lectura de código. Las páginas de autoservicio solo cargan el helper; no
  llaman a `check_session()`.

**Problema.**
```php
$cc_employee = $CI->input->post('id_employee');
$company     = $CI->input->post('company');
$sql = "SELECT id,email,cellphone_no
        FROM employee_master
        WHERE emp_unique_id = '$cc_employee'
        AND nivel1= '$company'";
```
Tres fallas superpuestas: sin verificación de sesión, inyección SQL directa en dos parámetros
de usuario, y devuelve `email` y `cellphone_no` en el JSON de respuesta.

**Riesgo.** Encadenado con A1 es **toma de cuenta completa**: con una cédula se obtiene el
celular, y el celular es la contraseña. Con la inyección (`' OR '1'='1`) se puede volcar
`employee_master` entero → fuga masiva de datos personales.

**Corrección propuesta:**
```php
$result_alumno = $CI->db->query(
    "SELECT id FROM employee_master WHERE emp_unique_id = ? AND nivel1 = ? AND status = '1'",
    array($cc_employee, $company)
)->result_array();
```
El frontend de autoservicio no necesita `email` ni `cellphone_no` para listar cursos: quitarlos
del `SELECT`. Evaluar además un segundo factor (código por SMS), porque hoy el endpoint es un
oráculo de enumeración de empleados.

---

### C3 — Inyección SQL autenticada por `course_code` (5 puntos)

- **Ubicación:**
  - `app/services/AccessService.php:34` ← **el más grave**
  - `app/services/CourseDashboardService.php:413`, `:439`, `:460`
  - `app/helpers/functions_helpers.php:235`
- **Estado:** ✅ **CORREGIDO** (2026-08-10)
- **Verificación:** lectura de código.

**Problema.** `AND tcd.course_code = '".$code_course."'` con `$code_course` proveniente de
`$_GET['course_code']` / `$_POST['code_course']` sin escapar.

`AccessService::checkPermissionEmployeeCourse()` es el caso crítico: se ejecuta en **toda**
página de curso y es justamente la función que decide si el alumno tiene acceso. Una inyección
ahí no solo lee datos, salta el control de matrícula.

**Nota:** la misma clase ya lo hace bien en `AccessService.php:147`
(`WHERE tca.id_employee = ? AND tcd.course_code = ?`). Es inconsistencia, no desconocimiento.

**Corrección propuesta:** bindings en los 5 puntos.
```php
$result = $CI->db->query($sql, array($id_employee, $code_course))->result_array()[0] ?? null;
```
`$id_employee` interpolado (`CourseDashboardService.php:171-173`) viene de sesión, así que es
menos urgente, pero conviene parametrizarlo en el mismo barrido (defensa en profundidad).

---

## 🟠 ALTO

### A1 — El modelo de autenticación es un secreto de baja entropía en texto plano

- **Ubicación:** `app/views/pages/login.php:19-59`
- **Estado:** ✅ **CORREGIDO** (2026-08-10) — mitigado; el cambio de modelo de credenciales sigue pendiente
- **Verificación:** lectura de código.

La "contraseña" es `employee_master.cellphone_no`, guardada **sin hash** y comparada en PHP:
```php
if($cellphone_no == trim($row['cellphone_no']) || $cellphone_no == trim($strCellphone))
```
- Sin hashing: cualquier lectura de la BD (o C2) entrega todas las credenciales.
- Comparación laxa `==`: con dos cadenas numéricas PHP compara numéricamente, así que
  `"007" == "7"` es verdadero. Debe ser `hash_equals()`.
- Sin límite de intentos: un celular colombiano tiene ~10 dígitos con prefijo conocido; la
  fuerza bruta es viable.

**Corrección propuesta.** Corto plazo: `hash_equals()` + limitación de intentos por cédula/IP +
registro de intentos fallidos. Medio plazo: contraseña propia con `password_hash()` o código de
un solo uso por SMS/correo.

### A2 — La protección CSRF del router es evadible

- **Ubicación:** `router.php:24-33`
- **Estado:** ✅ **CORREGIDO** (2026-08-10)
- **Verificación:** lectura de código.

```php
if ($origin !== '' && $host !== '' && stripos($origin, $host) === false) { rechazar }
```
Dos huecos: es una comparación de **subcadena** (un `Origin: https://localhost.evil.com`
contiene `localhost` y pasa), y si no llegan `Origin` **ni** `Referer` la condición se salta
entera.

**Corrección propuesta:**
```php
$origin_host = parse_url($origin, PHP_URL_HOST);
if ($origin_host === null || strcasecmp($origin_host, preg_replace('/:\d+$/', '', $host)) !== 0) {
    rechazar;
}
```
Lo ideal es un token CSRF por sesión, que CodeIgniter ya sabe generar.

### A3 — XSS almacenado en el listado del menú lateral

- **Ubicación:** `widgets/sidenav.php:123` y `:146`
- **Estado:** ✅ **CORREGIDO** (2026-08-10)
- **Verificación:** lectura de código.

```php
<?= $course['course_title'] ?>       <!-- sin escapar -->
<?= $module['category_name']; ?>     <!-- sin escapar -->
```
Un título con `<img src=x onerror=...>` se ejecuta en el navegador de todo alumno matriculado.
Requiere acceso al panel de administración: es escalada de privilegios (administrador de
contenidos → sesión de cualquier alumno), no ataque anónimo.

Las tarjetas de `homember.php` sí escapan correctamente; es solo el menú.

```php
<?= htmlspecialchars((string) $course['course_title'], ENT_QUOTES, 'UTF-8') ?>
```

### A4 — El tracking de equsera-2026 no persiste nada

- **Ubicación:** `course_content/cursos/equsera-2026/plugins/js/tracking.js:135` y `:191`
- **Estado:** ⬜ pendiente
- **Verificación:** ejecutando (los archivos destino no existen; historial de git confirma que
  nunca existieron).

Apuntan a `app/public/progreso_equsera.php` y `update_progress_equsera.php`, que no existen y
que el `.htaccess` de `app/` bloquearía igual. El progreso de los alumnos matriculados queda
solo en `localStorage`.

**Bloqueante para la corrección:** `TrainingProgressController` tiene
`const CONTENT_CODE = 'gaia-ambiental-v2'` hardcodeado para resolver el bloqueo secuencial de
módulos, así que no basta con cambiar la URL. Opciones: (a) resolver el content code
dinámicamente desde `td.url` — ya existe `CourseDashboardService::resolveContentCodeFromUrl()`
haciendo exactamente eso — o (b) acciones propias para equsera.

### A5 — `error_reporting(0)` en los endpoints oculta fallos reales

- **Ubicación:** `app/controllers/ProctoringController.php:35-36` y `:175-176`
- **Estado:** ✅ **CORREGIDO** (2026-08-10)

Fue lo que mantuvo invisible el fatal de `AWS_REGION`: firma y foto fallaban devolviendo cuerpo
vacío y el front lo interpretaba como error genérico.

**Corrección propuesta:** dejar que `config.php` gobierne la visibilidad de errores (ya
distingue producción de local) y envolver cada acción en `try/catch` que registre en log y
responda un JSON de error estable. Nunca silenciar globalmente.

---

## 🟡 MEDIO

| # | Ubicación | Problema | Recomendación | Estado |
|---|---|---|---|---|
| M1 | `app/services/AccessService.php:40` | `setcookie("unique_course_code", …)` sin `HttpOnly`, `Secure` ni `SameSite` | Pasar array de opciones: `['httponly'=>true,'secure'=>true,'samesite'=>'Lax']` | ✅ (2026-08-11) |
| M2 | `router.php:12` | `$_REQUEST['action']` incluye cookies según `request_order`; una cookie `action` puede fijar la acción | `$_GET['action'] ?? $_POST['action'] ?? ''` | ✅ (2026-08-11) |
| M3 | `app/controllers/ProctoringController.php:236` | `'Error subiendo a S3: ' . $e->getMessage()` se devuelve al cliente | Log interno + mensaje genérico | ✅ (2026-08-11) |
| M4 | `app/services/CourseDashboardService.php:118-127`, `functions_helpers.php:311-313` | 5 `SHOW COLUMNS` por request sin caché entre llamadas; N+1 en `getEvaluationProgressByCourse()` (1 consulta por curso: 18 en la prueba) | Cachear esquema; resolver evaluación de N cursos en una consulta agregada | ✅ (2026-08-11) |
| M5 | `app/public/` (10 de 11 archivos) | Código muerto e inalcanzable por `.htaccess`: `progreso.php`, `update_progress.php`, `progreso_publico.php`, `update_progress_publico.php`, 3× `adaptive_*`, `data_user.php`, y los 2 gates. Cero llamadores | Eliminar (verificado archivo por archivo) | ✅ (2026-08-11) |
| M6 | `app/helpers/functions_helpers.php:215` y `:269` | El bloque `progress_courses` está **duplicado**, el segundo es inalcanzable. `adaptive_profile_context` tiene 0 llamadores | Borrar duplicado y bloque muerto; migrar los 2 endpoints vivos al router | ✅ (2026-08-11) |
| M7 | `training_details.course_description` | Guarda HTML pegado de Teams/ChatGPT (1850 caracteres en el id 59) | Limpiar en escritura, no solo al mostrar | ⬜ **bloqueado** (ver nota) |
| M8 | 15 `<link>`/`<script>` a CDN en vistas y autoservicio | **Ninguno** tiene `integrity=`/SRI; mezclan Bootstrap 5.3.3, 5.0.2 y 4.5.2 | Añadir SRI + `crossorigin` o servir local; unificar versión | ✅ (2026-08-11) — falta unificar versión |

---

## 🔵 BAJO

| # | Ubicación | Problema | Estado |
|---|---|---|---|
| B1 | `app/services/AccessService.php:12` | `header("Location: …") or die(…)`: funciona por accidente (`header()` devuelve `null`). Usar `header(...); exit;` | ✅ (2026-08-12) — las 16 ocurrencias vivas del repo |
| B2 | Todo el repo | Sin pruebas automatizadas. Prioridad de cobertura: acceso a curso, matrícula, proctoring, URL pública | ⬜ |
| B3 | `app/views/pages/error-404.php:11` | Errata: `'Sin acesso'` → *acceso*. También `Verificacion de Identidad` sin tilde en el `<title>` de proctoring | ✅ (2026-08-12) |
| B4 | Vistas | Accesibilidad: `<i class="fa …">` decorativos sin `aria-hidden="true"`; enlace de URL pública abre pestaña nueva sin avisarlo; `error-404.php` sin `<title>` | ✅ (2026-08-12) — parcial: falta avisar de la pestaña nueva |

---

## ✅ Aspectos positivos

- **Router único con tabla de rutas declarativa** (`app/routes.php`): buen patrón, y los
  comentarios que justifican cada `requiere_sesión` explican el *porqué* de cada decisión.
- **`ActivityController::sessionEmployee()`** documenta y corrige exactamente el fallo que sigue
  vivo en `uploadAction`: la identidad se toma de la sesión, nunca del body. El criterio correcto
  ya existe en el proyecto.
- **Guards `SHOW COLUMNS`** para el esquema multi-tenant: bien pensados y bien explicados.
- **Comentarios de alto valor** que explican el porqué histórico (copia única del SDK de AWS,
  el `overflow-x` que rompe `position:sticky`, el `CONTENT_CODE` hardcodeado).
- **Limpieza reciente**: se eliminó `_get_codes.php` (exponía datos con conexión directa a RDS
  sin sesión) y se sacó `proctoring_config.php` con las llaves de AWS fuera de la raíz servible.
- **`.env` no versionado** (solo `.env.example`) y bloqueado por el `.htaccess` raíz.

---

## Plan priorizado

### Ahora (antes de cualquier despliegue)
- [x] **C1** — sesión + identidad de sesión + validación de archivo en `uploadAction`; ruta a `requiere_sesión = true`
- [x] **C2** — parametrizar el endpoint de autoservicio y dejar de devolver `email`/`cellphone_no`
- [x] **C3** — bindings en los 5 puntos con `course_code`, empezando por `checkPermissionEmployeeCourse`

### Esta semana
- [x] **A2** — comparación de `Origin` por host parseado en el router
- [x] **A1** — `hash_equals()` + límite de intentos (el cambio de modelo de credenciales se planifica aparte)
- [x] **A3** — escapar los dos `<?= ?>` del menú lateral
- [x] **A5** — quitar el silenciado global de errores en los endpoints

### Después
- [ ] **A4** — resolver el `CONTENT_CODE` de equsera y reactivar su tracking
- [x] **M5 / M6** — borrar `app/public/` muerto y los bloques-endpoint del helper; migrar los 2 endpoints vivos al router
- [x] **M4** — N+1 y caché de esquema
- [x] **M1, M2, M3** — cookie con flags, `action` sin `$_REQUEST`, errores de S3 sin detalle al cliente
- [x] **N1** — `hasSession()` para endpoints JSON
- [x] **B1** — `header(); exit;` explícito (2026-08-10 en `AccessService`; el resto del repo el 2026-08-12)
- [x] **M8** — SRI en los 19 recursos de CDN + borrado del script muerto
- [x] **N2** — XSS almacenado en las páginas públicas de autoservicio
- [x] **B3 / B4** — erratas y accesibilidad (2026-08-12)
- [ ] **M7** (bloqueado: escritura en el proyecto hermano), unificar versiones de Bootstrap, **B2** (pruebas)

---

## Correcciones aplicadas — 2026-08-10

### C1 · `app/controllers/ProctoringController.php:172-245`
- `check_session()` al entrar; el alumno sale de la sesión (`user_id`), ya no de `$_POST['emp_unique_id']`.
- El `unique_course_id` se resuelve en servidor con `AccessService::getUniqueCourseIdForEmployee()`
  a partir del `course_code`: si el alumno no está matriculado, se rechaza. Ya no se acepta el
  que mande el cliente.
- Validación del archivo: `is_uploaded_file()`, tamaño ≤ 5 MB (`MAX_UPLOAD_BYTES`) y tipo real
  por `mime_content_type()` restringido a PNG/JPG (`$ALLOWED_UPLOAD_MIME`).
- El `ContentType` que se guarda en S3 es el detectado, no `image/png` fijo.
- La ruta se deja en `false` **a propósito**: el controlador ya responde JSON suave; ponerla en
  `true` haría que el router redirigiera a `login.php` una llamada AJAX. El comentario en
  `app/routes.php:18-21` lo explica.

### C2 · `app/helpers/functions_helpers.php:293-330`
- Consulta preparada para `emp_unique_id` y `nivel1`.
- **Correo y celular se enmascaran en el servidor** con las nuevas
  `mask_contact_email()` / `mask_contact_phone()`, réplicas exactas de las funciones JS de las
  páginas de autoservicio. Como el algoritmo es idempotente, el front puede seguir aplicando su
  máscara y la pantalla se ve igual.
- `$id_employee` se castea a `int` antes de entrar en las consultas siguientes.

**Riesgo residual:** la máscara del teléfono deja visibles los 3 primeros y 3 últimos dígitos
(≈4 dígitos desconocidos → 10⁴ combinaciones). Mientras el celular siga siendo la contraseña
(A1), este endpoint sigue reduciendo el espacio de búsqueda: **A1 (límite de intentos) es
necesario para cerrar del todo la cadena.**

### C3 · 5 puntos
- `AccessService::checkPermissionEmployeeCourse()` — bindings; además ya no accede a `[0]` a ciegas.
- `CourseDashboardService::getProgressCourses()`, `getPorcentage()`, `getSurveyLink()` — bindings
  (incluidos `module_id` y las fechas). `getPorcentage()` devolvía "Undefined offset" con un
  código inexistente; ahora devuelve `false`.
- Endpoint `?progress_courses` del helper — bindings y el alumno forzado desde sesión.

### Bug adicional encontrado y corregido (funcionalidad)
El bloque `?progress_courses` estaba **duplicado** en el helper y el primero no hacía `exit`, así
que se ejecutaban los dos y la respuesta salía con dos JSON pegados:

```
{"course_progress":"0.0"}{"course_progress":null}
```

Los 14 `interactividad.js` que lo consumen usan `dataType: "json"`, así que el parseo fallaba y
el porcentaje del curso **nunca se pintaba**. Se eliminó la copia duplicada y se cierra con
`exit`. Verificado: la respuesta ahora es un único JSON válido.

### A1 (mitigación) · `app/views/pages/login.php` + `app/services/LoginThrottleService.php`
- **`hash_equals()`** en lugar de `==` para comparar la credencial: comparación estricta y en
  tiempo constante. Con `==`, dos cadenas numéricas se comparaban NUMÉRICAMENTE, así que un
  celular guardado como `0123456789` también aceptaba `123456789`.
- **Límite de intentos** (nuevo `LoginThrottleService`): 5 fallos por documento y 30 por IP en
  una ventana de 15 minutos. Se comprueba **antes** de consultar `employee_master`, para no
  filtrar por tiempo de respuesta si el documento existe. Un acierto limpia los fallos previos.
- **Registro de intentos** en la tabla `login_attempts` (se crea sola, mismo patrón que
  `create_proctoring_table()`; documentada en `app/sql/database_changes.sql`). Antes no quedaba
  ningún rastro de accesos ni de intentos fallidos.
- Un documento/empresa inexistente **también** cuenta como intento fallido: si no, enumerar
  documentos válidos seguiría siendo gratis.
- **`sess_regenerate(TRUE)`** al autenticar, contra fijación de sesión.
- Mensaje de bloqueo genérico ("Demasiados intentos, vuelva en N minutos"): no revela si el
  documento existe.

**Lo que NO cubre:** la contraseña sigue siendo el celular en texto plano en `employee_master`.
Esto es una mitigación, no el arreglo de fondo. Pendiente: contraseña propia con
`password_hash()` o código de un solo uso. El hallazgo A1 queda abierto en ese sentido.

**Riesgo de la comparación estricta:** un alumno cuyo celular guardado tenga ceros a la
izquierda y que antes entrara escribiéndolo sin ellos, ahora debe escribirlo exacto. En la base
local se verificó: **0 empleados** con `cellphone_no` que empiece por `0`. Conviene repetir esa
consulta en cada tenant antes de desplegar:
```sql
SELECT COUNT(*) FROM employee_master WHERE cellphone_no LIKE '0%';
```

### A2 · `router.php:21-45`
- Se compara el **host parseado** (`parse_url(..., PHP_URL_HOST)`) contra `HTTP_HOST` sin puerto,
  con `strcasecmp`. La versión anterior usaba `stripos($origin, $host)`, una búsqueda de
  subcadena: un atacante con el dominio `<host-legítimo>.evil.com` la superaba.
- Si **no llega ni `Origin` ni `Referer`, se rechaza**. Antes se dejaba pasar. Los navegadores
  envían `Origin` en todo POST (fetch, XHR y formularios), así que no afecta a ningún llamador
  legítimo del sitio; solo bloquea clientes hechos a mano.
- Verificado con 7 casos, incluidos los dos bypass (sufijo y prefijo) y el POST legítimo, que
  sigue pasando.

**Pendiente relacionado:** sigue sin haber token CSRF por sesión. La defensa en profundidad
natural aquí es `SameSite=Lax` en la cookie de sesión, pero esa configuración vive en
`amatia_capacitacion` (proyecto hermano), fuera del alcance de esta revisión.

### A3 · `widgets/sidenav.php:123` y `:146`
- `course_title` y `category_name` pasan por `htmlspecialchars(..., ENT_QUOTES, 'UTF-8')`.
- También se escapó el `href` del módulo y se castearon a `int` los ids del atributo `id=`.
- `course_code` y el parámetro `module` ahora van con `rawurlencode()`. Esto además corrige un
  fallo latente: `__my_simple_crypt__()` devuelve base64, que puede contener `+`; sin codificar,
  PHP lo interpreta como espacio al leer `$_GET` y el descifrado del módulo falla. Verificado el
  round-trip cifrar → URL → `parse_str` → descifrar con tres ids.

### A5 · `app/controllers/ProctoringController.php`
- Fuera `error_reporting(0)`. Ahora `prepareJsonOutput()` deja `display_errors = 0` (para que un
  warning no rompa el JSON) pero mantiene `error_reporting(E_ALL)` y `log_errors = 1`: los fallos
  se registran, que era lo que faltaba.
- Las dos acciones se envuelven en `runJsonAction()`, que captura cualquier `Throwable`, lo
  registra con `log_message('error', ...)` incluyendo archivo y línea, y responde un JSON estable
  sin filtrar detalles internos al cliente.

### Verificación ejecutada
Suite de 8 comprobaciones (todas OK): inyección `' OR '1'='1` neutralizada en las 4 funciones de
servicio, código legítimo sigue resolviendo, enmascarado correcto e idempotente. Además, contra
el endpoint real de autoservicio: con cédula válida devuelve
`{"id":"9406","email":"ale*******@*******.com","cellphone_no":"+57********220"}` y con payload de
inyección devuelve "No hay alumno registrado". Sin regresiones en homember (18 tarjetas) ni en
las páginas de captura.

---

## Correcciones aplicadas — 2026-08-11 (M5, M6, M4)

### M5 · `app/public/` — 10 archivos borrados
Quedaba solo `logout.php`, que sí tiene llamador (el shim `logout.php` de la raíz). Los otros
diez no tenían ninguno y además eran inalcanzables por HTTP (`app/.htaccess` responde 403):

- `progreso.php`, `update_progress.php` — su comentario decía ser el entry point de
  gaia-ambiental-v2, pero el `tracking.js` de ese curso apunta a
  `router.php?action=progress.get/update` y advierte explícitamente que no se usen estas rutas.
- `progreso_publico.php`, `update_progress_publico.php` — mismo caso con `progress.getPublic/updatePublic`.
- `adaptive_profile_context.php`, `adaptive_profile_diagnostic.php`, `adaptive_slide_context.php`,
  `course_access_gate.php`, `pre_evaluation_gate.php` — shims de una línea hacia controladores
  que ya se alcanzan por `router.php`.
- `data_user.php` — sin llamadores. Tenía además SQL interpolado (`course_code`, `mid` desde
  `$_GET`); estaba fuera de alcance por el `.htaccess`, pero era deuda esperando a que alguien
  moviera el archivo.

Se actualizaron los comentarios de `AccessGateController` y `AdaptiveController`, que seguían
describiendo esos shims como el camino de entrada.

### M6 · endpoints fuera del helper
`app/helpers/functions_helpers.php` tenía tres bloques `if(isset($_GET['...']))`. Como cientos de
páginas de `course_content/` hacen `require()` del helper, esos bloques convertían a **cualquier
página del sitio** en el endpoint: colgarle `?progress_courses` a la URL de un curso cortaba la
página y devolvía JSON. Ahora:

- `?adaptive_profile_context` — **borrado**. Cero llamadores y la acción `adaptive.context` ya
  hacía lo mismo por el router.
- `?progress_courses` → `router.php?action=dashboard.courseProgress` (nuevo `DashboardController`;
  la consulta vive en `CourseDashboardService::getSessionCourseProgress()`).
- `?courses_list_autoservicio` → `router.php?action=autoservicio.coursesList` (nuevos
  `AutoservicioController` y `AutoservicioService`, que recoge también el enmascarado de contacto).
- Se repuntaron los **14 `interactividad.js`** y las **2 páginas de autoservicio**.

**Compat temporal:** los `interactividad.js` se sirven sin cache-buster
(`<script src="assets/js/interactividad.js">`), así que un navegador puede seguir pidiendo la URL
vieja durante días. Quedan dos shims de tres líneas al final del helper que delegan en el mismo
controlador. **Borrarlos cuando las cachés hayan rotado** — con eso el helper deja de responder a
parámetros de URL por completo.

**Corrección al informe original:** migrar estos endpoints *no* habilita borrar el shim
`functions_helpers.php` de la raíz. Ese shim existe porque cientos de archivos de
`course_content/` hacen `require('.../functions_helpers.php')` para usar las **funciones**
(`check_session()`, `progress_courses()`, ...), no por los endpoints. Sigue siendo necesario.

### M4 · caché de esquema y N+1
- Nuevo `app/services/SchemaService.php`: `hasColumn()` / `hasTable()` con caché estática por
  request. Reemplaza los `SHOW COLUMNS`/`SHOW TABLES` sueltos de `CourseDashboardService`,
  `AccessService`, `AdaptiveProfileService` y el helper. La caché **no** se persiste entre
  requests a propósito: aplicar un `ALTER` en un tenant tiene que surtir efecto en la petición
  siguiente, sin vaciar cachés.
- `getEvaluationProgressByCourse()` memoizada por `(unique_course_id, id_employee)`. Era el N+1
  real y estaba **duplicado**: `homember.php` recorre la misma lista de cursos dos veces, una
  desde `getEstadisticasGenerales()` (panel del menú lateral) y otra desde `getMyCoursesList()`
  (tarjetas), así que cada curso se consultaba dos veces.
- De paso, la consulta a `training_activity_results` pasó a bindings.

**Medido** con el log general de MySQL local, alumno con 21 cursos vigentes, misma página
`homember.php` (100.183 bytes idénticos antes y después):

| | consultas totales | consultas de evaluación |
|---|---|---|
| antes (`CourseDashboardService` de HEAD) | 131 | 42 |
| después | 110 | 21 |

La caché de esquema no mueve la aguja en esta página concreta (6 `SHOW COLUMNS` antes y después:
no había repeticiones dentro del mismo request en esa ruta). Su valor es estructural —una sola
implementación del guard— y evita las repeticiones en las rutas donde varios servicios corren
juntos. El −16% medido viene de la memoización.

### Verificación ejecutada
Contra el sitio local, con sesión real y con el log de consultas de MySQL:

- `dashboard.courseProgress` y el shim viejo devuelven **el mismo JSON** (`{"course_progress":"75.00"}`).
- `autoservicio.coursesList` devuelve el listado con contacto enmascarado; con payload
  `' OR '1'='1` responde "No hay alumno registrado" (bindings intactos tras la migración).
- `code_course` con inyección → `{"course_progress":null}`.
- `adaptive.context` sigue respondiendo por el router tras borrar el bloque del helper.
- POST sin `Origin` → 403 (la defensa CSRF de A2 no se tocó).
- `homember.php`, `login.php`, `error-404.php` y las dos páginas de autoservicio: HTTP 200, sin
  warnings ni fatales en el HTML.
- `app/public/logout.php` sigue devolviendo 403 por `.htaccess`; `logout.php` de la raíz, 302.

---

## Correcciones aplicadas — 2026-08-11 (M1, M2, M3)

### M1 · `app/services/AccessService.php` — cookie `unique_course_code`
Pasa a opciones explícitas: `HttpOnly`, `SameSite=Lax`, `path=/` y `Secure` **condicionado a
HTTPS** (marcarla Secure en local, donde WAMP sirve por `http://`, haría que el navegador la
descartara).

El `path` es el cambio con más efecto práctico: antes se usaba el default, que es el directorio
del script que la escribe. Como `checkPermissionEmployeeCourse()` se llama desde
`course_content/<cliente>/<curso>/...`, el navegador iba acumulando una cookie distinta con el
mismo nombre por cada ruta, y el `unset($_COOKIE[...])` de la línea anterior no borra ninguna
(solo limpia el array de PHP).

**Verificado ejecutando:**
```
Set-Cookie: unique_course_code=MD1031-365; expires=…; Max-Age=604800; path=/; HttpOnly; SameSite=Lax
```

**Observación:** esta cookie es de **solo escritura**. El único lector en los dos proyectos es una
línea comentada en `login.php:3`. Se endureció porque era lo pedido, pero lo correcto de fondo es
borrarla: una cookie que nadie lee es superficie sin contrapartida.

### M2 · `router.php` y `AdaptiveController`
`$_REQUEST` sustituido por `$_GET`/`$_POST` explícitos. Qué entra en `$_REQUEST` lo decide
`request_order` del `php.ini`; si incluye `C`, una cookie `action` pisa el parámetro de la URL.

**Este servidor usa `request_order = GP`** (verificado en Apache, no solo en CLI), así que **no
era explotable aquí**. Pero es una garantía de configuración, no de código, y la de producción no
tiene por qué coincidir. Se añadió además un cast a string, para que `?action[]=x` no llegue como
array a `isset($routes[$action])`.

En `AdaptiveController::diagnosticAction()` el formulario se envía a la misma URL (`<form
method="post">` sin `action`), así que en el submit llegan GET **y** POST con los mismos nombres.
El nuevo `requestParam()` mira **POST primero**, para conservar exactamente la precedencia que
tenía `$_REQUEST` con `request_order="GP"`.

**Verificado:** `?action=…` y `action` por POST siguen resolviendo; una cabecera
`Cookie: action=dashboard.courseProgress` y un `?action[]=…` dan "Acción no encontrada".

### M3 · `app/controllers/ProctoringController.php`
Los cuatro `$e->getMessage()` que llegaban al cliente se sustituyen por un mensaje estable
(`No se pudo guardar la firma/la evidencia. Intente de nuevo.`) más `logThrowable()`, que registra
clase, mensaje, archivo y línea. Un `AwsException` trae nombre de bucket, región, endpoint y a
veces el motivo exacto del deny: era un mapa de la infraestructura servido a cualquiera que
provocara el error.

También se generalizaron los dos mensajes de "SDK de AWS no instalado", que revelaban la
dependencia de `amatia_capacitacion`. Los dos pares `catch (AwsException) / catch (Exception)` se
unificaron en `catch (Throwable)`, que es lo que ya hace `runJsonAction()`.

Ningún JS del repo depende del texto de esos mensajes (verificado por búsqueda).

**Límite de la verificación:** las rutas que NO tocan S3 se probaron ejecutando (sin sesión,
método incorrecto, datos incompletos, curso ajeno, tipo de archivo no permitido). **El `catch` de
S3 en sí solo está verificado por lectura de código**: provocarlo requeriría subir al bucket real
o romper la configuración de AWS, y ninguna de las dos cosas se hizo.

---

## Hallazgo nuevo — 2026-08-11

### N1 — `check_session()` rompe el JSON de los endpoints AJAX 🟠

- **Ubicación:** `app/services/AccessService.php:12` · `app/routes.php:22-24` ·
  `app/controllers/ProctoringController.php`
- **Verificación:** ejecutando.

`app/routes.php` deja `proctoring.upload` y `proctoring.saveSignature` con
`requiere_sesión = false` razonando que "el controlador ya maneja *sin sesión* con una respuesta
JSON suave". **No la maneja.** El controlador hace:

```php
if (!check_session()) { $this->json(false, 'Sesión no válida'); }
```

pero `AccessService::checkSession()` no devuelve `false` nunca: o devuelve `1`, o emite un
`Location:` y muere. La rama del `json()` es inalcanzable.

Resultado real de un POST sin sesión a `router.php?action=proctoring.upload`:

```
HTTP/1.1 302 Found
Location: http://localhost/amatia/courses_v2/login.php
Content-Length: 22
Content-Type: text/html; charset=UTF-8

Header redirect Failed
```

Es decir: la llamada AJAX recibe un 302 y un cuerpo de texto plano ("Header redirect Failed", el
`die()` de B1 disparándose siempre porque `header()` devuelve `null`), no JSON. El front lo lee
como error genérico y el alumno no se entera de que su sesión caducó — exactamente el modo de
fallo silencioso que A5 vino a corregir.

**Corrección propuesta.** Separar las dos responsabilidades:
```php
// AccessService
public static function hasSession(){
    $CI =& get_instance();
    return !empty($CI->session->userdata('employee_data'));
}
public static function checkSession(){        // para páginas navegables
    if (!self::hasSession()) {
        global $baseURL;
        header("Location: " . $baseURL . "login.php");
        exit;                                  // ← también cierra B1
    }
    return 1;
}
```
y en los controladores JSON usar `hasSession()`, que sí puede devolver `false`. Cierra B1 de paso.

**Nota:** la cabecera `Set-Cookie` de la sesión observada en esa misma respuesta confirma el
hallazgo pendiente sobre la cookie de sesión: `ama_mysess_capacitacion=…; path=/; HttpOnly` —
**sin `Secure` y sin `SameSite`**.

---

## Hallazgo nuevo — N2: XSS almacenado en las páginas públicas de autoservicio 🟠

- **Ubicación:** `autoservicio/autoservicio_marmato/index.php` y
  `autoservicio/autoservicio_segovia/index.php`
- **Estado:** ✅ **CORREGIDO** (2026-08-11)
- **Verificación:** ejecutando.

Apareció buscando dónde se pintaba `course_description` para M7. Las dos páginas montan las
tarjetas de resultado concatenando strings y las inyectan con `alertDiv.html(content)`, metiendo
sin escapar valores que salen de la base de datos — sobre todo `course_title`:

```js
content += "<h6 ...><strong>Curso: </strong>" + course.course_title + "</h6>";
content += "<a href='" + course.url + "' ...>Ir al curso</a>";
```

Es el mismo fallo que A3 (`widgets/sidenav.php`) pero **con más alcance**: sidenav exige sesión de
alumno; estas páginas son **públicas, sin login**. Un título de curso con
`<img src=x onerror=...>` se ejecuta en el navegador de cualquiera que consulte su estado.

Aparte, el botón de certificado interpolaba tres ids dentro de
`onClick="generateCertificates('${...}')"` — un atributo HTML que a su vez es código JS. Dos
contextos anidados, imposibles de escapar bien de una sola pasada.

**Corrección:**
- `escapeHtml()` en cada página (junto a las `maskEmail`/`maskPhoneNumber` que ya vivían ahí) y
  aplicado a todo valor que venga del servidor. `estado` no lo lleva: es un literal local.
- El `onClick` inline se sustituye por atributos `data-*` y un handler delegado, lo que **elimina**
  el anidamiento en vez de intentar escaparlo.
- El handler lee con `.attr()`, **no** con `.data()`: jQuery convierte a `Number` todo string que
  parezca numérico, y `unique_course_id_cryp` es base64 — uno que saliera todo dígitos con un cero
  delante perdería ese cero y rompería la URL del certificado.

**Verificado:** la `escapeHtml()` extraída del HTML realmente servido neutraliza los 7 casos de
prueba (`<img onerror>`, ruptura de atributo con comilla simple y doble, `&`, `null`, `undefined`)
y deja intacto un título normal.

---

## Correcciones aplicadas — 2026-08-11 (M8)

Enfoque: **`integrity` + `crossorigin="anonymous"`** sobre los mismos archivos que ya se servían.
No se cambió ninguna versión, así que no hay riesgo visual. Comprobado que los 5 hosts
(jsdelivr, code.jquery.com, cdnjs, stackpath, netdna) responden `Access-Control-Allow-Origin: *`,
sin lo cual SRI no funcionaría entre orígenes.

**19 recursos** en 5 archivos: `app/views/proctoring/photo_capture.php` (4),
`signature_capture.php` (2), `app/views/pages/error-404.php` (3) y las dos páginas de
autoservicio (5 cada una).

Detalles que no estaban en el hallazgo original:

- **`face-api.js` se carga por inyección dinámica de `<script>`**, no por etiqueta, así que el SRI
  va por propiedad (`script.integrity` + `script.crossOrigin`), no por atributo.
- **`maskdata.min.js` se borró en vez de asegurarse.** Devuelve **404** (comprobado) y **no se
  usa**: `maskEmail()` y `maskPhoneNumber()` están definidas en la propia página. Encima iba **sin
  versión** (`npm/maskdata/dist/`, un puntero a *latest*), que es justo lo que SRI no puede cubrir.
  Se borró también la línea comentada de `jquery-3.5.1.slim`.
- **`error-404.php` usaba URLs protocolo-relativas** (`//host/...`); ahora `https://` explícito.
- **Bug de orden corregido de paso:** esa página cargaba el JS de Bootstrap 3 **antes** que jQuery,
  que es justo lo que Bootstrap 3 exige. Lanzaba "Bootstrap requires jQuery" en consola desde
  siempre. Al tocar las dos líneas para el SRI se intercambiaron.

**Verificado ejecutando:** un script re-descarga cada uno de los 19 recursos y recalcula su sha384
contra el `integrity` escrito en el archivo → **19/19 coinciden**, 0 hashes mal pegados. Además,
las páginas siguen sirviendo 200 y `homember`/`login` no cambian.

### Por qué M7 queda bloqueado

`training_details.course_description` **no se escribe desde courses_v2**. El insert y el update
viven en `amatia_capacitacion/application/modules/training/controllers/Training.php:298` y `:393`
— el proyecto hermano, que esta revisión excluyó de su alcance.

Además, el campo se edita con un **editor rich-text** (Syncfusion `ejRTE`,
`training_view.php:1647`) y el admin lo pinta con `.html()`: el HTML es **intencional**, no un
accidente de pegado. "Limpiar en escritura" ahí significa sanear por **allowlist** de etiquetas,
no `strip_tags`, o se destruyen las descripciones existentes.

En courses_v2 el único consumidor es `app/views/pages/homember.php:290`, que **ya** hace
`strip_tags(html_entity_decode(...))` y luego `htmlspecialchars` — es decir, el lado de lectura ya
está cubierto. Lo que falta es la higiene del dato en origen, y eso es una decisión sobre el otro
proyecto.

---

## Correcciones aplicadas — 2026-08-12 (B1, B3, B4 + dos bugs)

Toda esta tanda se verificó bajo **PHP 7.4.33**, que es la versión de destino del proyecto. Ojo
con el entorno local: el Apache de WAMP sirve con **8.3.28** y el `php` del PATH es 8.2, así que
las verificaciones anteriores (10 y 11 de agosto) se hicieron sobre 8.3, no sobre 7.4. Para
comprobar en la versión real: `c:/wamp64/bin/php/php7.4.33/php.exe -l <archivo>` y, para páginas,
un `php7.4 -S` aparte (no aplica `.htaccess`, eso sigue siendo cosa de Apache).

### B1 · `header(); exit;` en todo el repo
De las 34 apariciones de `header(...) or die("Header redirect Failed")`, **16 estaban vivas**; las
otras 18 están dentro de bloques comentados (`/* ... */` de los `index.php` y la línea 4 de
`login.php`) y se dejaron como estaban.

- `login.php` (6), `index.php` de la raíz, `course_content/index.php`, los 7 `index.php` de
  cliente (`arismarmato`, `arissegovia`, `cursos`, `emerald`, `rekonecta`, `tecnitanques`,
  `transprensa`) y `app/public/logout.php`.
- En `login.php:99/103` (el redirect posterior a autenticar) **no había `exit`**: era el `die` el
  que cortaba. Al quitarlo hay que poner el `exit` explícito o el formulario de login se
  renderizaría debajo del 302.

**Verificado ejecutando** (servidor 7.4): el login correcto devuelve `302` con **cuerpo de 0
bytes**; antes devolvía `Header redirect Failed` como cuerpo del 302.

### B3 · erratas
`'Sin acesso'` → `'Sin acceso'` en `error-404.php`, y `Verificacion` → `Verificación` en el
`<title>` de `photo_capture.php`. Queda sin tocar "Reintentar camara" (`photo_capture.php:392`).

### B4 · accesibilidad
- `<title>` en `error-404.php`, que no tenía: la pestaña mostraba la URL. La página es un
  fragmento sin `<head>`, pero el parser sube ahí los `<title>/<link>/<style>/<script>` iniciales.
- `aria-hidden="true"` en los **30 iconos decorativos** de `widgets/sidenav.php` (7),
  `homember.php` (8) y `photo_capture.php` (15). Todos acompañan a texto visible, así que no
  aportan nada al lector de pantalla. `homember.php:153` ya lo tenía.
- **Pendiente de B4:** avisar de que el enlace de URL pública abre pestaña nueva
  (`homember.php:368`, que sí lleva ya `rel="noopener noreferrer"`).

### Bug corregido · `Undefined variable $module` en dos cursos
Reportado en `course_content/arismarmato/aris-sagrilaft-ptee-qhs-segovia/index.php:20`. La línea
`$url .= ... $module['module_id']` está **fuera** del `foreach`, así que con `$modules` vacío
`$module` no existe (y `$url` tampoco). **14 de los 16 `index.php`** que comparten ese bloque ya
tenían la guarda `if (!empty($module))`; faltaba en dos:

- `course_content/arismarmato/aris-sagrilaft-ptee-qhs-segovia/index.php`
- `course_content/cursos/aris_segovia_seguridad_vial/index.php`

Se les aplicó la misma guarda, idéntica a la de los otros catorce. **Límite de la verificación:**
no se logró reproducir por HTTP la condición de `$modules` vacío con los datos locales, así que el
arreglo se sustenta en equivalencia con los 14 archivos hermanos, no en un antes/después medido.
Nota aparte: en estos archivos `$url` no se usa en el HTML — es cálculo muerto.

### Bug corregido · warning en cada login
`login.php:57` leía `$info_instance["company_name"]` sin guarda. `get_list_subdomain()` devuelve
`[]` en local **para todos los hosts probados**, así que lanzaba un warning en cada intento de
login y la rama Aris Segovia/Emerald (que usa `emp_code` como contraseña en vez del celular)
nunca se activaba. Ahora se lee con `??`, igual que las líneas 207 y 274 del mismo archivo y que
`homember.php:135`. Si en producción esa función sí devuelve datos, el comportamiento no cambia.

---

## Limitaciones de esta revisión

- No se auditaron `vendor/`, `_backup/` ni `amatia_capacitacion` (proyecto hermano que aporta
  CodeIgniter, el SDK de AWS y la configuración de BD por subdominio).
- No se revisaron permisos de IAM del bucket S3 ni la configuración del servidor web más allá
  de los `.htaccess` del repo.
- No se ejecutaron pruebas de explotación; los hallazgos marcados como "lectura de código" no
  fueron confirmados con una petición maliciosa real.
- Solo se consultó la BD local (`courses_demo` y `courses_arismarmato`). El comportamiento en
  otros tenants puede diferir, sobre todo donde faltan columnas del esquema.
