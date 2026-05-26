# EOSIS Edge v1.0 — Deep Technical Audit Report (Parsing & Semantic Extraction Layer)

## 1. Extraction Pipeline — Full Runtime Flow

```
uploaded file
→ parser selection (extension check in TechnicalExtractionEngine._register_parsers)
→ RawDataProposal creation (in _parse_* methods)
→ SpatialSemanticClassifier.classify(token, value, context)
→ SemanticEvidence generation (dataclass with candidate_type, confidence, reasons)
→ EntityBuilder.build(proposal)
→ TechnicalEntity construction
→ ExtractionResult (collection of entities + metadata)
```

**Actual Classes and Methods:**
- `TechnicalExtractionEngine.extract()` (backend/app/services/technical_extraction_engine.py:39-52)
- `PDFParser.parse()` (backend/app/services/parsers/pdf_parser.py:13-65)
- `SpatialSemanticClassifier.classify()` (backend/app/services/semantic_evidence.py:89-203)
- `EntityBuilder.build()` (backend/app/services/entity_builder.py:25-70)
- `RawDataProposal` (backend/app/schemas/technical_entity.py:107-117)
- `ExtractionResult` (backend/app/schemas/technical_entity.py:180-190)

**Object Transformations:**
1. Parser returns raw dict with `format`, `content_text`, `tables`, `areas`
2. `SpatialSemanticClassifier` converts token+value+context → `SemanticEvidence`
3. `RawDataProposal` wraps candidate entity with provenance, confidence, semantic_evidence
4. `EntityBuilder.build()` → `TechnicalEntity` with uid, schema_version, processing_history

---

## 2. Parser Layer — Internal Mechanics

### PDFParser (backend/app/services/parsers/pdf_parser.py)

**Inputs:**
- `application/pdf` MIME type
- Layout detection heuristic: filename contains "layout", "plano", "drawing", "elevation", "floorplan" OR page dimensions > 2000pt

**Extraction Strategy:**
- Text extraction via `fitz.Page.get_text()` (PyMuPDF)
- Table extraction via `fitz.Page.find_tables()` (lines 227-241)
- Regex patterns for technical parameters (Watts, Lumens, SHGC, U-Value)
- Area extraction via 3 patterns (lines 168-172):
  - Explicit: `Area|Superficie|Local`... with value + unit
  - Named pattern: Spanish name + value + m2
  - Standalone number + m2

**Heuristics:**
- `is_layout` heuristic (lines 22-31): skips table extraction on layout sheets
- `is_valid_name()` (lines 95-108): rejects truncated labels (≤2 chars, alphabetic), numeric bleedthrough, OCR corruption (`\x00`, `\ufffd`)
- `is_building_total()` (lines 111-112): rejects values > 10000 or < 0.1
- Row quality scoring: `row_quality_score = 1.0` if ≥2 valid row entries (lines 139-141)
- Neighboring token extraction: `row[:5]` (line 147)

**Failure Modes:**
- Layout sheets skip table extraction entirely
- Empty OCR fragments filtered by name quality
- Large values (>10000) classified as global_area in semantic classifier

### CADParser (backend/app/services/parsers/cad_parser.py)

**Inputs:**
- `.dxf` and `.dwg` extensions
- For DWG: binary string extraction via regex (lines 28-37) for ASCII and UTF-16 strings
- DXF parsed via `ezdxf.readfile()`

**Extraction Strategy:**
- Polylines: `poly.is_closed` or inferred closed if endpoints < 50 units apart (lines 247-254)
- Circles: `math.pi * radius^2` (lines 268-277)
- HATCH areas: shoelace formula on edge points if `hatch.dxf.area` unavailable (lines 284-299)
- TEXT/MTEXT extraction with pattern matching (lines 143-188)
- DIMENSION extraction via `dim.get_measurement()` with fallback to `<>` replacement (line 149)

