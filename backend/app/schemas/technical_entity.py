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


class EntityStatus(str, Enum):
    CONFIRMED = "confirmed"     # Direct observation/extraction
    INFERRED = "inferred"       # Derived by logic/AI
    INCOMPLETE = "incomplete"   # Missing critical properties
    CONTRADICTORY = "contradictory" # Conflicts found in reconciliation


class AdjudicationStatus(str, Enum):
    ADJUDICATED = "adjudicated"     # Chosen as final truth
    AMBIGUOUS = "ambiguous"         # Conflicts require manual review
    REJECTED = "rejected"           # Evidence discarded by dominance policy
    PENDING = "pending"             # Awaiting arbitration


class ArbitrationResult(BaseModel):
    """Detailed reasoning behind a truth adjudication decision (TAL v1.0)."""
    decision: AdjudicationStatus
    winning_source: str
    dominant_status: EntityStatus
    rejected_sources: List[str] = Field(default_factory=list)
    logic_applied: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RelationshipType(str, Enum):
    ILLUMINATES = "illuminates"
    FEEDS = "feeds"
    CONNECTED_TO = "connected_to"
    LOCATED_IN = "located_in"
    PART_OF = "part_of"
    CONTROLS = "controls"
    SUPPLIES = "supplies"
    REFERENCES = "references"


class RelationshipStatus(str, Enum):
    FACT = "fact"               # Observed relationship
    INFERENCE = "inference"     # Logical derivation
    HYPOTHETICAL = "hypothetical" # AI suggestion / Low confidence


SCHEMA_VERSION = "1.0"


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
    schema_version: str = Field(default=SCHEMA_VERSION)


class RawDataProposal(BaseModel):
    """Temporary structure for parsers to propose data before official Entity construction."""
    type: EntityType
    properties: Dict[str, Any]
    provenance: Provenance
    coordinates: Optional[Dict[str, Any]] = None
    confidence: float = 0.90
    measure: Optional[MeasureType] = None
    discipline: Optional[Discipline] = None
    semantic_evidence: Optional[Dict[str, Any]] = Field(default=None, description="Semantic classification evidence")


class TechnicalEntity(BaseModel):
    """Universal technical entity - The Engineering Compiler's Single Source of Truth."""
    uid: str = Field(description="Unique identifier (e.g., LUM-ARCH-001)")
    type: EntityType = Field(description="Type of technical entity")
    status: EntityStatus = Field(default=EntityStatus.CONFIRMED, description="UAKG Status")
    adjudication: Optional[ArbitrationResult] = Field(default=None, description="TAL Adjudication Result")
    measure: MeasureType = Field(default=MeasureType.GENERAL, description="EDGE measure classification")
    discipline: Discipline = Field(default=Discipline.DESIGN, description="Engineering discipline")
    provenance: Provenance
    coordinates: Optional[Dict[str, Any]] = Field(default=None, description="Geometry/bbox")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Technical properties")
    confidence: float = Field(ge=0.0, le=1.0, default=0.95, description="Extraction confidence score")
    validation_status: Optional[str] = Field(default=None, description="Current validation state")
    semantic_metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual semantic info")
    schema_version: str = Field(default=SCHEMA_VERSION)
    processing_history: List[Dict[str, Any]] = Field(default_factory=list, description="Audit log of changes")
    relations: List[Dict[str, Any]] = Field(default_factory=list, description="Semantic relationships to other entities")
    
    model_config = {
        "populate_by_name": True,
        "populate_by_alias": True,
        "frozen": False 
    }


class Relationship(BaseModel):
    """UAKG Connection between technical entities with uncertainty awareness."""
    uid: str = Field(alias="id")
    type: RelationshipType
    status: RelationshipStatus = Field(default=RelationshipStatus.FACT)
    source_uid: str = Field(alias="source_entity_id")
    target_uid: str = Field(alias="target_entity_id")
    source_file: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=0.95)
    validation_status: Optional[str] = None
    schema_version: str = Field(default=SCHEMA_VERSION)

    model_config = {
        "populate_by_name": True,
        "populate_by_alias": True
    }



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