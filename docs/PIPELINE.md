# Pipeline EOSIS — Documentación Técnica

## Visión General

El Pipeline es el **orquestador de procesamiento** que coordina 11 stages determinísticos para transformar archivos técnicos en un Knowledge Graph validado.

```
Archivos → Pipeline → Entities → Relationships → Validation → Compliance → Report
```

---

## Arquitectura

```
ProcessingPipeline
├── 11 Stages (secuenciales)
├── Event Bus (eventos)
├── Artifact Store (persistencia)
└── Context (datos compartidos)
```

---

## Stages del Pipeline

| # | Stage | Archivo | Qué hace |
|----|-------|---------|---------|
| 1 | **FileIngestionStage** | `stages.py` | Valida y normaliza archivos de entrada |
| 2 | **ParsingStage** | `stages.py` | Extrae datos con parsers (PDF, CAD, Excel) |
| 3 | **EntityExtractionStage** | `stages.py` | Convierte datos en entidades técnicas |
| 4 | **EntityNormalizationStage** | `stages.py` | Normaliza nombres y propiedades |
| 5 | **IdentityResolutionStage** | `stages.py` | Resuelve identidad de entidades (LHBS01 = LHBS-01) |
| 6 | **RelationshipInferenceStage** | `stages.py` | Infiere relaciones (área→luminaria, panel→circuito) |
| 7 | **SpatialAnalysisStage** | `stages.py` | Análisis espacial (contenimiento, proximidad) |
| 8 | **ValidationStage** | `stages.py` | Valida entidades contra reglas |
| 9 | **CrossDocumentReconciliationStage** | `stages.py` | Reconcilia datos entre documentos |
| 10 | **ComplianceScoringStage** | `stages.py` | Calcula score de cumplimiento EDGE |
| 11 | **ReportingStage** | `stages.py` | Genera reporte final |

---

## Stage 1: FileIngestionStage

**Propósito:** Validar archivos de entrada.

```python
class FileIngestionStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        # Valida que cada archivo tenga "path"
        # Normaliza: {path, type, size}
```

**Output:**
```python
{
    "files": [{"path": "...", "type": "pdf", "size": 1024}],
    "count": 1
}
```

---

## Stage 2: ParsingStage

**Propósito:** Extraer datos de archivos usando parsers.

```python
class ParsingStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        from app.services.technical_extraction_engine import engine
        # Usa TechnicalExtractionEngine que detecta tipo y aplica parser
```

**Output:**
```python
{
    "parsed": [
        {
            "file": "plano.dxf",
            "result": {
                "format": "DXF",
                "areas": [...],
                "layers": [...],
                "entities": [...]
            }
        }
    ],
    "count": 1
}
```

**Dependencias:** Todos los parsers (PDF, CAD, Excel, DOCX)

---

## Stage 3: EntityExtractionStage

**Propósito:** Convertir datos parseados en entidades técnicas.

```python
class EntityExtractionStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        # Extrae "entities" de cada parsed result
```

**Output:**
```python
{
    "entities": [
        {
            "id": "AREA_001",
            "type": "area",
            "measure": "DESIGN",
            "discipline": "ARCHITECTURAL",
            "properties": {"area_m2": 25.0}
        }
    ],
    "count": N
}
```

---

## Stage 4: EntityNormalizationStage

**Propósito:** Normalizar nombres de entidades.

```python
class EntityNormalizationStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        # Normaliza: id, type, measure, discipline
```

**Qué normaliza:**
- `entity_id` → `id`
- `entity_type` → `type`
- Estandariza `measure` (DESIGN, ENERGY, WATER)
- Estandariza `discipline` (ARCHITECTURAL, ELECTRICAL, MECHANICAL)

---

## Stage 5: IdentityResolutionStage

**Propósito:** Resolver identidad de entidades (distinguir vs fusionar).

```python
class IdentityResolutionStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        from app.services.entity_identity import EntityIdentityResolver
        resolver = EntityIdentityResolver()
        # Resuelve: LHBS01 = LHBS-01 = LHBS_01 → misma entidad
```

**Output:**
```python
{
    "identity_map": {
        "LHBS01": "LHBS_001",
        "LHBS-01": "LHBS_001",
        "LHBS_01": "LHBS_001"
    },
    "resolved_count": N
}
```

**Dependencias:** `entity_identity.py`

---

## Stage 6: RelationshipInferenceStage

**Propósito:** Inferir relaciones entre entidades.

```python
class RelationshipInferenceStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        from app.services.spatial_intelligence import SpatialReasoning
        # Infiere: área→luminaria, panel→circuito, HVAC→zona
```

**Output:**
```python
{
    "relationships": [
        {
            "type": "luminaire_area_coverage",
            "source": "LUM_001",
            "target": "AREA_001",
            "confidence": 0.85
        }
    ],
    "count": N
}
```

