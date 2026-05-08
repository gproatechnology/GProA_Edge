import pandas as pd
import logging
from typing import Dict, Any, List
from app.services.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class ExcelParser(BaseParser):
    """Parser especializado en hojas de cálculo e inventarios."""

    def parse(self, file_path: str) -> Dict[str, Any]:
        """Lee el Excel y extrae las tablas de todas las hojas."""
        try:
            # Leemos todas las hojas
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                # Convertimos el DataFrame a una lista de diccionarios (máximo 50 filas para el resumen)
                sheets_data[sheet_name] = {
                    "columns": list(df.columns),
                    "row_count": len(df),
                    "data_preview": df.head(50).to_dict(orient='records')
                }

            return {
                "format": "XLSX",
                "sheet_count": len(excel_file.sheet_names),
                "sheets": list(excel_file.sheet_names),
                "content": sheets_data
            }
        except Exception as e:
            logger.error(f"Error parseando Excel {file_path}: {e}")
            return {"error": str(e)}

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrae metadatos básicos del archivo Excel."""
        # Pandas no extrae metadatos de autor por defecto, se requiere openpyxl directo
        return {"filename": file_path.split("/")[-1]}
