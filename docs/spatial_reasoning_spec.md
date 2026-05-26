# Spatial Reasoning Engine Specification
## For EDGE Certification Pipeline

> **Goal**: Transformar geometría extraída (DXF/PDF) en Spatial Knowledge Graph estructurado.

---

## 1. Architecture Layers (Mandatory)

```
┌─────────────────────────────────────────────┐
│  LAYER 3: Semantic & EDGE Layer            │
│  - Space classification                      │
│  - EDGE Strategy Mapping                     │
│  - Semantic entities (TechnicalEntity)       │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  LAYER 2: Spatial Reasoning Layer           │
│  - Spatial Graph construction                │
│  - Adjacency detection                       │
│  - Relationship inference                    │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  LAYER 1: Geometry Layer                    │
│  - Parsers (DXF, PDF, CAD)                   │
│  - Raw geometry extraction                   │
│  - Provenance tracking                       │
└─────────────────────────────────────────────┘
```

---

## 2. Spatial Graph Schema (v1.0)

```python
class SpatialNode(BaseModel):
    """A spatial node in the graph."""
    uid: str                    # Spatial-{type}-{hash}
    node_type: SpatialNodeType  # space, corridor, zone, service_area
    geometry_ref: str           # Ref to source entity UID
    centroid: Tuple[float, float]
    bounds: SpatialBounds
    area_m2: float
    confidence: float = 0.95
    source_layer: Optional[str]
    schema_version: str = "1.0"

class SpatialEdge(BaseModel):
    """A relationship between spatial nodes."""
    source_uid: str
    target_uid: str
    edge_type: SpatialEdgeType  # CONNECTED_TO, ADJACENT_TO, CONTAINS, INTERSECTS
    confidence: float
    evidence: Dict[str, Any]     # geometric proof of relationship
    schema_version: str = "1.0"

class SpatialGraph(BaseModel):
    """Complete spatial graph for a drawing."""
    nodes: List[SpatialNode]
    edges: List[SpatialEdge]
    geometry_metadata: Dict[str, Any]
    schema_version: str = "1.0"
```

---

## 3. Acceptance Criteria

### AC-1: Geometry Clustering
- **Input**: List of polygons/hatches from DXF parser
- **Output**: Clustered into "spaces" based on layer proximity
- **Criteria**: Each cluster has centroid, bounds, area

### AC-2: Adjacency Detection
- **Input**: Spatial nodes with bounds
- **Output**: Edges where nodes share boundaries (distance < threshold + intersection)
- **Criteria**: Shared boundary > 10% of smaller polygon perimeter

### AC-3: Space Classification
- **Input**: SpatialNode with area, shape, adjacency
- **Output**: Node classified as office/corridor/restroom/mechanical
- **Rules**:
  - Area 10-100m2 + rectangular → office
  - Area 1-5m2 + elongated → corridor
  - Layer name contains "WC"→ restroom
  - Area > 50m2 + irregular → mechanical

---

## 4. Non-Functional Requirements

- **Determinism**: Same input → same graph ALWAYS
- **Traceability**: Each edge has geometric evidence
- **Backward Compatibility**: Works with existing EntityBuilder
- **Performance**: < 5s for 1000 polygons

---

## 5. Integration Points

```
CADParser.extract() → GeometryLayer
GeometryLayer → SpatialReasoningEngine.build_graph()
SpatialGraph → SpaceClassifier.classify()
Classified nodes → EDGEStrategyMapper.map_to_measure()
```

---

## 6. File Structure

```
app/services/spatial_reasoning/
├── __init__.py
├── graph.py              # SpatialGraph models
├── adjacency.py          # Adjacency detection logic
├── clustering.py         # Geometry clustering
├── classification.py     # Space type classification
└── engine.py             # Main SpatialReasoningEngine
```