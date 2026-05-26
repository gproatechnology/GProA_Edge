# Parsers EOSIS — Documentación Técnica

## Visión General

Los parsers son la **capa de extracción determinística** que extrae datos estructurados de archivos técnicos (PDF, CAD, Excel, DOCX, imágenes).

```
Archivo Entrada → Parser → Datos Estructurados → Edge Processors → IA → Base de Datos
```

---

## Lista de Parsers

| Parser | Archivo | Formatos | Qué Extrae |
|--------|---------|----------|------------|
| **PDFParser** | `pdf_parser.py` | `.pdf` | Texto, tablas, parámetros técnicos (Watts, Lumens, áreas) |
| **CADParser** | `cad_parser.py` | `.dxf`, `.dwg` | Capas, bloques, áreas geométricas, texto |
| **ExcelParser** | `excel_parser.py` | `.xlsx`, `.xls` | Áreas breakdown, tablas, datos |
| **DOCXParser** | `docx_parser.py` | `.docx` | Texto de documentos |
| **DXFDimensionParser** | `dxf_dimension_parser.py` | `.dxf` | Cotas/dimensiones específicas |
| **ImageProcessor** | `image_processor.py` | `.png`, `.jpg`, `.jpeg` | Imágenes para análisis multimodal |

---

## PDFParser

**Ubicación:** `backend/app/services/parsers/pdf_parser.py`

**Dependencias:** `PyMuPDF` (fitz)

### Métodos

```python
def parse(file_path: str) -> Dict[str, Any]
def get_metadata(file_path: str) -> Dict[str, Any]
```

### Campos Retornados

| Campo | Descripción |
|-------|------------|
| `format` | "PDF" |
| `page_count` | Número de páginas |
| `extracted_parameters` | Watts, Lumens, SHGC, U-Value (via RegEx) |
| `tables` | Tablas estructuradas (PyMuPDF) |
| `content_text` | Texto limpio para IA |
| `text_summary.detected_areas_from_text` | Áreas detectadas en texto/tablas |

### Lógica Especial

- **Heurística de layout**: Si el archivo contiene "layout", "plano", "drawing", "elevation" → salta tablas
- **Detección de tablas**: Usa `page.find_tables()` de PyMuPDF (más rápido que pdfplumber)
- **Parámetros técnicos**: RegEx para Watts, Lumens, SHGC, U-Value
- **Filtrado de nombres (SPRINT Semantic Precision)**: 
  - Rechaza etiquetas truncadas ≤ 2 caracteres como OCR noise
  - Filtra valores numéricos puros (bleedthrough) que no son espacios válidos
  - Rechaza valores > 10000 m² como GLOBAL_AREA (no espacios)

---

## CADParser

**Ubicación:** `backend/app/services/parsers/cad_parser.py`

**Dependencias:** `ezdxf`

### Métodos

```python
def parse(file_path: str) -> Dict[str, Any]
def get_metadata(file_path: str) -> Dict[str, Any]
def extract_dimensions(file_path: str, layer_filter: str = None) -> list
def extract(file_path: str) -> ExtractionResult
```

### Campos Retornados (parse)

| Campo | Descripción |
|-------|------------|
| `format` | "DXF" o "DWG" |
| `version` | Versión DXF (ej: "R2018") |
| `units` | mm, cm, m, pulgadas |
| `layers` | Lista de capas |
| `blocks` | Frecuencia de bloques |
| `entities` | Conteo de polylines, lines, texts |
| `areas` | Áreas calculadas de polilíneas, círculos, hatch |
| `suggested_category` | ENERGY, WATER, DESIGN (por capas) |

### Métodos Adicionales

| Método | Descripción |
|--------|------------|
| `extract()` | Retorna `ExtractionResult` con entidades estandarizadas |
| `extract_dimensions()` | Lista cotas/dimensiones con coordenadas |

### Lógica Especial

- **DWG binario**: Si no puede leer como DXF → escaneo heurístico de strings
- **Escala de áreas**: Ajusta según unidades del archivo (mm → m² divide por 1,000,000)
- **Detección de áreas**: 
  - Geométricas (polilíneas cerradas, círculos, hatch)
  - Texto (etiquetas con m²)
  - Heurístico (números solos)

---

## ExcelParser

**Ubicación:** `backend/app/services/parsers/excel_parser.py`

**Dependencias:** `pandas`, `openpyxl`

### Métodos

```python
def parse(file_path: str) -> Dict[str, Any]
def get_metadata(file_path: str) -> Dict[str, Any]
```

### Campos Retornados

