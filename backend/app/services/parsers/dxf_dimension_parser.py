import ezdxf
import logging
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from app.services.parsers.base_parser import BaseParser
from app.schemas.technical_entity import (
    ExtractionResult, TechnicalEntity, Provenance, MeasureType,
    Discipline, EntityType
)
from app.services.confidence_pipeline import ExtractionConfidence

logger = logging.getLogger(__name__)


class DxfDimensionParser(BaseParser):
    """Parser especializado en extracción de dimensiones de archivos DXF."""

    DIMENSION_TYPE_NAMES = {
        0: "Aligned",
        1: "Rotated",
        2: "Radial",
        3: "Diametric",
        4: "Angular",
        5: "ArcLength"
    }

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()

            layers = self._get_layers(doc)
            dimensions = self._extract_dimensions(msp)

            return {
                "format": "DXF",
                "version": doc.dxfversion,
                "units": self._get_unit_name(doc),
                "layers": layers,
                "dimensions": dimensions,
                "dimension_count": len(dimensions)
            }
        except Exception as e:
            logger.error(f"Error parsing DXF dimensions from {file_path}: {e}")
            return {"error": str(e)}

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        try:
            doc = ezdxf.readfile(file_path)
            return {
                "version": doc.dxfversion,
                "units": self._get_unit_name(doc),
                "layer_count": len(doc.layers)
            }
        except Exception:
            return {}

    def _get_layers(self, doc) -> List[str]:
        return [layer.dxf.name for layer in doc.layers]

    def _get_unit_name(self, doc) -> str:
        units_map = {
            0: "Undefined", 1: "Inches", 2: "Feet", 3: "Miles",
            4: "Millimeters", 5: "Centimeters", 6: "Meters"
        }
        insunits = doc.header.get('$INSUNITS', 0)
        return units_map.get(insunits, "Unknown")

    def _extract_dimensions(self, msp) -> List[Dict[str, Any]]:
        dimensions = []
        for dim in msp.query('DIMENSION'):
            dim_data = self._parse_dimension(dim)
            if dim_data:
                dimensions.append(dim_data)
        return dimensions

    def _parse_dimension(self, dim) -> Optional[Dict[str, Any]]:
        try:
            dim_type = dim.dxf.dimtype if hasattr(dim.dxf, 'dimtype') else 0
            dim_value = dim.get_measurement()

            points = self._get_dimension_points(dim)

            return {
                "handle": dim.dxf.handle if hasattr(dim.dxf, 'handle') else None,
                "layer": dim.dxf.layer,
                "type": dim_type,
                "type_name": self.DIMENSION_TYPE_NAMES.get(dim_type, "Unknown"),
                "value": round(dim_value, 4),
                "points": points
            }
        except Exception as e:
            logger.warning(f"Error parsing dimension: {e}")
            return None

    def _get_dimension_points(self, dim) -> Dict[str, List[float]]:
        points = {"origin": None, "defpoint1": None, "defpoint2": None}

        try:
            if hasattr(dim.dxf, 'origin'):
                points["origin"] = [round(dim.dxf.origin.x, 4), round(dim.dxf.origin.y, 4)]
            if hasattr(dim.dxf, 'defpoint1'):
                points["defpoint1"] = [round(dim.dxf.defpoint1.x, 4), round(dim.dxf.defpoint1.y, 4)]
            if hasattr(dim.dxf, 'defpoint2'):
                points["defpoint2"] = [round(dim.dxf.defpoint2.x, 4), round(dim.dxf.defpoint2.y, 4)]
        except Exception:
            pass

        return points

    def get_dimensions_by_layer(self, file_path: str, layer_name: str) -> List[Dict[str, Any]]:
        result = self.parse(file_path)
        if "error" in result:
            return []
        return [d for d in result.get("dimensions", []) if d.get("layer") == layer_name]

    def extract(self, file_path: str) -> ExtractionResult:
        """Extract dimensions as standardized ExtractionResult."""
        result = self.parse(file_path)
        if "error" in result:
            return ExtractionResult(
                measure=MeasureType.DESIGN,
                discipline=Discipline.ARCHITECTURAL,
                warnings=[result["error"]]
            )

        entities = []
        file_hash = self._compute_file_hash(file_path)
        source_file = Path(file_path).name

        for dim in result.get("dimensions", []):
            provenance = Provenance(
                source_file=source_file,
                source_layer=dim.get("layer"),
                source_coordinates=dim.get("points"),
                parser_used=self.__class__.__name__,
                extraction_method="dimension",
                extracted_at=datetime.utcnow().isoformat(),
                file_hash=file_hash
            )

            entities.append(TechnicalEntity(
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

        return ExtractionResult(
            measure=MeasureType.DESIGN,
            discipline=Discipline.ARCHITECTURAL,
            entities=entities,
            confidence=ExtractionConfidence.DXF_DIMENSION.value,
            source_metadata={
                "layers": result.get("layers", []),
                "units": result.get("units"),
                "version": result.get("version"),
                "dimension_count": result.get("dimension_count", 0)
            }
        )

    def _compute_file_hash(self, file_path: str) -> str:
        h = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    h.update(chunk)
            return h.hexdigest()[:16]
        except Exception:
            return ""