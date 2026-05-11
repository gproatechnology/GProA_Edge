import fitz # PyMuPDF
import logging
import re
from typing import Dict, Any, List
from app.services.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class PDFParser(BaseParser):
    """Parser especializado en PDFs técnicos y fichas de producto."""

    def parse(self, file_path: str) -> Dict[str, Any]:
        """Extrae texto y parámetros técnicos del PDF."""
        try:
            doc = fitz.open(file_path)
            full_text = ""
            pages_data = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                full_text += text
                
                # Extracción de geometría vectorial (para planos)
                paths = page.get_drawings()
                vector_data = self._process_vector_geometry(paths)
                
                pages_data.append({
                    "page": page_num + 1,
                    "text_length": len(text),
                    "vector_shapes": len(paths),
                    "detected_areas": vector_data
                })

            return {
                "format": "PDF",
                "page_count": len(doc),
                "metadata": self.get_metadata(file_path),
                "extracted_parameters": self._extract_technical_params(full_text),
                "geometry": pages_data,
                "text_summary": {
                    "total_chars": len(full_text),
                    "detected_areas_from_text": self._extract_areas_from_text(full_text)
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
        except:
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

    def _extract_areas_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Busca menciones de áreas en el texto (ej: 'Local 1: 45.5 m2')."""
        areas = []
        patterns = [
            r'(?:Area|Superficie|Total):\s*(\d+(?:\.\d+)?)\s*(?:m2|m²|sqm)',
            r'(\d+(?:\.\d+)?)\s*(?:m2|m²|sqm)'
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                val = float(m.group(1))
                if val > 1.0: # Ignorar valores irrelevantes
                    areas.append({"value": val, "unit": "m2"})
        return areas

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
