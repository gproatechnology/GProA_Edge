import fitz # PyMuPDF
import logging
import re
from typing import Dict, Any, List, Optional
from app.services.parsers.base_parser import BaseParser
from app.services.spatial_semantic_classifier import classifier, SemanticEvidence

logger = logging.getLogger(__name__)

class PDFParser(BaseParser):
    """Parser especializado en PDFs técnicos y fichas de producto."""

    def parse(self, file_path: str) -> Dict[str, Any]:
        """Extrae texto y parámetros técnicos del PDF."""
        try:
            doc = fitz.open(file_path)
            full_text = ""
            pages_data = []
            
            # Heurística: ¿Es un plano arquitectónico?
            filename_lower = file_path.lower()
            is_layout = any(word in filename_lower for word in ["layout", "plano", "drawing", "elevation", "floorplan"])
            
            # Fast path: text extraction
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Checar si la página es enorme (tamaño plano A0/Arch E > 2000 pts)
                rect = page.rect
                if rect.width > 2000 or rect.height > 2000:
                    is_layout = True
                    
                text = page.get_text()
                full_text += text + "\n"
                
                pages_data.append({
                    "page": page_num + 1,
                    "text_length": len(text),
                })
            
            # Limpiar texto para Gemini (quitar excesos de saltos de línea y ruido espacial)
            full_text = re.sub(r'\n{3,}', '\n\n', full_text).strip()
            
            # Extracción de TABLAS (Cuadros de áreas, cargas, etc.)
            tables_data = []
            if not is_layout:
                tables_data = self._extract_tables_with_fitz(doc)
            else:
                logger.info(f"Saltando extracción de tablas en {file_path} (heurística de layout activada).")
            
            return {
                "format": "PDF",
                "page_count": len(doc),
                "metadata": self.get_metadata(file_path),
                "extracted_parameters": self._extract_technical_params(full_text),
                "tables": tables_data,
                "content_text": full_text,
                "text_summary": {
                    "total_chars": len(full_text),
                    "detected_areas_from_text": self._extract_areas_from_text(full_text, tables_data)
                }
            }
        except Exception as e:
            logger.error(f"Error parseando PDF {file_path}: {e}")
            return {"error": str(e)}

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrae metadatos del archivo PDF."""
        try:
            doc = fitz.open(file_path)
            return doc.metadata
        except Exception:
            return {}

    def _extract_technical_params(self, text: str) -> Dict[str, Any]:
        """Busca patrones numéricos técnicos (Watts, Lumens, etc.) mediante RegEx."""
        params = {}
        patterns = {
            "watts": r'(\d+(?:\.\d+)?)\s*(?:W|Watts|Vatios)',
            "lumens": r'(\d+(?:\.\d+)?)\s*(?:lm|Lumens|Flujo)',
            "shgc": r'(?:SHGC|Factor Solar):\s*(\d\.\d+)',
            "u_value": r'(?:U-Value|Valor U|Valor-U):\s*(\d\.\d+)',
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                params[key] = float(match.group(1))
        return params

    def _extract_areas_from_text(self, text: str, tables_data: List[List[List[str]]] = None, pages_data: List = None) -> List[Dict[str, Any]]:
        """Busca menciones de áreas en el texto y en tablas extraídas con filtros de calidad."""
        areas = []
        
        # Helper: validate name quality
        def is_valid_name(name: str, val: float) -> bool:
            if not name or not name.strip():
                return False
            name = name.strip()
            # Reject truncated labels (2 chars or less, alphabetic only, likely OCR fragments)
            if len(name) <= 2 and name.replace(" ", "").isalpha():
                return False
            # Reject purely numeric names (numeric bleedthrough)
            if name.replace(".", "").replace("-", "").isdigit():
                return False
            # Reject names with OCR corruption patterns
            if any(c in name for c in ["\x00", "\ufffd"]):
                return False
            return True
        
        # PRIORITY 3: Filter extreme values that are building totals, not spaces
        def is_building_total(val: float) -> bool:
            return val > 10000 or val < 0.1
        
        # 1. Buscar en tablas (Cuadros de Áreas) - Muy confiable
        if tables_data:
            for table_idx, table in enumerate(tables_data):
                for row_idx, row in enumerate(table):
                    row_str = " ".join([str(c) for c in row if c])
                    match = re.search(r'(\d+[\.,]\d+)\s*(m2|m²|mt2)', row_str, re.IGNORECASE)
                    if match:
                        val = float(match.group(1).replace(',', '.'))
                        name = str(row[0]) if len(row) > 0 else "Espacio de Tabla"
                        
                        # PRIORITY 1: Name quality filter
                        if not is_valid_name(name, val):
                            continue
                        
                        # PRIORITY 3: Reject building totals masquerading as spaces
                        if is_building_total(val):
                            continue
                        
                        # PHASE 6: Observability - bbox from table cell
                        bbox = None
                        if pages_data and len(pages_data) > 0:
                            bbox = {"page": 1, "table_idx": table_idx, "row": row_idx}
                        
                        # PRIORITY 2: Row continuity check (shifted columns detection)
                        row_quality_score = 0.0
                        valid_row_entries = [c for c in row if c and str(c).strip() and len(str(c).strip()) > 1]
                        if len(valid_row_entries) >= 2:
                            row_quality_score = 1.0
                        
                        # Semantic classification with observability
                        context = {
                            "neighbor_text": row_str, 
                            "source": "table",
                            "neighboring_tokens": row[:5] if len(row) > 1 else [],
                            "row_quality_score": row_quality_score
                        }
                        evidence = classifier.classify(name, val, context)
                        
                        areas.append({
                            "nombre": name, 
                            "area_m2": val, 
                            "unit": "m2", 
                            "source": "table",
                            "semantic_evidence": evidence.to_dict(),
                            "bbox": bbox,
                            "parser_strategy": "table_extraction",
                            "quality_metrics": {
                                "valid_row_entries": len(valid_row_entries),
                                "name_length": len(name.strip()),
                                "passed_filters": True
                            }
                        })
        
        # 2. Buscar en texto plano
        patterns = [
            r'(?:Area|Superficie|Total|Local|Sala|Recamara)[: ]*(\d+[\.,]\d+)\s*(?:m2|m²|mt2|sqm)',
            r'([A-ZÁÉÍÓÚ][a-záéíóúÁÉÍÓÚA-Z ]{3,})[^0-9]{0,5}(\d+[\.,]\d+)\s*(?:m2|m²|mt2|sqm)',  # SPRINT: Name followed by value
            r'(\d+[\.,]\d+)\s*(?:m2|m²|mt2|sqm)'
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                # SPRINT: Handle named pattern (2 capture groups)
                if pattern.count('(') >= 2 and len(m.groups()) >= 2:
                    name = m.group(1).strip() if m.group(1) else "Area Detectada"
                    val = float(m.group(2).replace(',', '.'))
                    context_str = text[max(0, m.start()-50):m.end()+50].strip()
                else:
                    val = float(m.group(1).replace(',', '.'))
                    context_str = text[max(0, m.start()-100):m.end()+50].strip()
                    # SPRINT: Better name extraction - look for space keywords
                    name_match = re.search(r'([A-ZÁÉÍÓÚ][a-záéíóú\s]{3,})[:\s]*?(\d+[\.,]\d+)', context_str)
                    if name_match:
                        name = name_match.group(1).strip()
                    else:
                        name_match = re.search(r'([a-zA-ZáéíóúÁÉÍÓÚ ]{4,})[:\s]*$', context_str)
                        name = name_match.group(1).strip() if name_match else "Area Detectada"
                
                # PRIORITY: Reject building totals (>10000) and noise (<1.0)
                if val > 10000 or val < 1.0:
                    continue
                
                # PRIORITY 1: Name quality filter
                if not is_valid_name(name, val):
                    continue
                
                # PHASE 6: Observability - extraction trace
                context = {
                    "neighbor_text": context_str, 
                    "source": "text",
                    "neighboring_tokens": context_str.split()[:5]
                }
                evidence = classifier.classify(name, val, context)
                
                if not any(abs(a["area_m2"] - val) < 0.1 for a in areas):
                    areas.append({
                        "nombre": name, 
                        "area_m2": val, 
                        "unit": "m2", 
                        "source": "text",
                        "semantic_evidence": evidence.to_dict(),
                        "extraction_trace": {
                            "pattern_used": pattern[:50],
                            "text_position": m.start()
                        },
                        "parser_strategy": "regex_text",
                        "quality_metrics": {
                            "context_length": len(context_str),
                            "passed_filters": True
                        }
                    })
        return areas

    def _extract_tables_with_fitz(self, doc: fitz.Document) -> List[Any]:
        """Extrae tablas estructuradas usando PyMuPDF (mucho más rápido que pdfplumber)."""
        tables = []
        try:
            for page in doc:
                tabs = page.find_tables()
                if tabs:
                    for tab in tabs:
                        data = tab.extract()
                        # Limpiar celdas vacías (None) a strings vacíos
                        clean_data = [[c if c is not None else "" for c in row] for row in data]
                        tables.append(clean_data)
        except Exception as e:
            logger.error(f"Error extrayendo tablas con PyMuPDF: {e}")
        return tables

    def _process_vector_geometry(self, paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Procesa rutas vectoriales para identificar polígonos cerrados (áreas)."""
        detected = []
        for path in paths:
            # Capturar rectángulos o áreas rellenas
            if path.get("type") == "f" or (path.get("fill") and path.get("rect")):
                rect = path["rect"]
                # 1 pt PDF = ~0.00035 m (Escala 1:100) -> 1 pt2 = ~1.2e-7 m2
                # Ajustamos el factor de escala para que sea más realista en planos arquitectónicos
                area_pts = rect.width * rect.height
                area_m2 = area_pts * 0.05 # Factor de escala simplificado para calibrar
                
                if area_m2 > 1.0: 
                    detected.append({
                        "type": "polygon",
                        "area_approx_m2": round(area_m2, 2),
                        "bounds": [rect.x0, rect.y0, rect.x1, rect.y1]
                    })
        return detected