**Heuristics:**
- Area scale factors: mm → divide by 1,000,000 (line 117); cm → divide by 10,000 (line 118)
- Explicit unit patterns bypass scaling (lines 165-167)
- CAD spacing pattern matching: values [3.05, 6.10, 9.14, 12.19, 15.24, ...] (line 209)
- Layer-based category suggestion: "AGUA"/"EQAG" → WATER, "ILUM"/"LED" → ENERGY (lines 123-124)

**Failure Modes:**
- Binary DWG without text headers returns limited keyword extraction only
- Missing `INSUNITS` header defaults to "Undefined" units
- MPOLYGON parsing commented out (line 308, no indentation)

### ExcelParser (backend/app/services/parsers/excel_parser.py)

**Inputs:**
- `.xlsx`, `.xls` via pandas `ExcelFile`

**Extraction Strategy:**
- Pandas-based row iteration with aggressive number detection (lines 41-57)
- Pattern detection: `contains('AREAS BREAKDOWN|LEVEL|AREA')` (line 36)
- Row values summed if multiple numbers present

**Heuristics:**
- Skip rows containing "TOTAL", "AREA", "BREAKDOWN" in name (line 52)
- Sheet name in entity name: `f"Excel: {name}"` (line 58)

**Failure Modes:**
- Malformed Excel returns empty areas list (line 94)

### DocxParser (backend/app/services/parsers/docx_parser.py)

**Extraction Strategy:**
- Paragraph text extraction (lines 22-25)
- Table cell text via `python-docx` (lines 28-36)

**Failure Modes:**
- Empty document returns empty content_text

---

## 3. SemanticEvidence System

**Dataclass Structure** (backend/app/services/semantic_evidence.py:20-47):
```python
@dataclass
class SemanticEvidence:
    token: str
    candidate_type: SemanticType  # DIMENSION, GLOBAL_AREA, ARCH_SPACE, AREA_SUMMARY, UNKNOWN
    confidence: float = 0.95
    reasons: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "spatial_pattern"
```

**Reasoning Logic** (_infer_reasons, lines 37-47):
- `is_isolated_numeric`: matches `^\d+(\.\d+)?$`
- `matches_cad_pattern`: matches `^\d{1,3}\.\d{2}$`
- `has_area_context`: looks for m2/m²/sqm in neighbor_text
- `has_room_label_nearby`: looks for room/area/production keywords

**Confidence Assignment** (SpatialSemanticClassifier.classify):
| Candidate Type | Confidence | Reasons |
|---------------|------------|---------|
| DIMENSION | 0.97 | isolated_numeric, cad_spacing_pattern, no_area_context, no_space_nearby |
| GLOBAL_AREA | 0.95 | value_exceeds_threshold, building_total_candidate |
| ARCH_SPACE | 0.90 | contains_space_keyword |
| AREA_SUMMARY | 0.85 | summary_keyword_detected |
| UNKNOWN | 0.50 | no_classification_match |
| Filtered (truncated/numeric name) | 0.10 | quality_filter |

**Why discard()/hard_reject() Avoided:**
Per GPT point 4 in semantic_evidence.py header: "NO destruir evidencia tempranamente; solo degradar confianza" - evidence is preserved for TAL/UAKG arbitration.

**Propagation:** Evidence stored in `RawDataProposal.semantic_evidence` (line 116, technical_entity.py) → `EntityBuilder.build()` stores in `TechnicalEntity.semantic_metadata` (line 41, entity_builder.py).

---

## 4. SpatialSemanticClassifier

**Classification Rules** (semantic_evidence.py):

