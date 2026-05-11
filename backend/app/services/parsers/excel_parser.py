import pandas as pd
import logging
import os
from typing import Dict, Any, List
from app.services.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class ExcelParser(BaseParser):
    """Parser especializado en hojas de cálculo e inventarios."""

    def parse(self, file_path: str) -> Dict[str, Any]:
        """Lee el Excel y extrae las tablas de todas las hojas, buscando desgloses de áreas."""
        if not os.path.exists(file_path):
            return {"error": "File not found"}

        try:
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}
            found_areas = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Convertimos el DataFrame a una lista de diccionarios
                sheets_data[sheet_name] = {
                    "columns": list(df.columns),
                    "row_count": len(df),
                    "data_preview": df.head(50).to_dict(orient='records')
                }

                # Lógica de detección de AREAS BREAKDOWN
                is_area_table = False
                if df.astype(str).apply(lambda x: x.str.contains('AREAS BREAKDOWN|LEVEL|AREA', case=False)).any().any():
                    is_area_table = True

                if is_area_table:
                    # ESCANEO AGRESIVO: Buscar cualquier fila con un nombre y un número
                    for _, row in df.iterrows():
                        row_list = row.tolist()
                        # Buscar números positivos > 0.1 (que no sean la primera columna si es el Nivel como '1')
                        # Pero el nivel suele ser 'S1', 'PB', etc.
                        nums = [v for i, v in enumerate(row_list) if isinstance(v, (int, float)) and v > 0.1]
                        if nums:
                            # Buscar el nombre (primera celda de texto con contenido en la fila)
                            texts = [str(v).strip() for v in row_list if v and not isinstance(v, (int, float)) and len(str(v)) > 1]
                            name = texts[0] if texts else str(row_list[0]) if row_list[0] else "Espacio detectado"
                            
                            # Si es un total o un encabezado, lo saltamos
                            if "TOTAL" in name.upper() or "AREA" in name.upper() or "BREAKDOWN" in name.upper(): 
                                continue
                            
                            total_area = sum(nums)
                            if total_area > 0:
                                found_areas.append({
                                    "nombre": f"Excel: {name}",
                                    "area_m2": round(float(total_area), 2),
                                    "source": f"Sheet: {sheet_name}"
                                })

            # Clasificación forzada por nombre de archivo
            filename_upper = os.path.basename(file_path).upper()
            suggested_category = None
            if "AREA" in filename_upper or "BREAKDOWN" in filename_upper:
                suggested_category = "DESIGN"

            return {
                "format": "XLSX",
                "sheet_count": len(excel_file.sheet_names),
                "sheets": list(excel_file.sheet_names),
                "areas": found_areas,
                "suggested_category": suggested_category,
                "specialized_data": {
                    "tipo": "Desglose de Áreas (Excel)",
                    "mensaje": f"Se detectaron {len(found_areas)} registros de área." if found_areas else "No se detectaron tablas de áreas claras.",
                    "status": "success" if found_areas else "warning"
                }
            }
        except Exception as e:
            logger.error(f"Error parseando Excel {file_path}: {e}")
            return {"error": str(e)}

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrae metadatos básicos del archivo Excel."""
        return {"filename": os.path.basename(file_path)}
