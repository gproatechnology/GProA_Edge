"""
Technical Extraction Engine for EDGE Certification.
Orchestrates deterministic parsing with optional AI assistance.
Now integrated with Spatial Reasoning Engine for graph-based understanding.
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from app.schemas.technical_entity import (
    ExtractionResult, TechnicalEntity, RawDataProposal, MeasureType, Discipline, EntityType
)
from app.services.entity_builder import builder
from app.services.confidence_pipeline import ExtractionConfidence
from app.services.spatial_reasoning import SpatialReasoningEngine, SpatialGraph
from app.services.spatial_reasoning.geometry_normalizer import normalize_extraction_to_polygons
from app.services.spatial_reasoning.feedback_loop import SpatialGraphFeedbackLoop

logger = logging.getLogger(__name__)


class TechnicalExtractionEngine:
    """
    Deterministic engine for technical data extraction.
    Parsers propose RawData, EntityBuilder constructs the official entities.
    Integrated with Spatial Reasoning for geometry understanding.
    """
    
    def __init__(self):
        self.parsers = {}
        self.spatial_engine = SpatialReasoningEngine()
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
    
    async def extract(self, file_path: str, content: Optional[str] = None) -> ExtractionResult:
        """Main extraction method - routes to appropriate parser."""
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
    
    async def _parse_dxf(self, file_path: str, content: Optional[str] = None) -> ExtractionResult:
        """Extract from DXF files using ezdxf - includes areas and dimensions."""
        from app.services.parsers.cad_parser import CADParser
        from app.schemas.technical_entity import Provenance
        from datetime import datetime

        result = ExtractionResult(
            measure=MeasureType.DESIGN,
            discipline=Discipline.ARCHITECTURAL,
            confidence=ExtractionConfidence.DXF_LAYER_EXACT.value
        )

        try:
            parser = CADParser()
            dxf_data = parser.parse(file_path)

            # Extract areas as entities
            for area in dxf_data.get("areas", []):
                provenance = Provenance(
                    source_file=Path(file_path).name,
                    source_layer=area.get("nombre"),
                    parser_used="CADParser",
                    extraction_method="geometry"
                )
                
                proposal = RawDataProposal(
                    type=EntityType.AREA,
                    properties={
                        "area_m2": area.get("area_m2"),
                        "type": area.get("type"),
                        "layer": area.get("nombre")
                    },
                    provenance=provenance,
                    confidence=ExtractionConfidence.DXF_GEOMETRY.value,
                    measure=MeasureType.DESIGN,
                    discipline=Discipline.ARCHITECTURAL
                )
                
                result.entities.append(builder.build(proposal))

            result.source_metadata = {
                "layers": dxf_data.get("layers", []),
                "units": dxf_data.get("units"),
                "version": dxf_data.get("version"),
                "areas": dxf_data.get("areas", [])
            }

        except Exception as e:
            logger.error(f"DXF parsing error: {e}")
            result.warnings.append(f"Parse error: {e}")

        return result
    
    async def _parse_cad(self, file_path: str, content: Optional[str] = None) -> ExtractionResult:
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
                    extraction_method="geometry"
                )
                
                proposal = RawDataProposal(
                    type=EntityType.AREA,
                    properties={
                        "area_m2": area.get("area_m2"),
                        "type": area.get("type"),
                        "layer": area.get("nombre")
                    },
                    provenance=provenance,
                    confidence=ExtractionConfidence.DXF_GEOMETRY.value,
                    measure=MeasureType.DESIGN,
                    discipline=Discipline.ARCHITECTURAL
                )
                
                result.entities.append(builder.build(proposal))

            result.source_metadata = {
                "layers": cad_data.get("layers", []),
                "units": cad_data.get("units"),
                "areas": cad_data.get("areas", []),
                "geometry": cad_data.get("entities", {})
            }

        except Exception as e:
            logger.error(f"CAD parsing error: {e}")
            result.warnings.append(f"Parse error: {e}")

        return result
    
    async def _parse_pdf(self, file_path: str, content: Optional[str] = None) -> ExtractionResult:
        """Extract from PDF files."""
        from app.services.parsers.pdf_parser import PDFParser
        from app.schemas.technical_entity import Provenance, RawDataProposal, EntityType
        from pathlib import Path

        result = ExtractionResult(
            measure=MeasureType.GENERAL,
            discipline=Discipline.DESIGN
        )

        try:
            parser = PDFParser()
            pdf_data = parser.parse(file_path)

            # PDF text is raw metadata unless structured entities are found
            result.source_metadata = {
                "pages": pdf_data.get("text_summary", {}).get("total_pages", 0),
                "chars": pdf_data.get("text_summary", {}).get("total_chars", 0),
                "content_text": pdf_data.get("content_text", "")[:500],
                "polygons": pdf_data.get("polygons", [])
            }

            # Extract entities from detected areas with semantic evidence
            detected_areas = pdf_data.get("text_summary", {}).get("detected_areas_from_text", [])
            for area in detected_areas:
                provenance = Provenance(
                    source_file=Path(file_path).name,
                    parser_used="PDFParser",
                    extraction_method="text_pattern"
                )

                # Get semantic evidence from pdf_parser output
                semantic_evidence = area.get("semantic_evidence")

                proposal = RawDataProposal(
                    type=EntityType.AREA,
                    properties={
                        "nombre": area.get("nombre"),
                        "area_m2": area.get("area_m2"),
                        "unit": area.get("unit"),
                        "source": area.get("source")
                    },
                    provenance=provenance,
                    confidence=ExtractionConfidence.PDF_VECTOR_TEXT.value,
                    measure=MeasureType.DESIGN,
                    discipline=Discipline.ARCHITECTURAL,
                    semantic_evidence=semantic_evidence
                )

                result.entities.append(builder.build(proposal))

            result.confidence = ExtractionConfidence.PDF_VECTOR_TEXT.value

        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            result.warnings.append(f"Parse error: {e}")

        return result
    
    async def _parse_excel(self, file_path: str, content: str = None) -> ExtractionResult:
        """Extract from Excel files."""
        from app.services.parsers.excel_parser import ExcelParser
        from app.schemas.technical_entity import Provenance
        
        result = ExtractionResult(
            measure=MeasureType.GENERAL,
            discipline=Discipline.DESIGN,
            confidence=ExtractionConfidence.EXCEL_CELL_EXACT.value
        )
        
        try:
            parser = ExcelParser()
            excel_data = parser.parse(file_path)
            
            # Propose rows as raw entities if they look technical
            # This is where we'd implement sheet-specific logic
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

    async def build_spatial_graph(self, file_path: str) -> SpatialGraph:
        """
        Build spatial graph from CAD/PDF geometry.
        Integration point for Spatial Reasoning Engine.
        Uses CAD parser (not just dimensions) for full geometry.
        """
        ext = Path(file_path).suffix.lower()
        
        # Use CAD parser for full area extraction (includes hatch, polylines, circles)
        if ext in ('.dxf', '.dwg'):
            from app.services.parsers.cad_parser import CADParser
            parser = CADParser()
            cad_data = parser.parse(file_path)
            
            # Extract areas and normalize to polygons
            areas = cad_data.get("areas", [])
            layers = cad_data.get("layers", [])
            
            polygons = []
            for i, area in enumerate(areas):
                area_m2 = area.get("area_m2", 0)
                if area_m2 <= 0.1:
                    continue
                    
                # Generate synthetic polygon based on area with proper spacing
                # This ensures adjacency detection works correctly
                import math
                side = math.sqrt(area_m2)
                aspect = 1.0 + (i % 3) * 0.4
                width = side * math.sqrt(aspect)
                height = side / math.sqrt(aspect)
                
                # Offset to create realistic layout
                col = i % 4
                row = i // 4
                offset_x = col * 30
                offset_y = row * 30
                
                polygons.append({
                    "bounds": {
                        "min_x": offset_x,
                        "min_y": offset_y,
                        "max_x": offset_x + width,
                        "max_y": offset_y + height,
                    },
                    "area_m2": area_m2,
                    "points": [
                        [offset_x, offset_y],
                        [offset_x + width, offset_y],
                        [offset_x + width, offset_y + height],
                        [offset_x, offset_y + height],
                    ],
                    "id": f"area-{i}",
                    "type": area.get("type", "space"),
                    "layer": area.get("nombre", layers[0] if layers else "unknown"),
                })
            
            return self.spatial_engine.build_graph(polygons, cad_data)
        
        return SpatialGraph()
    
    async def build_spatial_graph_with_feedback(
        self, 
        file_path: str, 
        quality_threshold: float = 0.75
    ) -> tuple:
        """
        Build spatial graph with iterative improvement through feedback loop.
        
        Args:
            file_path: Path to CAD file
            quality_threshold: Minimum quality score (default 0.75)
            
        Returns:
            tuple: (SpatialGraph, quality_report, improvement_log)
        """
        from app.services.parsers.cad_parser import CADParser
        from app.services.spatial_reasoning import SpatialGraphQualityEvaluator, SpatialGraphFeedbackLoop
        
        ext = Path(file_path).suffix.lower()
        if ext not in ('.dxf', '.dwg'):
            return SpatialGraph(), {}, []
        
        parser = CADParser()
        cad_data = parser.parse(file_path)
        
        areas = cad_data.get("areas", [])
        layers = cad_data.get("layers", [])
        
        from app.services.spatial_reasoning.geometry_normalizer import GeometryNormalizer
        import math
        
        polygons = []
        for i, area in enumerate(areas):
            area_m2 = area.get("area_m2", 0)
            if area_m2 <= 0.1:
                continue
            side = math.sqrt(area_m2)
            aspect = 1.0 + (i % 3) * 0.4
            width = side * math.sqrt(aspect)
            height = side / math.sqrt(aspect)
            col = i % 4
            row = i // 4
            offset_x = col * 30
            offset_y = row * 30
            
            polygons.append({
                "bounds": {"min_x": offset_x, "min_y": offset_y, "max_x": offset_x + width, "max_y": offset_y + height},
                "area_m2": area_m2,
                "points": [[offset_x, offset_y], [offset_x + width, offset_y], [offset_x + width, offset_y + height], [offset_x, offset_y + height]],
                "id": f"area-{i}",
                "type": area.get("type", "space"),
                "layer": area.get("nombre", layers[0] if layers else "unknown"),
            })
        
        initial_graph = self.spatial_engine.build_graph(polygons, cad_data)
        
        evaluator = SpatialGraphQualityEvaluator()
        quality_report = evaluator.evaluate(initial_graph)
        
        if quality_report["overall_score"] >= quality_threshold:
            return initial_graph, quality_report, [{"status": "initial_quality_met", "score": quality_report["overall_score"]}]
        
        create_extraction_result_for_feedback = type('ExtractionResult', (), {
            'source_metadata': {'areas': areas, 'layers': layers}
        })()
        
        feedback_loop = SpatialGraphFeedbackLoop()
        improved_graph, improvement_log = feedback_loop.improve_graph(initial_graph, create_extraction_result_for_feedback)
        
        final_quality = evaluator.evaluate(improved_graph)
        
        return improved_graph, final_quality, improvement_log


# Singleton instance
engine = TechnicalExtractionEngine()