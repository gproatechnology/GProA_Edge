import ezdxf
import logging
from typing import Dict, Any, List
from app.services.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class CADParser(BaseParser):
    """Parser especializado en archivos CAD (DXF/DWG)."""

    def parse(self, file_path: str) -> Dict[str, Any]:
        """Realiza un análisis técnico completo del plano."""
        try:
            # Detectar si es un archivo DWG binario
            with open(file_path, "rb") as f:
                header = f.read(6)
                if header.startswith(b"AC"): # Firma de AutoCAD DWG
                    version = header.decode("ascii", errors="ignore")
                    return {
                        "format": "DWG",
                        "status": "unsupported_binary",
                        "version": version,
                        "message": "Archivo DWG binario detectado. Para análisis automático de áreas, por favor guarde el archivo como DXF (R12 o superior) en AutoCAD y vuelva a subirlo."
                    }

            # Intentamos abrir como DXF
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            
            return {
                "format": "DXF",
                "version": doc.dxfversion,
                "layers": self._get_layers(doc),
                "blocks": self._get_blocks(doc),
                "entities_count": len(msp),
                "areas": self._extract_areas(msp)
            }
        except Exception as e:
            logger.error(f"Error parseando archivo CAD {file_path}: {e}")
            return {"error": str(e), "message": "Asegúrese de que el archivo sea un DXF válido o compatible."}

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrae metadatos básicos del encabezado del archivo."""
        try:
            doc = ezdxf.readfile(file_path)
            return {
                "author": doc.header.get("$PROJECTNAME", "Desconocido"),
                "created": doc.header.get("$TDCREATE", "Desconocido"),
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
            if not name.startswith('*'): # Ignorar bloques internos anónimos
                counts[name] = counts.get(name, 0) + 1
        return counts

    def _extract_areas(self, msp) -> List[Dict[str, Any]]:
        """Intenta calcular áreas de polilíneas cerradas."""
        areas = []
        # Buscamos polilíneas que podrían representar locales
        for poly in msp.query('LWPOLYLINE'):
            if poly.is_closed:
                try:
                    area = poly.area()
                    areas.append({
                        "layer": poly.dxf.layer,
                        "area_m2": round(area, 2),
                        "is_closed": True
                    })
                except:
                    continue
        return areas
