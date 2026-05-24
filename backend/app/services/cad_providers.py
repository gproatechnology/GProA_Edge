"""
CAD Abstraction Layer for multiple CAD providers.
Supports DXF, ZWCAD, AutoCAD, and future CAD formats.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from app.schemas.technical_entity import ExtractionResult, MeasureType, Discipline

logger = logging.getLogger(__name__)


@dataclass
class CADLayer:
    """CAD layer information."""
    name: str
    color: Optional[int] = None
    linetype: Optional[str] = None
    visible: bool = True


@dataclass
class CADEntity:
    """Normalized CAD entity from any provider."""
    entity_id: str
    entity_type: str
    layer: str
    coordinates: Dict[str, Any]
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class CADProvider(ABC):
    """Abstract base for CAD providers."""
    
    @abstractmethod
    async def extract_entities(self, file_path: str) -> List[CADEntity]:
        """Extract all entities from CAD file."""
        pass
    
    @abstractmethod
    def get_layers(self, file_path: str) -> List[CADLayer]:
        """Get all layers in file."""
        pass
    
    @abstractmethod
    def get_dimensions(self, file_path: str) -> List[CADEntity]:
        """Extract dimension entities."""
        pass
    
    def to_extraction_result(self, entities: List[CADEntity], layers: List[CADLayer]) -> ExtractionResult:
        """Convert CAD entities to standardized ExtractionResult."""
        from app.schemas.technical_entity import TechnicalEntity, Provenance
        from datetime import datetime
        
        result = ExtractionResult(
            measure=MeasureType.DESIGN,
            discipline=Discipline.ARCHITECTURAL
        )
        
        for entity in entities:
            provenance = Provenance(
                source_file=file_path.split("/")[-1],
                source_layer=entity.layer,
                source_coordinates=entity.coordinates,
                parser_used=self.__class__.__name__,
                extraction_method=entity.entity_type,
                extracted_at=datetime.utcnow().isoformat()
            )
            
            tech_entity = TechnicalEntity(
                id=entity.entity_id,
                type=entity.entity_type,
                measure=MeasureType.DESIGN,
                discipline=Discipline.ARCHITECTURAL,
                provenance=provenance,
                coordinates=entity.coordinates,
                properties=entity.properties
            )
            result.entities.append(tech_entity)
        
        result.source_metadata = {
            "layers": [l.name for l in layers],
            "entity_count": len(entities)
        }
        
        return result


class DXFProvider(CADProvider):
    """DXF file provider using ezdxf."""
    
    async def extract_entities(self, file_path: str) -> List[CADEntity]:
        import ezdxf
        from pathlib import Path
        
        doc = ezdxf.readfile(file_path)
        entities = []
        
        for layer in doc.layers:
            for e in doc.modelspace().query(f'*[layer=="{layer.dxf.name}"]'):
                entity = self._convert_entity(e, layer.dxf.name)
                if entity:
                    entities.append(entity)
        
        return entities
    
    def _convert_entity(self, e, layer_name: str) -> Optional[CADEntity]:
        entity_type = e.dxftype().lower()
        
        if entity_type == "dimension":
            return CADEntity(
                entity_id=str(hash(e.dxf.handle)),
                entity_type="dimension",
                layer=layer_name,
                coordinates={"insert": list(e.dxf.insert) if e.dxf.insert else []},
                properties={"text": e.dxf.text if hasattr(e.dxf, 'text') else ""}
            )
        elif entity_type in ["line", "lwpolyline", "polyline"]:
            if hasattr(e, 'dxf') and hasattr(e.dxf, 'pts'):
                pts = [(p[0], p[1]) for p in e.dxf.pts]
            elif hasattr(e, 'vertices'):
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            else:
                pts = []
            
            return CADEntity(
                entity_id=str(hash(e.dxf.handle)),
                entity_type=entity_type,
                layer=layer_name,
                coordinates={"points": pts},
                properties={"closed": e.closed if hasattr(e, 'closed') else False}
            )
        
        return None
    
    def get_layers(self, file_path: str) -> List[CADLayer]:
        import ezdxf
        
        doc = ezdxf.readfile(file_path)
        return [CADLayer(name=l.dxf.name, color=l.dxf.color) for l in doc.layers]
    
    def get_dimensions(self, file_path: str) -> List[CADEntity]:
        import ezdxf
        
        doc = ezdxf.readfile(file_path)
        dimensions = []
        
        for e in doc.modelspace().query('DIMENSION'):
            dimensions.append(self._convert_entity(e, e.get_layer()))
        
        return [d for d in dimensions if d]


class ZWCADProvider(CADProvider):
    """ZWCAD local worker provider (Windows only)."""
    
    def __init__(self, zwcad_path: str = None):
        self.zwcad_path = zwcad_path or r"C:\Program Files\ZWCAD\ZWCAD.exe"
        self._ensure_available()
    
    def _ensure_available(self):
        import os
        if not os.path.exists(self.zwcad_path):
            logger.warning(f"ZWCAD not found at {self.zwcad_path}")
    
    async def extract_entities(self, file_path: str) -> List[CADEntity]:
        """Extract via ZWCAD COM API (requires local ZWCAD installation)."""
        # Placeholder - would require pywin32 on Windows
        logger.warning("ZWCAD provider requires Windows + ZWCAD installation")
        return []
    
    def get_layers(self, file_path: str) -> List[CADLayer]:
        return []
    
    def get_dimensions(self, file_path: str) -> List[CADEntity]:
        return []


# Provider registry
PROVIDERS = {
    ".dxf": DXFProvider,
    ".dwg": DXFProvider,  # ezdxf can read dwg too
    ".zwc": ZWCADProvider,
}


def get_provider(file_path: str) -> CADProvider:
    """Get appropriate provider for file type."""
    from pathlib import Path
    ext = Path(file_path).suffix.lower()
    
    if ext in PROVIDERS:
        return PROVIDERS[ext]()
    
    return DXFProvider()  # Default