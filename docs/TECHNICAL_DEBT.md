Aquí tienes el **Informe de Deuda Técnica** traducido al español, manteniendo el formato profesional y técnico original:

# Informe de Deuda Técnica - GProA EOSIS Edge

**Fecha:** 22-05-2026

**Alcance:** Backend (directorio `/backend/`)

---

## ALTA PRIORIDAD

### 1. Ausencia de Suite de Pruebas (Test Suite)

**Impacto:** Riesgo de regresiones, ausencia de puertas de calidad automatizadas.

**Ubicación:** Todo el directorio `/backend/`.

**Descripción:** No existe un directorio de pruebas. Es crítico para un despliegue CI/CD.

**Esfuerzo:** 8-16 horas.

### 2. Valores de Configuración Hardcodeados

**Impacto:** Vulnerabilidades de seguridad, fallos específicos por entorno.

**Ubicación:** `app/services/edge_processors.py` (nombres de modelos).

**Descripción:** Nombres de modelos como "gemini-2.5-flash", "gemini-flash-latest" deberían ser configurables.

**Esfuerzo:** 2 horas.

### 3. Funciones Grandes que Violan SRP (Principio de Responsabilidad Única)

**Impacto:** Mantenibilidad y testeabilidad.

**Ubicación:** `app/services/ai_service.py` (312 líneas), `app/services/edge_processors.py` (825 líneas).

**Descripción:** Las funciones exceden el límite recomendado de 50-100 líneas.

**Esfuerzo:** 4-8 horas de refactorización.

---

## PRIORIDAD MEDIA

### 4. Operaciones de Archivo Sincrónicas en Contexto Asíncrono

**Impacto:** Potencial bloqueo del bucle de eventos (event loop).

**Ubicación:** `app/services/parsers/excel_parser.py` (uso de openpyxl).

**Descripción:** Procesamiento de archivos de forma sincrónica en endpoints asíncronos.

**Esfuerzo:** 3-4 horas.

### 5. Falta de Type Hints (Anotaciones de tipo)

**Impacto:** Soporte de IDE, errores en tiempo de ejecución.

**Ubicación:** Todo el código, especialmente en los analizadores (parsers).

**Descripción:** Las funciones carecen de anotaciones de tipo adecuadas.

**Esfuerzo:** 4-6 horas.

### 6. Ausencia de Validación de Carga de Archivos

**Impacto:** Ataques de agotamiento de recursos.

**Ubicación:** `app/api/endpoints/files.py`.

**Descripción:** Falta validación de tamaño y tipo de archivo.

**Esfuerzo:** 2-3 horas.

---

## BAJA PRIORIDAD

### 7. Mensajes de Error Inconsistentes (Mezcla Español/Inglés)

**Impacto:** Experiencia del usuario.

**Ubicación:** Múltiples endpoints de la API.

**Descripción:** Algunos errores están en español y otros en inglés.

**Esfuerzo:** 1-2 horas.

### 8. Falta de Patrón de Repositorio

**Impacto:** Acoplamiento a la base de datos, dificultad para realizar pruebas.

**Ubicación:** `app/db/database.py`.

**Descripción:** Acceso directo a la base de datos disperso en los servicios.

**Esfuerzo:** 6-8 horas.

### 9. Sin Rate Limiting (Límite de tasa)

**Impacto:** Vulnerabilidades DoS.

**Ubicación:** `app/main.py`.

**Descripción:** Falta middleware para limitar la frecuencia de peticiones.

**Esfuerzo:** 2 horas.

---

## RESUELTO (de la sesión de auditoría)

| Problema | Estado | Fecha de resolución |
| --- | --- | --- |
| API Key en .env (hardcodeada) | ✅ Corregido | 22-05-2026 |
| CORS permisivo "*" | ✅ Corregido | 22-05-2026 |
| Bases de datos duales (gproa.db + gproa_edge.db) | ✅ Consolidadas → gproa_unified.db | 22-05-2026 |
| Cláusulas "except" vacías en database.py, files.py, projects.py, pdf_parser.py, docx_parser.py | ✅ Corregido | 22-05-2026 |
| Importaciones duplicadas en ai_service.py | ✅ Corregido | 22-05-2026 |
| Archivos de debug huérfanos en scratch/ (36 archivos) | ✅ Eliminados | 22-05-2026 |
| Archivos temporales en uploads/ (50+) | ✅ Eliminados | 22-05-2026 |
| Línea duplicada en main.py | ✅ Corregido | 22-05-2026 |
| .gitignore creado | ✅ Creado | 22-05-2026 |

---

## TAREAS PENDIENTES DETALLADAS

### Inmediatas (2-4 horas estimadas)

1. **Crear suite de pruebas básica**
   - Agregar `pytest-asyncio` a requirements.txt
   - Crear `backend/tests/` con tests para endpoints críticos
   
2. **Configuration constants refactoring**
   - Mover constantes de modelos Gemini a `config.py`
   - Agregar `GEMINI_MODEL_FLASH`, `GEMINI_MODEL_PRO` como variables de entorno

### Corto plazo (día 1-2)

3. **File upload validation**
   - Agregar `python-magic` para validación de tipos MIME
   - Limitar tamaño máximo (ej: 50MB)
   - Validar extensiones permitidas: `.pdf`, `.dxf`, `.dwg`, `.xlsx`, `.docx`, `.jpg`, `.png`

4. **Type hints en parsers**
   - `cad_parser.py`: Añadir hints a `parse()`, `_parse_dxf()`, `_extract_areas()`
   - `pdf_parser.py`: Añadir hints a `parse()`, `get_metadata()`

### Mediano plazo (día 3-5)

5. **Rate limiting**
   - Instalar `slowapi` o `starlette-limiter`
   - Aplicar límites: 100 req/min por IP

6. **Repository pattern**
   - Crear `app/repositories/files.py`
   - Crear `app/repositories/projects.py`
   - Refactorizar llamadas directas a `udb`

---

## Próximos pasos recomendados

1. **Crear branch de feature:** `git checkout -b tech-debt-payment`
2. **Empezar con tests** (máximo impacto, mínimo esfuerzo)
3. **Trabajar item por item** y marcar como ✅ resuelto