| Campo | Descripción |
|-------|------------|
| `format` | "XLSX" |
| `sheet_count` | Número de hojas |
| `sheets` | Lista de nombres de hojas |
| `areas` | Áreas detectadas (nombre, m², fuente) |
| `content_text` | Texto plano de todas las hojas (para IA) |
| `suggested_category` | "DESIGN" si contiene "AREA" o "BREAKDOWN" |
| `specialized_data` | Tipo y status de extracción |

### Lógica Especial

- **Detección de áreas**: Busca filas con números > 0.1 y texto en la misma fila
- **Area Breakdown**: Detecta si hay keywords "AREAS BREAKDOWN", "LEVEL", "AREA"
- **Preview**: Primeros 50 registros por hoja para IA

---

## DOCXParser

**Ubicación:** `backend/app/services/parsers/docx_parser.py`

**Dependencias:** `python-docx`

### Métodos

```python
def parse(file_path: str) -> Dict[str, Any]
def get_metadata(file_path: str) -> Dict[str, Any]
```

### Campos Retornados

| Campo | Descripción |
|-------|------------|
| `format` | "DOCX" |
| `paragraph_count` | Total de párrafos |
| `paragraphs` | Lista de párrafos |
| `table_count` | Total de tablas |
| `tables` | Tablas detectadas |
| `content_text` | Texto completo |
| `metadata` | Metadatos del documento (autor, fecha, título)

---

## DXFDimensionParser

**Ubicación:** `backend/app/services/parsers/dxf_dimension_parser.py`

**Dependencias:** `ezdxf`

### Propósito

Extrae **cotas específicas** de archivos DXF para validación de medidas.

### Métodos

```python
def parse(file_path: str) -> Dict[str, Any]
def get_metadata(file_path: str) -> Dict[str, Any]
def extract(file_path: str) -> ExtractionResult
def get_dimensions_by_layer(file_path: str, layer_name: str) -> List[Dict[str, Any]]
```

### Retorna (parse)

```python
# parse() retorna:
{
    "format": "DXF",
    "version": "AC1027",
    "units": "Millimeters",
    "layers": ["0", "COTAS", ...],
    "dimensions": [
        {
            "value": 2.50,        # Valor de la cota
            "layer": "COTAS",     # Capa
            "type": 0,           # Tipo de cota (0=Aligned, 1=Rotated, 2=Radial, etc.)
            "type_name": "Aligned",
            "handle": "ABC123",   # Handle AutoCAD
            "points": {           # Coordenadas estructuradas
                "origin": [x, y],
                "defpoint1": [x, y],
                "defpoint2": [x, y]
            }
        }
    ],
    "dimension_count": 15
}
```

> **Nota:** El método `extract()` retorna `ExtractionResult` con entidades estandarizadas listas para el EntityBuilder.

---

## ImageProcessor

**Ubicación:** `backend/app/services/parsers/image_processor.py`

**Dependencias:** `Pillow`, `pdf2image`

### Propósito

Procesa imágenes para análisis multimodal (CAD como imagen).

### Métodos

```python
async def process(file_path: str, hint_measure: str = "") -> Dict[str, Any]
def convert_pdf_to_images(pdf_path: str, dpi: int = 300) -> list
```

### Retorna (process)

```python
{
    "classification": {
        "category_edge": "ENERGY|WATER|MATERIALS|DESIGN",
        "measure_edge": "EEMXX|WEMXX|etc",
        "doc_type": "ficha_tecnica|fotografia|plano",
        "confidence": 0.0-1.0,
        "drawing_title": "string detectado en el cajetin"
    },
    "extracted_parameters": {
        "watts": null,
        "lumens": null,
        "marca": "string",
        "modelo": "string"
    },
    "detected_text": "Resumen del texto detectado",
    "message": "Descripción de lo encontrado"
}
```

---

## BaseParser (Abstracto)

**Ubicación:** `backend/app/services/parsers/base_parser.py`

Todos los parsers heredan de esta clase base:

```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        pass
```

---

## Flujo de Uso

### Directo

```python
from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.cad_parser import CADParser
from app.services.parsers.excel_parser import ExcelParser

parser = PDFParser()
result = parser.parse("archivo.pdf")

parser = CADParser()
result = parser.parse("plano.dxf")

parser = ExcelParser()
result = parser.parse("areas.xlsx")
```

### Via AuditService

El `AuditService` detecta el tipo de archivo y usa el parser apropiado automáticamente.

---

## Errores Comunes

| Error | Causa | Solución |
|-------|------|---------|
| `Unsupported CAD format` | DWG binario sin soporte | Guardar como DXF R12/2000 |
| `Error al leer el archivo` | Archivo corrupto | Verificar en AutoCAD |
| `File not found` | Path incorrecto | Verificar ruta |

---

## Próximos Pasos

- [ ] Documentar Pipeline de procesamiento
- [ ] Documentar Edge Processors
- [ ] Agregar más parsers (si aplica)