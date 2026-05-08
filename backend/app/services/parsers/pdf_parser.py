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
                "geometry": pages_data
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
        
        # Patrones comunes en fichas EDGE
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

    def _process_vector_geometry(self, paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Procesa rutas vectoriales para identificar polígonos cerrados (áreas)."""
        detected = []
        for path in paths:
            # Si la ruta está cerrada y tiene un área razonable
            if path.get("type") == "f" or (path.get("fill") and path.get("rect")):
                rect = path["rect"]
                area_pts = rect.width * rect.height
                # Convertir puntos de PDF a m2 aproximados (Asumiendo escala 1:100 por defecto)
                # 1 pt = 1/72 inch. 1 inch = 0.0254 m.
                # Esta es una estimación que requiere calibración de escala
                area_m2 = (area_pts * (0.0254/72)**2) * 10000 
                if area_m2 > 0.5: # Ignorar formas pequeñas (ruido)
                    detected.append({
                        "type": "polygon",
                        "area_approx_m2": round(area_m2, 2),
                        "bounds": [rect.x0, rect.y0, rect.x1, rect.y1]
                    })
        return detected
