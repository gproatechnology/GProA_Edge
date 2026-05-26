"""Spatial Ground Truth Dataset for validation."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GroundTruthSpace(BaseModel):
    """Expected space from ground truth."""
    id: str
    name: str
    expected_area_m2: float
    expected_bounds: Dict[str, float]  # min_x, min_y, max_x, max_y
    expected_type: str = "space"
    expected_adjacencies: List[str] = Field(default_factory=list)


class GroundTruthDataset(BaseModel):
    """Complete ground truth for a floor plan."""
    plan_id: str
    spaces: List[GroundTruthSpace] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_space_by_id(self, space_id: str) -> Optional[GroundTruthSpace]:
        for space in self.spaces:
            if space.id == space_id or space.name == space_id:
                return space
        return None
    
    def get_expected_adjacency_pairs(self) -> List[tuple]:
        """Get all expected adjacency pairs."""
        pairs = []
        for space in self.spaces:
            for adjacent_id in space.expected_adjacencies:
                pair = tuple(sorted([space.id, adjacent_id]))
                if pair not in pairs:
                    pairs.append(pair)
        return pairs


def create_office_ground_truth() -> GroundTruthDataset:
    """Create a sample office floor plan ground truth."""
    return GroundTruthDataset(
        plan_id="office-plan-001",
        spaces=[
            GroundTruthSpace(
                id="SALA-01",
                name="Main Office",
                expected_area_m2=50.0,
                expected_bounds={"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 5},
                expected_type="office",
                expected_adjacencies=["CORRIDOR-01"]
            ),
            GroundTruthSpace(
                id="CORRIDOR-01",
                name="Main Corridor",
                expected_area_m2=20.0,
                expected_bounds={"min_x": 10, "min_y": 0, "max_x": 15, "max_y": 5},
                expected_type="corridor",
                expected_adjacencies=["SALA-01", "WC-01"]
            ),
            GroundTruthSpace(
                id="WC-01",
                name="Restroom",
                expected_area_m2=8.0,
                expected_bounds={"min_x": 15, "min_y": 0, "max_x": 20, "max_y": 4},
                expected_type="service",
                expected_adjacencies=["CORRIDOR-01"]
            ),
        ]
    )


def create_classroom_ground_truth() -> GroundTruthDataset:
    """Create a classroom building ground truth (different typology)."""
    return GroundTruthDataset(
        plan_id="classroom-plan-001",
        metadata={"building_type": "educational", "building_code": "E"},
        spaces=[
            GroundTruthSpace(
                id="CLASS-101",
                name="Classroom 101",
                expected_area_m2=60.0,
                expected_bounds={"min_x": 0, "min_y": 0, "max_x": 8, "max_y": 7.5},
                expected_type="classroom",
                expected_adjacencies=["HALLWAY-A"]
            ),
            GroundTruthSpace(
                id="CLASS-102",
                name="Classroom 102",
                expected_area_m2=60.0,
                expected_bounds={"min_x": 8, "min_y": 0, "max_x": 16, "max_y": 7.5},
                expected_type="classroom",
                expected_adjacencies=["HALLWAY-A"]
            ),
            GroundTruthSpace(
                id="HALLWAY-A",
                name="Main Hallway",
                expected_area_m2=25.0,
                expected_bounds={"min_x": 0, "min_y": 7.5, "max_x": 20, "max_y": 3.5},
                expected_type="corridor",
                expected_adjacencies=["CLASS-101", "CLASS-102", "STAIRS-1"]
            ),
            GroundTruthSpace(
                id="STAIRS-1",
                name="Main Stairs",
                expected_area_m2=15.0,
                expected_bounds={"min_x": 20, "min_y": 7.5, "max_x": 25, "max_y": 5},
                expected_type="stairs",
                expected_adjacencies=["HALLWAY-A"]
            ),
        ]
    )


def create_residential_ground_truth() -> GroundTruthDataset:
    """Create a residential apartment ground truth."""
    return GroundTruthDataset(
        plan_id="apt-plan-001",
        metadata={"building_type": "residential", "apartment_type": "1BR"},
        spaces=[
            GroundTruthSpace(
                id="LIVING",
                name="Living Room",
                expected_area_m2=25.0,
                expected_bounds={"min_x": 0, "min_y": 0, "max_x": 5, "max_y": 5},
                expected_type="living",
                expected_adjacencies=["KITCHEN"]
            ),
            GroundTruthSpace(
                id="KITCHEN",
                name="Kitchen",
                expected_area_m2=12.0,
                expected_bounds={"min_x": 5, "min_y": 0, "max_x": 10, "max_y": 4},
                expected_type="kitchen",
                expected_adjacencies=["LIVING", "BEDROOM"]
            ),
            GroundTruthSpace(
                id="BEDROOM",
                name="Bedroom",
                expected_area_m2=15.0,
                expected_bounds={"min_x": 5, "min_y": 4, "max_x": 10, "max_y": 8},
                expected_type="bedroom",
                expected_adjacencies=["KITCHEN", "BATH"]
            ),
            GroundTruthSpace(
                id="BATH",
                name="Bathroom",
                expected_area_m2=6.0,
                expected_bounds={"min_x": 10, "min_y": 4, "max_x": 13, "max_y": 6},
                expected_type="bathroom",
                expected_adjacencies=["BEDROOM"]
            ),
        ]
    )


# List of diverse ground truth datasets for validation
GROUND_TRUTH_DATASETS = [
    create_office_ground_truth,
    create_classroom_ground_truth,
    create_residential_ground_truth,
]