| Pattern | Condition | Result | Confidence |
|---------|-----------|--------|------------|
| Truncated label | `len(token) <= 2 and token.isalpha()` | UNKNOWN | 0.10 |
| Numeric bleedthrough | `token_clean.isdigit()` | UNKNOWN | 0.10 |
| CAD dimension | `DIMENSION_PATTERN.match` AND `has_spacing_pattern` AND NOT `has_m2_context` AND NOT `has_space_keyword` | DIMENSION | 0.97 |
| Global area | `value > 10000` | GLOBAL_AREA | 0.95 |
| Space keyword | any of SPACE_KEYWORDS in token_upper | ARCH_SPACE | 0.90 |
| Summary keyword | TOTAL/SUM/SUMMARY in token | AREA_SUMMARY | 0.85 |

**SPACE_KEYWORDS** (lines 82-87):
```python
{"ROOM", "AREA", "PRODUCTION", "OFFICE", "RESTROOM", "STORAGE",
 "MECHANICAL", "ELECTRICAL", "CORRIDOR", "LOBBY", "KITCHEN",
 "BATHROOM", "BEDROOM", "LIVING", "GARAGE", "PATIO",
 "EXTERNAL", "CARPARKING", "LIGHTING", "OPTIMIZING", "PUMPS", "HOUSE"}
```

**Thresholds:**
- `DIMENSION_PATTERN`: `^\d{1,3}\.\d{2}$` (1-3 digits, exactly 2 decimals)
- CAD spacing values (line 209): [3.05, 6.10, 9.14, 12.19, 15.24, 18.29, 21.34, 24.38, 27.43]
- Global area threshold: 10000 m² (line 162)
- Building total heuristic: `val > 10000 or val < 0.1` (pdf_parser.py:112)

---

## 5. Entity Construction Flow

```
ParserResult (raw dict)
→ RawDataProposal (lines 194-207, technical_extraction_engine.py)
→ EntityBuilder.build() (entity_builder.py:25-70)
→ TechnicalEntity (schemas/technical_entity.py:119-140)
→ ExtractionResult (schemas/technical_entity.py:180-190)
```

**Schema Contracts:**
- `RawDataProposal.type`: EntityType enum (AREA, DIMENSION, POLYLINE, etc.)
- `RawDataProposal.properties`: Dict with domain-specific fields (area_m2, nombre, layer)
- `RawDataProposal.provenance`: Provenance with source_file, parser_used, extraction_method
- `RawDataProposal.semantic_evidence`: Optional dict from SemanticEvidence.to_dict()
- `TechnicalEntity.uid`: Generated via `id_generator.generate(type_val, properties)` (line 36)

**Metadata Propagation:**
- `semantic_metadata["semantic_evidence"]` directly from proposal (line 41)
- `processing_history` appends construction trace with timestamp (lines 61-66)
- `schema_version = "1.0"` (SCHEMA_VERSION constant)

**Semantic Evidence Survival:**
Evidence preserved through `RawDataProposal.semantic_evidence` → `TechnicalEntity.semantic_metadata["semantic_evidence"]`. No degradation occurs in EntityBuilder (line 47 comment indicates TAL will use this).

---

## 6. Observability Layer

**Currently Implemented:**
- `bbox`: Page and table indices from table extraction (pdf_parser.py:133-135)
- `extraction_trace`: pattern_used, text_position (lines 215-218)
- `parser_strategy`: "table_extraction" or "regex_text" (lines 159, 219)
- `quality_metrics`: valid_row_entries, name_length, passed_filters (lines 160-164, 221-223)
- `neighboring_tokens`: row[:5] or context_str.split()[:5] (lines 147, 204)
- `provenance`: source_file, parser_used, extraction_method, source_layer, source_coordinates (Provenance schema)
- `semantic_reasoning_trace`: candidate_type, reasons, source (lines 148-152)
- `confidence_delta_trace`: original, calibrated, degradation_reasons (lines 143-147)

**Cannot Yet Be Audited:**
- Spatial relationship between extracted entities
- Cross-document consistency tracking
- Temporal extraction variance

---

## 7. Benchmark & Regression Infrastructure

**benchmark_runner.py** (tests/benchmark_runner.py):

