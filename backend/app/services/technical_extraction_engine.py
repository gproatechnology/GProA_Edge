"""
Technical Extraction Engine for EDGE Certification.
Orchestrates deterministic parsing with optional AI assistance.
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from app.schemas.technical_entity import (
    ExtractionResult, TechnicalEntity, MeasureType, Discipline, EntityType
)
from app.services.confidence_pipeline import ExtractionConfidence

logger = logging.getLogger(__name__)


class TechnicalExtractionEngine:
    """
    Deterministic engine for technical data extraction from construction documents.
    Uses AI only for classification and reconciliation, not for rule-based calculations.
    """
    
    def __init__(self):
        self.parsers = {}
        self._register_parsers()
    
    def _register_parsers(self):
        """Register available parsers by file extension."""
        self.parsers = {
            '.dxf': self._parse_dxf,
            '.dwg': self._parse_cad,
            '.pdf': self._parse_pdf,
            '.xlsx': self._parse_excel,
            '.xls': self._parse_excel,
            '.docx': self._parse_docx,
        }
    
    async def extract(self, file_path: str, content: str = None) -> ExtractionResult:
        """
        Main extraction method - routes to appropriate parser.
        
        Args:
            file_path: Path to source file
            content: Optional pre-extracted text content
            
        Returns:
            Standardized ExtractionResult
        """
        ext = Path(file_path).suffix.lower()
        parser = self.parsers.get(ext)
        
        if not parser:
            return ExtractionResult(
                measure=MeasureType.GENERAL,
                discipline=Discipline.DESIGN,
                warnings=[f"Unsupported file type: {ext}"]
            )
        
        result = await parser(file_path, content)
        return result
    
    async def _parse_dxf(self, file_path: str, content: str = None) -> ExtractionResult:
        """Extract from DXF files using ezdxf."""
        from app.services.parsers.dxf_dimension_parser import DxfDimensionParser
        from app.schemas.technical_entity import Provenance
        from datetime import datetime

        result = ExtractionResult(
            measure=MeasureType.DESIGN,
            discipline=Discipline.ARCHITECTURAL,
            confidence=ExtractionConfidence.DXF_LAYER_EXACT.value
        )

        try:
            parser = DxfDimensionParser()
            dxf_data = parser.parse(file_path)

            for dim in dxf_data.get("dimensions", []):
                provenance = Provenance(
                    source_file=Path(file_path).name,
                    source_layer=dim.get("layer"),
                    source_coordinates=dim.get("points"),
                    parser_used="DxfDimensionParser",
                    extraction_method="dimension",
                    extracted_at=datetime.utcnow().isoformat()
                )
                result.entities.append(TechnicalEntity(
                    type=EntityType.DIMENSION,
                    measure=MeasureType.DESIGN,
                    discipline=Discipline.ARCHITECTURAL,
                    provenance=provenance,
                    coordinates=dim.get("points"),
                    properties={
                        "value": dim.get("value"),
                        "dim_type": dim.get("type_name"),
                        "layer": dim.get("layer")
                    },
                    confidence=ExtractionConfidence.DXF_DIMENSION.value
                ))

            result.source_metadata = {
                "layers": dxf_data.get("layers", []),
                "units": dxf_data.get("units"),
                "version": dxf_data.get("version"),
                "dimension_count": dxf_data.get("dimension_count", 0)
            }

        except Exception as e:
            logger.error(f"DXF parsing error: {e}")
            result.warnings.append(f"Parse error: {e}")

        return result
    
    async def _parse_cad(self, file_path: str, content: str = None) -> ExtractionResult:
        """Extract from CAD files (DWG/DXF)."""
        from app.services.parsers.cad_parser import CADParser
        from app.schemas.technical_entity import Provenance
        from datetime import datetime

        result = ExtractionResult(
            measure=MeasureType.DESIGN,
            discipline=Discipline.ARCHITECTURAL
        )

        try:
            parser = CADParser()
            cad_data = parser.parse(file_path)

            for area in cad_data.get("areas", []):
                provenance = Provenance(
                    source_file=Path(file_path).name,
                    source_layer=area.get("nombre"),
                    parser_used="CADParser",
                    extraction_method="geometry",
                    extracted_at=datetime.utcnow().isoformat()
                )
                result.entities.append(TechnicalEntity(
                    type=EntityType.AREA,
                    measure=MeasureType.DESIGN,
                    discipline=Discipline.ARCHITECTURAL,
                    provenance=provenance,
                    properties={
                        "area_m2": area.get("area_m2"),
                        "type": area.get("type"),
                        "layer": area.get("nombre")
                    },
                    confidence=ExtractionConfidence.DXF_GEOMETRY.value
                ))

            result.source_metadata = {
                "layers": cad_data.get("layers", []),
                "units": cad_data.get("units"),
                "geometry": cad_data.get("entities", {})
            }

        except Exception as e:
            logger.error(f"CAD parsing error: {e}")
            result.warnings.append(f"Parse error: {e}")

        return result
    
    async def _parse_pdf(self, file_path: str, content: str = None) -> ExtractionResult:
        """Extract from PDF files."""
        from app.services.parsers.pdf_parser import PDFParser
        
        result = ExtractionResult(
            measure=MeasureType.GENERAL,
            discipline=Discipline.DESIGN
        )
        
        try:
            parser = PDFParser()
            pdf_data = parser.parse(file_path)
            
            result.source_metadata = {
                "pages": pdf_data.get("text_summary", {}).get("total_pages", 0),
                "chars": pdf_data.get("text_summary", {}).get("total_chars", 0),
                "content_text": pdf_data.get("content_text", "")[:500]
            }
            result.confidence = ExtractionConfidence.PDF_VECTOR_TEXT.value
            
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            result.warnings.append(f"Parse error: {e}")
        
        return result
    
    async def _parse_excel(self, file_path: str, content: str = None) -> ExtractionResult:
        """Extract from Excel files."""
        from app.services.parsers.excel_parser import ExcelParser
        
        result = ExtractionResult(
            measure=MeasureType.GENERAL,
            discipline=Discipline.DESIGN,
            confidence=ExtractionConfidence.EXCEL_CELL_EXACT.value
        )
        
        try:
            parser = ExcelParser()
            excel_data = parser.parse(file_path)
            
            result.source_metadata = {
                "sheets": excel_data.get("sheets", []),
                "total_rows": excel_data.get("total_rows", 0)
            }
            
        except Exception as e:
            logger.error(f"Excel parsing error: {e}")
            result.warnings.append(f"Parse error: {e}")
        
        return result
    
    async def _parse_docx(self, file_path: str, content: str = None) -> ExtractionResult:
        """Extract from Word files."""
        from app.services.parsers.docx_parser import DocxParser
        
        result = ExtractionResult(
            measure=MeasureType.GENERAL,
            discipline=Discipline.DESIGN
        )
        
        try:
            parser = DocxParser()
            docx_data = parser.parse(file_path)
            
            result.source_metadata = {
                "paragraphs": docx_data.get("paragraph_count", 0),
                "tables": docx_data.get("table_count", 0)
            }
            result.confidence = 0.85
            
        except Exception as e:
            logger.error(f"DOCX parsing error: {e}")
            result.warnings.append(f"Parse error: {e}")
        
        return result


# Singleton instance
engine = TechnicalExtractionEngine()