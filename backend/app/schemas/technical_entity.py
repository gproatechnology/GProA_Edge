"""
Standardized technical entity schema for EDGE certification pipeline.
All parsers must output data in this format for consistency.
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class MeasureType(str, Enum):
    EEM01 = "EEM01"
    EEM09 = "EEM09"
    EEM16 = "EEM16"
    EEM22 = "EEM22"
    EEM23 = "EEM23"
    WEM01 = "WEM01"
    WEM02 = "WEM02"
    MEM01 = "MEM01"
    DESIGN = "DESIGN"
    GENERAL = "GENERAL"


class Discipline(str, Enum):
    ENERGY = "ENERGY"
    WATER = "WATER"
    MATERIALS = "MATERIALS"
    DESIGN = "DESIGN"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    ARCHITECTURAL = "architectural"


class EntityType(str, Enum):
    LUMINAIRE = "luminaire"
    PANEL = "panel"
    AREA = "area"
    HVAC_UNIT = "hvac_unit"
    FIXTURE = "fixture"
    DIMENSION = "dimension"
    POLYLINE = "polyline"
    TEXT_LABEL = "text_label"
    HATCH = "hatch"
    DOOR = "door"
    STAIR = "stair"
    CIRCUIT = "circuit"


class Provenance(BaseModel):
    """Complete provenance tracking for auditability and traceability."""
    source_file: str
    source_page: Optional[int] = None
    source_layer: Optional[str] = None
    source_coordinates: Optional[Dict[str, Any]] = None
    parser_used: str
    extraction_method: str
    extracted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    file_hash: Optional[str] = None


class TechnicalEntity(BaseModel):
    """Universal technical entity from any source file."""
    entity_id: str = Field(default="", description="Semantic ID (LUM-ARCH-001, PAN-ELEC-001)")
    type: str = Field(default="dimension", description="Type of technical entity")
    measure: MeasureType = Field(default=MeasureType.GENERAL, description="EDGE measure classification")
    discipline: Discipline = Field(default=Discipline.DESIGN, description="Engineering discipline")
    provenance: Provenance
    coordinates: Optional[Dict[str, Any]] = Field(default=None, description="Geometry/bbox")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Measured properties")
    confidence: float = Field(ge=0.0, le=1.0, default=0.95, description="Extraction confidence")
    validation_status: Optional[str] = Field(default=None, description="Cross-validation status")
    semantic_metadata: Dict[str, Any] = Field(default_factory=dict, description="Semantic info")
    
    model_config = {"populate_by_name": True}
    
    def __init__(self, **data):
        if not data.get('entity_id') and not data.get('id'):
            from app.services.semantic_id import id_generator
            entity_type = data.get('type', 'dimension')
            data['entity_id'] = id_generator.generate(entity_type, data.get('properties'))
        super().__init__(**data)
    
    model_config = {"populate_by_name": True}


class SpatialBounds(BaseModel):
    """Spatial bounding box for geometry operations."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    centroid_x: Optional[float] = None
    centroid_y: Optional[float] = None

    def contains_point(self, x: float, y: float) -> bool:
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def contains_bounds(self, other: "SpatialBounds") -> bool:
        return (self.min_x <= other.min_x and self.min_y <= other.min_y and
                self.max_x >= other.max_x and self.max_y >= other.max_y)


class ExtractionResult(BaseModel):
    """Standardized output from any parser."""
    measure: MeasureType = Field(default=MeasureType.GENERAL)
    discipline: Discipline = Field(default=Discipline.DESIGN)
    entities: List[TechnicalEntity] = Field(default_factory=list)
    relationships: List[Dict[str, str]] = Field(default_factory=list)
    calculations: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    source_metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationRule(BaseModel):
    """Deterministic EDGE validation rule."""
    measure: MeasureType
    rule_name: str
    calculation: str
    threshold: Any
    operator: str = ">="

    def validate(self, value: Any) -> bool:
        ops = {">=": lambda a, b: a >= b, ">": lambda a, b: a > b,
               "<=": lambda a, b: a <= b, "<": lambda a, b: a < b,
               "==": lambda a, b: a == b}
        return ops.get(self.operator, lambda a, b: True)(value, self.threshold)


class ValidationIssue(BaseModel):
    """Cross-document validation issue."""
    severity: str = "warning"
    issue_type: str
    source_files: List[str]
    values: Dict[str, Any]
    confidence: float = 0.90
    message: str = ""