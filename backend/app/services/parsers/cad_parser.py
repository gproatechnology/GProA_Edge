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
            # UTF-8 / ASCII strings
            strings_ascii = re.findall(br'[a-zA-Z0-9_\- \.]{4,}', content)
            unique_strings = set(s.decode('ascii', errors='ignore').strip() for s in strings_ascii)
            
            # UTF-16 strings (Modern DWGs)
            strings_utf16 = re.findall(br'(?:[\x20-\x7E]\x00){4,}', content)
            for s in strings_utf16:
                try:
                    text = s.decode('utf-16le').strip()
                    if len(text) > 4: unique_strings.add(text)
                except: continue
            
            unique_strings = sorted(list(unique_strings))
            
            # Identify interesting keywords
            keywords = ["LUMINARIA", "LED", "AREA", "M2", "WATTS", "VOLTS", "AGUA", "WC", "NIVEL", "PISO", "CUARTO", "SALA", "LOCAL"]
            found_keywords = [s for s in unique_strings if any(k in s.upper() for k in keywords)]
            
            # Heuristic Area Detection from text strings
            detected_areas = []
            # Pattern improved for: "Area 12.3", "12.3 m2", "Habitacion: 15m2"
            area_pattern = re.compile(r'(?:AREA|SUP|TOTAL)?[: ]*(\d+[\.,]\d+) ?(?:M2|m2|m²|M\^2|MT2|SQM)', re.IGNORECASE)
            
            for s in unique_strings:
                match = area_pattern.search(s)
                if match:
                    val_str = match.group(1).replace(',', '.')
                    try:
                        val = float(val_str)
                        if 1.0 < val < 10000.0: # Filter out noise
                            # Try to find a name before the value or use the string context
                            name = s[:match.start()].strip(": -_")
                            if not name or len(name) < 2:
                                name = "Espacio Detectado"
                            
                            detected_areas.append({
                                "nombre": name,
                                "area_m2": round(val, 2),
                                "type": "text_heuristic"
                            })
                    except: continue

            return {
                "content_text": " ".join(unique_strings),
                "format": "DWG",
                "detected_areas": detected_areas,
                "found_keywords": found_keywords,
                "metadata": {},
                "extracted_parameters": {}
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
            except Exception:
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
            
            # 1. Detección de Unidades
            insunits = doc.header.get('$INSUNITS', 0)
            units_map = {0: "Sin definir", 1: "Pulgadas", 4: "Metros", 5: "Centímetros", 6: "Milímetros"}
            unit_name = units_map.get(insunits, "Desconocida")
            
            # Factor de escala (si es mm, dividir áreas por 1,000,000)
            area_scale = 1.0
            if insunits == 6: area_scale = 1.0 / 1000000.0
            elif insunits == 5: area_scale = 1.0 / 10000.0
            
            # 2. Análisis de Capas y Clasificación sugerida
            layers = self._get_layers(doc)
            suggested_category = "DESIGN"
            if any("AGUA" in l.upper() or "EQAG" in l.upper() for l in layers): suggested_category = "WATER"
            elif any(l.upper() in ["06MUREXT", "26VENT", "ILUM", "LED"] for l in layers): suggested_category = "ENERGY"
            
            # 3. Conteo de Bloques (Equipos, puertas, ventanas)
            blocks = self._get_blocks(doc)
            
            # 4. Extracción de Áreas con Escala
            raw_areas = self._extract_areas(msp)
            scaled_areas = []
            for a in raw_areas:
                a["area_m2"] = round(a["area_m2"] * area_scale, 2)
                scaled_areas.append(a)

            # 5. Análisis de Texto (Escaneo Permisivo)
            import re
            # Patrón 1: Explícito o con unidades comunes (m2, m, mts)
            area_pattern = re.compile(r'(?:AREA|SUP|TOTAL)?[: ]*(\d+[\.,]\d+)\s*(?:M2|m2|m²|MT2|SQM|M|MTS|MT)?', re.IGNORECASE)
            # Patrón 2: Cualquier número decimal solo (ej: 125.50)
            number_pattern = re.compile(r'(\d+[\.,]\d+)')
            
            texts = msp.query('TEXT MTEXT DIMENSION')
            text_content = []
            for t in texts:
                raw_content = ""
                if t.dxftype() == 'DIMENSION':
                    # Obtener el texto de la cota o su medida real si el texto es automático (<>)
                    raw_content = t.dxf.text if t.dxf.text and t.dxf.text != "<>" else f"{t.get_measurement():.2f}"
                else:
                    raw_content = t.dxf.text if hasattr(t.dxf, 'text') else t.text
                
                if raw_content: 
                    # Limpiar códigos de formato de AutoCAD (ej: \P, \fArial|b0...)
                    content = re.sub(r'\\[A-Z0-9].*?;', '', raw_content) # Limpiar estilos
                    content = content.replace('\\P', ' ').strip() # Limpiar saltos de línea
                    
                    text_content.append(content)
                    
                    # A) Intento 1: Buscar áreas explícitas (m2, mt, m)
                    match = area_pattern.search(content)
                    if match:
                        try:
                            val = float(match.group(1).replace(',', '.'))
                            # Si tiene unidad explícita (m2, mt, m), YA está en metros. 
                            # No aplicar el factor de escala del archivo (mm).
                            scaled_val = round(val, 2)
                            if 1.0 < scaled_val < 50000.0:
                                scaled_areas.append({
                                    "nombre": f"Etiqueta: {content[:20]}",
                                    "area_m2": scaled_val,
                                    "type": "text_label"
                                })
                        except: pass
                    
                    # B) Intento 2: Si el texto es SOLO un número (Heurístico)
                    elif number_pattern.match(content) and len(scaled_areas) < 50:
                        try:
                            val = float(content.replace(',', '.'))
                            # Aquí sí aplicamos escala porque es un número "mudo"
                            scaled_val = round(val * area_scale, 2)
                            if 5.0 < scaled_val < 10000.0:
                                scaled_areas.append({
                                    "nombre": f"Número en {t.dxf.layer}",
                                    "area_m2": scaled_val,
                                    "type": "heuristic_number"
                                })
                        except: pass

            return {
                "content_text": " ".join(text_content),
                "format": "DXF",
                "version": doc.dxfversion,
                "units": unit_name,
                "suggested_category": suggested_category,
                "layers": layers,
                "blocks": blocks,
                "entities": {
                    "polylines": len(msp.query('LWPOLYLINE')),
                    "lines": len(msp.query('LINE')),
                    "texts": len(texts)
                },
                "areas": scaled_areas,
                "text_summary": {
                    "sample_text": text_content[:10],
                    "total_texts": len(text_content)
                }
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
        except Exception:
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
        # 1. Polilíneas ligeras
        for poly in msp.query('LWPOLYLINE POLYLINE'):
            is_closed = poly.is_closed
            if not is_closed and len(poly) > 2:
                if hasattr(poly, 'get_points'):
                    points = list(poly.get_points())
                else:
                    points = list(poly.points())
                p1, p2 = points[0], points[-1]
                dist = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
                if dist < 50.0: is_closed = True

            if is_closed:
                try:
                    area = poly.area()
                    if area > 0.0001:
                        areas.append({
                            "nombre": f"Polilínea Capa: {poly.dxf.layer}",
                            "area_m2": area,
                            "type": "polyline"
                        })
                except: continue

        # 2. Círculos
        for circle in msp.query('CIRCLE'):
            try:
                import math
                area = math.pi * (circle.dxf.radius ** 2)
                areas.append({
                    "nombre": f"Círculo Capa: {circle.dxf.layer}",
                    "area_m2": area,
                    "type": "circle"
                })
            except: continue

        # 3. HATCH (Sombreados) - Muy común para áreas
        for hatch in msp.query('HATCH'):
            try:
                # Ezdxf puede calcular el área de muchos sombreados
                area = hatch.dxf.area # Algunos archivos tienen este atributo pre-calculado
                if not area:
                    # Si no, intentamos obtener el área de los bordes (si existen)
                    pass 
                
                if area and area > 0.1:
                    areas.append({
                        "nombre": f"Hatch (Sombreado) Capa: {hatch.dxf.layer}",
                        "area_m2": area,
                        "type": "hatch"
                    })
            except: continue
            
        # 4. MPOLYGON
        for mpoly in msp.query('MPOLYGON'):
            try:
                area = mpoly.area()
                if area > 0.1:
                    areas.append({
                        "nombre": f"MPolygon Capa: {mpoly.dxf.layer}",
                        "area_m2": area,
                        "type": "mpolygon"
                    })
            except: continue
                
        return areas