**Dependencias:** `spatial_intelligence.py`

---

## Stage 7: SpatialAnalysisStage

**Propósito:** Análisis espacial (contenimiento, proximidad).

```python
class SpatialAnalysisStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        # Detecta qué entidades están dentro de qué áreas
        # Usa Bounding Box (bbox)
```

**Output:**
```python
{
    "containment": [
        {"entity": "LUM_001", "contained_in": "AREA_001"},
        {"entity": "HVAC_001", "contained_in": "AREA_002"}
    ]
}
```

---

## Stage 8: ValidationStage

**Propósito:** Validar entidades contra reglas de negocio.

```python
class ValidationStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        from app.services.validation_engine import ValidationEngine
        val_engine = ValidationEngine()
        issues = val_engine.validate_entities(entities)
```

**Output:**
```python
{
    "issues": [
        {
            "severity": "error",
            "message": "Área sin valor de m2",
            "entity_id": "AREA_003"
        }
    ]
}
```

**Dependencias:** `validation_engine.py`

---

## Stage 9: CrossDocumentReconciliationStage

**Propósito:** Reconciliar datos entre múltiples documentos.

```python
class CrossDocumentReconciliationStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        from app.services.cross_document_reconciliation import CrossDocumentReconciler
```

**Output:**
```python
{
    "reconciled": True
}
```

**Dependencias:** `cross_document_reconciliation.py`

---

## Stage 10: ComplianceScoringStage

**Propósito:** Calcular score de cumplimiento EDGE.

```python
class ComplianceScoringStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        issues = context.get("issues", [])
        compliance_score = max(0.0, 1.0 - len(issues) * 0.1)
```

**Output:**
```python
{
    "compliance_score": 0.85,
    "issues_count": 2
}
```

---

## Stage 11: ReportingStage

**Propósito:** Generar reporte final.

```python
class ReportingStage(BaseStage):
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        result.output = {
            "summary": {
                "entities": len(context.get("entities", [])),
                "relationships": len(context.get("relationships", [])),
                "compliance_score": context.get("compliance_score", 0)
            }
        }
```

**Output:**
```python
{
    "summary": {
        "entities": 45,
        "relationships": 12,
        "compliance_score": 0.85
    }
}
```

---

## Uso del Pipeline

### Ejecución Completa

```python
from app.services.pipeline.pipeline import ProcessingPipeline

pipeline = ProcessingPipeline(project_id="PROY_001", revision="v1")

files = [
    {"path": "plano.dxf", "type": "dxf"},
    {"path": "ficha.pdf", "type": "pdf"}
]

result = await pipeline.run(files)
```

### Re-ejecutar desde un Stage

```python
# Re-ejecutar desde "validation"
result = await pipeline.re_run_from("validation")
```

---

## Eventos del Pipeline

| Evento | Cuándo |
|-------|--------|
| `PIPELINE_STARTED` | Inicio del pipeline |
| `STAGE_STARTED` | Inicio de cada stage |
| `STAGE_COMPLETED` | Fin de cada stage |
| `ARTIFACT_SAVED` | Persistencia de artifact |
| `PIPELINE_COMPLETED` | Fin del pipeline |

**Archivo:** `pipeline/events.py`

---

## Artifact Store

Cada stage guarda su output como JSON:

```
artifacts/
└── {project_id}/
    ├── file.ingestion.json
    ├── parsing.json
    ├── entity.extraction.json
    └── ...
```

**Archivo:** `pipeline/artifacts.py`

---

## Contratos (StageResult)

```python
class StageResult:
    stage_name: str
    status: StageStatus  # RUNNING, COMPLETED, FAILED
    output: Dict[str, Any]
    errors: List[str]
    confidence: float  # 0.0 - 1.0
    execution_time_ms: float
```

**Archivo:** `pipeline/contracts.py`

---

## Flujo Completo

```
Input Files
    ↓
[1] FileIngestion → {files: [...]}
    ↓
[2] Parsing → {parsed: [...]}
    ↓
[3] EntityExtraction → {entities: [...]}
    ↓
[4] EntityNormalization → {entities: normalized}
    ↓
[5] IdentityResolution → {identity_map: {...}}
    ↓
[6] RelationshipInference → {relationships: [...]}
    ↓
[7] SpatialAnalysis → {containment: [...]}
    ↓
[8] Validation → {issues: [...]}
    ↓
[9] CrossDocumentReconciliation → {reconciled: true}
    ↓
[10] ComplianceScoring → {compliance_score: 0.85}
    ↓
[11] Reporting → {summary: {...}}
    ↓
Output Final
```

---

## Próximos Pasos

- [ ] Documentar servicios individuales (audit_service, edge_processors)
- [ ] Documentar Knowledge Graph
- [ ] Agregar más stages si aplica