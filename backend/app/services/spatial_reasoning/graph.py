"""Spatial Graph models for geometry-to-knowledge transformation."""
import uuid
from enum import Enum
from typing import Tuple, Dict, Any, Optional
from pydantic import BaseModel, Field


class SpatialNodeType(str, Enum):
    """Types of spatial nodes."""
    SPACE = "space"
    CORRIDOR = "corridor"
    ZONE = "zone"
    SERVICE_AREA = "service_area"


class SpatialEdgeType(str, Enum):
    """Types of spatial relationships."""
    CONNECTED_TO = "connected_to"
    ADJACENT_TO = "adjacent_to"
    CONTAINS = "contains"
    INTERSECTS = "intersects"


class SpatialBounds(BaseModel):
    """Bounding box for spatial operations."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    centroid_x: Optional[float] = None
    centroid_y: Optional[float] = None

    def __post_init__(self):
        if self.centroid_x is None:
            self.centroid_x = (self.min_x + self.max_x) / 2
        if self.centroid_y is None:
            self.centroid_y = (self.min_y + self.max_y) / 2

    def model_post_init(self, __context):
        """Pydantic v2 hook for post-init."""
        if self.centroid_x is None:
            self.centroid_x = (self.min_x + self.max_x) / 2
        if self.centroid_y is None:
            self.centroid_y = (self.min_y + self.max_y) / 2

    def contains_point(self, x: float, y: float) -> bool:
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def boundary_distance(self, other: "SpatialBounds") -> float:
        """Minimum distance between boundaries."""
        dx = max(0, max(self.min_x - other.max_x, other.min_x - self.max_x))
        dy = max(0, max(self.min_y - other.max_y, other.min_y - self.max_y))
        return (dx**2 + dy**2) ** 0.5

    def shared_boundary_length(self, other: "SpatialBounds") -> float:
        """Calculate shared boundary length (1D overlap)."""
        x_overlap = max(0, min(self.max_x, other.max_x) - max(self.min_x, other.min_x))
        y_overlap = max(0, min(self.max_y, other.max_y) - max(self.min_y, other.min_y))
        
        if x_overlap > 0 and y_overlap == 0:
            return x_overlap
        if y_overlap > 0 and x_overlap == 0:
            return y_overlap
        return 0.0


class SpatialNode(BaseModel):
    """A spatial node in the graph representing a space/area."""
    uid: str = Field(default_factory=lambda: f"SPATIAL-{uuid.uuid4().hex[:8]}")
    node_type: SpatialNodeType = SpatialNodeType.SPACE
    geometry_ref: str = ""
    centroid: Tuple[float, float] = (0.0, 0.0)
    bounds: SpatialBounds
    area_m2: float = 0.0
    confidence: float = 0.95
    source_layer: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"


class SpatialEdge(BaseModel):
    """A relationship between two spatial nodes."""
    source_uid: str
    target_uid: str
    edge_type: SpatialEdgeType
    confidence: float = 0.90
    evidence: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"

    def __hash__(self):
        return hash((self.source_uid, self.target_uid, self.edge_type))


class SpatialGraph(BaseModel):
    """Complete spatial graph representing a floor plan."""
    nodes: list = Field(default_factory=list)
    edges: list = Field(default_factory=list)
    geometry_metadata: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"

    def get_node(self, uid: str) -> Optional[SpatialNode]:
        for node in self.nodes:
            if node.uid == uid:
                return node
        return None

    def get_edges_for_node(self, uid: str) -> list:
        return [e for e in self.edges if e.source_uid == uid or e.target_uid == uid]

    def add_node(self, node: SpatialNode) -> None:
        if not self.get_node(node.uid):
            self.nodes.append(node)

    def add_edge(self, edge: SpatialEdge) -> None:
        edge_key = (edge.source_uid, edge.target_uid, edge.edge_type)
        existing = any(
            e.source_uid == edge.source_uid and 
            e.target_uid == edge.target_uid and 
            e.edge_type == edge.edge_type 
            for e in self.edges
        )
        if not existing:
            self.edges.append(edge)