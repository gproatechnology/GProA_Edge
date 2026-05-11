import ezdxf
import logging
import os
from typing import Dict, Any, List
from app.services.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class CADParser(BaseParser):
    """Parser especializado en archivos CAD (DXF/DWG)."""

    def _heuristically_parse_dwg(self, file_path: str) -> dict:
        """
        Advanced engineering fallback: Scan binary DWG for extractable text/metadata.
        Even without a full CAD engine, we can pull layers and annotations.
        """
        import re
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Extract printable strings (length > 4)
            # This captures layer names, block names, and text entities hidden in the binary
            strings = re.findall(br'[a-zA-Z0-9_\- ]{5,}', content)
            unique_strings = sorted(list(set(s.decode('ascii', errors='ignore').strip() for s in strings)))
            
            # Identify interesting keywords
            keywords = ["LUMINARIA", "LED", "AREA", "M2", "WATTS", "VOLTS", "AGUA", "WC", "NIVEL", "PISO"]
            found_keywords = [s for s in unique_strings if any(k in s.upper() for k in keywords)]
            
            # Heuristic Area Detection from text strings
            # Look for patterns like "AREA: 45.5" or "Habitacion 12.3 m2"
            detected_areas = []
            area_pattern = re.compile(r'(?:AREA|SUP|TOTAL)?[: ]*(\d+(?:\.\d+)?) ?(?:M2|m2|M\^2|MT2)', re.IGNORECASE)
            for s in unique_strings:
                match = area_pattern.search(s)
                if match:
                    val = float(match.group(1))
                    if val > 0.1:
                        # Try to find a name before the value
                        name_match = re.search(r'([a-zA-Z ]+)', s[:match.start()])
                        name = name_match.group(1).strip() if name_match else "Area Detectada"
                        detected_areas.append({
                            "nombre": name or "Area Detectada",
                            "area_m2": round(val, 2),
                            "type": "text_heuristic"
                        })

            return {
                "format": "DWG (Binary Inspected)",
                "status": "partial",
                "extracted_text_count": len(unique_strings),
                "detected_context": found_keywords[:20], # Top 20 relevant strings
                "message": "Archivo DWG inspeccionado mediante ingeniería binaria. Se extrajeron metadatos y etiquetas de texto.",
                "entities": {"polylines": 0, "text_notes": len(unique_strings)},
                "areas": detected_areas 
            }
        except Exception as e:
            return {"error": f"Heuristic scan failed: {str(e)}"}

    def parse(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            return {"error": "File not found"}

        ext = file_path.split('.')[-1].lower()
        
        if ext == 'dwg':
            # Check if it's actually a DXF renamed (common)
            try:
                with open(file_path, 'r', encoding='ascii', errors='ignore') as f:
                    if "SECTION" in f.read(100):
                        return self._parse_dxf(file_path)
            except:
                pass
            
            # If true binary DWG, use heuristic inspection
            return self._heuristically_parse_dwg(file_path)
            
        elif ext == 'dxf':
            return self._parse_dxf(file_path)
            
        return {"error": "Unsupported CAD format"}

    def _parse_dxf(self, file_path: str) -> Dict[str, Any]:
        """Realiza un análisis técnico completo del plano."""
        try:
            # Intentamos abrir como DXF
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            
            # Análisis expandido de entidades
            entities = {
                "polylines": len(msp.query('LWPOLYLINE')),
                "lines": len(msp.query('LINE')),
                "circles": len(msp.query('CIRCLE')),
                "texts": len(msp.query('TEXT MTEXT')),
            }

            return {
                "format": "DXF",
                "version": doc.dxfversion,
                "layers": self._get_layers(doc),
                "blocks": self._get_blocks(doc),
                "entities": entities,
                "areas": self._extract_areas(msp)
            }
        except Exception as e:
            logger.error(f"Error parseando archivo CAD {file_path}: {e}")
            return {
                "error": str(e), 
                "format": "CAD",
                "message": "Error al leer el archivo. Si es un DWG, intente guardarlo como DXF versión R12 o 2000 para un análisis completo de áreas."
            }

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrae metadatos básicos del encabezado del archivo."""
        try:
            doc = ezdxf.readfile(file_path)
            return {
                "author": doc.header.get("$PROJECTNAME", "Desconocido"),
                "units": doc.header.get("$INSUNITS", "Sin definir")
            }
        except:
            return {}

    def _get_layers(self, doc) -> List[str]:
        """Lista todas las capas presentes en el dibujo."""
        return [layer.dxf.name for layer in doc.layers]

    def _get_blocks(self, doc) -> Dict[str, int]:
        """Cuenta la frecuencia de cada bloque (ej: luminarias, mobiliario)."""
        counts = {}
        for block in doc.blocks:
            name = block.name
            if not name.startswith('*'): 
                counts[name] = counts.get(name, 0) + 1
        return counts

    def _extract_areas(self, msp) -> List[Dict[str, Any]]:
        """Intenta calcular áreas de polilíneas y otras formas cerradas."""
        areas = []
        # Polilíneas ligeras (las más comunes para áreas)
        for poly in msp.query('LWPOLYLINE POLYLINE'):
            if poly.is_closed:
                try:
                    area = poly.area()
                    if area > 0.1:
                        areas.append({
                            "nombre": f"Polilínea Capa: {poly.dxf.layer}",
                            "area_m2": round(area, 2),
                            "type": "polyline"
                        })
                except:
                    continue
        
        # Círculos (pueden representar columnas o tanques)
        for circle in msp.query('CIRCLE'):
            try:
                import math
                area = math.pi * (circle.dxf.radius ** 2)
                areas.append({
                    "nombre": f"Círculo Capa: {circle.dxf.layer}",
                    "area_m2": round(area, 2),
                    "type": "circle"
                })
            except:
                continue
                
        return areas