**Golden Output Structure:**
```json
{
  "entities": [{uid, type, value, unit, name, confidence, ...}],
  "false_positives": [{uid, reason, subtype, ...}],
  "semantic_expectations": [{token, candidate_type, confidence, reasons}],
  "confidence_ranges": [],
  "extraction_trace": {parser_strategy, total_time_ms, entities_found}
}
```

**Metrics Calculation:**
- `semantic_precision` (line 255): `correct_semantic / total_entities`
- `false_positive_rate` (line 256): `false_positives / total_entities`
- `confidence_distribution` (lines 258-263): min/max/avg of entity confidences

**CORRECT_SEMANTIC Definition** (lines 238-244):
- `arch_space` or `area_summary` → correct
- `unknown` with space keywords in name → correct
- `dimension` and `global_area` with m2 unit → false positive

**False Positive Detection** (detect_false_positives, lines 16-98):
- DIMENSION with m2 unit → "ocr_corruption", "dimension_misclassified_as_area"
- GLOBAL_AREA with m2 unit → "unit_confusion", "global_area_misclassified_as_space"
- Empty/truncated/numeric names → respective rejection subtypes
- Extreme values (>100000 or <0.1) → "unit_confusion", "extreme_value"

**Current Output Files:**
- `benchmark_summary.json`: aggregate metrics
- `regression_deltas.json`: fp_by_reason, fp_by_pdf counts
- `confidence_statistics.json`: by_candidate_type, calibration_adjustments

---

## 8. Deterministic vs Probabilistic Boundaries

| Component | Type | Reasoning |
|-----------|------|-----------|
| DXF dimension extraction | Deterministic | `ezdxf` library reads exact DIMENSION entities |
| DXF area calculation | Deterministic | Shoelace formula on exact geometry |
| PDF text extraction | Deterministic | PyMuPDF extracts exact text from page |
| Regex pattern matching | Deterministic | Fixed patterns with no randomness |
| Table extraction (fitz) | Deterministic | PyMuPDF table detection |
| SemanticEvidence._infer_reasons | Heuristic | Regex-based boolean checks |
| SpatialSemanticClassifier.classify | Heuristic | Rule-based with hardcoded thresholds |
| CAD spacing pattern match | Heuristic | Exact value match against hardcoded list |
| Confidence values | Probabilistic | Enum-based but arbitrary assignments |
| Row quality scoring | Heuristic | Threshold at >=2 valid entries |
| Name validity filter | Deterministic | Boolean checks only |

**Uncertainty Entry Points:**
1. Semantic classifier assigns confidence 0.95-0.97 to heuristics without statistical validation
2. OCR corruption patterns are regex-matched, not image-analyzed
3. Building total threshold (10000) is heuristic, not normalized

---

## 9. Current Technical Debt (REAL EXISTING)

| Location | Debt Type | Description |
|----------|-----------|-------------|
| pdf_parser.py:243-261 | Large function | `_process_vector_geometry` extracts polygons but unused in main flow |
| semantic_evidence.py:64-72 | Optional typing | `to_dict()` returns Any instead of explicit Dict[str, Any] |
| technical_extraction_engine.py:110-108 | Async sync mismatch | Parser methods are sync but called via `await` with no `asyncio.to_thread` |
| cad_parser.py:308 | Code formatting | MPOLYGON block has incorrect indentation (continuation of HATCH block) |
| benchmark_runner.py:101-118 | Missing async | `extract_and_save_golden` is async but not awaited in main block (uses `asyncio.run`) |
| confidence_pipeline.py:38-47 | Optional typing | Dict values are floats but CONFIDENCE_LABELS uses float keys (0.99, 0.95, etc.) |
| entity_builder.py:49-47 | Incomplete implementation | Comment indicates TAL will use semantic evidence but no actual confidence degradation occurs |
| pdf_parser.py:90-225 | Large function | `_extract_areas_from_text` is 136 lines with nested functions |
| tests/test_semantic_classifier.py:33-43 | False positive gap | Test expects GLOBAL_AREA for `AREA-TOTAL` but classifier checks `value > 10000` not token |

