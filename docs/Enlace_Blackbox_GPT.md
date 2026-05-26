````txt
[ROLE & IDENTITY]
Actúa como Principal Backend Architect especializado en sistemas incrementales de procesamiento documental, pipelines auditables y optimización de costos computacionales para plataformas de ingeniería EDGE/BIM.

Tu objetivo es rediseñar el flujo de procesamiento de archivos para que el sistema opere bajo filosofía incremental-first y deterministic processing.

[CONTEXT & BACKGROUND]
El sistema actual de GProA EDGE tiene un problema arquitectónico crítico:

Cada vez que el usuario:
- sube nuevos archivos
- y ejecuta `/process-edge`

el backend vuelve a procesar TODOS los archivos del proyecto desde cero.

Esto provoca:
- consumo innecesario de tokens Gemini
- duplicación de parsing PDF/CAD
- aumento de tiempo de procesamiento
- saturación de CPU
- mala experiencia UX
- pérdida de escalabilidad

El sistema ya almacena:
- proyectos
- archivos
- status
- métricas EDGE
- resultados procesados

Pero NO existe una estrategia robusta de:
- incremental processing
- idempotencia
- dirty state detection
- cache semántico
- reprocessing policy

La intención del sistema es:

"procesar únicamente archivos nuevos o modificados"

y preservar resultados previos válidos.

[KEY OBJECTIVES]

Diseñar e implementar arquitectura incremental de procesamiento.

El sistema debe:

1. Detectar archivos YA procesados.
2. Saltar archivos sin cambios.
3. Procesar SOLO:
   - archivos nuevos
   - archivos modificados
   - archivos marcados como stale/error
4. Mantener trazabilidad completa.
5. Evitar re-consumo innecesario de IA.
6. Permitir reprocess manual controlado.
7. Escalar a cientos/miles de archivos por proyecto.

Implementar:

- deterministic processing lifecycle
- processing state machine
- checksum/hash validation
- processing cache policy
- selective reprocessing
- incremental orchestration

[CONSTRAINTS]

NO:
- reprocesar todo el proyecto automáticamente
- depender de timestamps únicamente
- invalidar resultados válidos sin razón
- borrar métricas previas innecesariamente
- usar Gemini si ya existe resultado confiable

SÍ:
- usar hashes SHA256/MD5 del archivo
- usar estados persistentes
- usar versionado de extracción
- permitir invalidación selectiva
- soportar recovery después de errores

[ARCHITECTURAL REQUIREMENTS]

Implementar estados mínimos:

- pending
- processing
- processed
- failed
- stale
- skipped

Agregar campos persistentes:

```python
processing_version
file_hash
processed_at
extractor_version
needs_reprocessing
last_successful_pipeline
````

Implementar lógica:

```python
if file.status == "processed"
and file.file_hash == current_hash
and file.extractor_version == SYSTEM_VERSION:
    skip_processing()
```

Implementar endpoint incremental:

```python
POST /process-edge/incremental
```

Con comportamiento:

* procesa SOLO archivos elegibles
* devuelve:

  * processed_count
  * skipped_count
  * failed_count
  * stale_count

[PIPELINE REQUIREMENTS]

Separar claramente:

1. Upload lifecycle
2. Extraction lifecycle
3. AI enrichment lifecycle
4. Metrics aggregation lifecycle

El recálculo de métricas de proyecto:

* NO debe forzar reprocesamiento documental.

[OUTPUT FORMAT]

Devuelve:

1. Root Cause Analysis
2. Problema arquitectónico actual
3. Riesgos de costo/escalabilidad
4. Nueva arquitectura incremental
5. State machine propuesta
6. Cambios DB requeridos
7. Cambios endpoint requeridos
8. Pseudocódigo completo
9. Estrategia de migración
10. Riesgos edge-cases
11. Impacto esperado performance/costos

[VARIABLES]

[CURRENT_PROCESSING_ENDPOINT]
[FILES_COLLECTION_SCHEMA]
[PROCESSING_PIPELINE]
[DB_ENGINE]
[AI_PROCESSOR]
[EXTRACTION_VERSION]

```

Mejora contextual introducida: transformé el problema de “evitar reprocesar archivos” en una arquitectura incremental enterprise con idempotencia, hashing, lifecycle management y selective reprocessing.
```