---

## 10. Production Readiness Assessment

**Extraction Reliability:**
- DXF/DWG: HIGH - ezdxf provides deterministic geometry extraction
- PDF text: HIGH - PyMuPDF reliable for vector PDFs
- PDF tables: MEDIUM - depends on table structure quality

**Auditability:**
- FULL - Provenance tracking complete (source_file, parser_used, extraction_method)
- FULL - Semantic evidence traceable via extraction_trace, confidence_delta_trace
- FULL - Schema versioning at v1.0 constant

**Reproducibility:**
- DETERMINISTIC - Regex patterns and geometric calculations produce identical results
- Note: PyMuPDF table detection may vary by version

**Semantic Stability:**
- classifier.py:210 calculates spacing values with 0.01 tolerance (line 210: `abs(val - s) < 0.01`)
- SemanticEvidence._infer_reasons recalculated on each instantiation (not cached)

**False-Positive Resilience:**
- 6 filter types in detect_false_positives(): truncated, numeric bleedthrough, empty token, ocr corruption, extreme values
- Row quality scoring reduces low-confidence row propagation
- Current metrics: semantic_precision = 1.0, false_positive_rate = 0.0 (per user context)

**Parser Observability:**
- bbox tracking limited to page/table indices (no pixel coordinates)
- parser_strategy field correctly identifies "table_extraction" vs "regex_text"
- processing_history in TechnicalEntity tracks construction events

---

## IMPLEMENTED: EDGE Semantic Operationalization Layer (GPT STEP 1-6)

Los siguientes componentes fueron implementados según la dirección técnica de GPT:

### Unit Normalization Layer (`backend/app/services/unit_normalizer.py`)
- `UnitNormalizer.normalize_value()`: Convierte "15,24 m2", "15.24 m²", "25 ft²" a valor canónico
- Soporta: áreas (m²/sq.m/ft²), potencia (W/kW), caudal (GPM/l/min), eficiencia (lm/W)
- `normalize_entity()` aplica escalas (ft² → m² factor 0.092903)

### EDGE Strategy Mapper (`backend/app/services/edge_strategy_mapper.py`)
- Reglas determinísticas: lighting→EEM22, windows→EEM01, fixtures→WEM01, recycled→MEM01
- `map_entity()`: Señales en nombre/propiedades → estrategia EDGE
- `get_strategy_confidence()`: 0.85 (1 match) → 0.95 (múltiples matches)

### Semantic Validator (`backend/app/services/semantic_validator.py`)
- `ValidationEvidence` dataclass: issue_type, severity, entity_uid, confidence
- Detecta: áreas negativas, valores extremos (>100000), missing provenance
- `validate_collection()`: detecta entidades duplicadas (mismo nombre+área)

### Evidence Fusion (`backend/app/services/evidence_fusion.py`)
- `fusion_key()`: Agrupa entidades por tipo+nombre+área_bucket
- `consolidate_entities()`: Estrategias FIRST_WINS, HIGHEST_CONFIDENCE, MOST_COMPLETE
- Ejemplo: PDF "LED 120W" + Ficha "120W" + Plano "luminaire" → entidad única

### EDGE Dataset Export (`backend/app/services/edge_dataset_export.py`)
- `EDGEProjectDataset`: Export estructurado con entities, relations, strategy_mappings
- `export_to_edge_dataset()`: Pipeline completo con mapper + validator integrados
- Output listo para calculadoras EDGE y TAL/UAKG futuro

### Schema Extension (`backend/app/schemas/technical_entity.py`)
- Campo `relations: List[Dict[str, Any]]` agregado a TechnicalEntity
- Soporta relaciones: belongs_to_floor, associated_strategy, measured_from