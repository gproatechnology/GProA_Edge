"""Multi-floor spatial reasoning for building analysis."""
from typing import Dict, Any, List, Optional
from app.services.spatial_reasoning import SpatialGraph, SpatialNode, SpatialEdge
from app.services.spatial_reasoning.graph import SpatialBounds


class FloorProcessor:
    """
    Process multi-floor buildings with floor-aware graph construction.
    """
    
    def __init__(self):
        self.floor_separator = 2.0  # Minimum vertical separation between floors (m)
    
    def assign_floors(self, graph: SpatialGraph) -> Dict[str, int]:
        """
        Assign floor numbers to nodes based on Y-coordinates.
        
        Returns dict mapping node uid -> floor number
        """
        if not graph.nodes:
            return {}
        
        nodes_with_y = [(n, n.bounds.min_y) for n in graph.nodes]
        nodes_with_y.sort(key=lambda x: x[1], reverse=True)  # Top floor first
        
        floors = {}
        current_floor = 1
        last_y = None
        threshold = 5.0  # Minimum Y difference for new floor
        
        for node, y in nodes_with_y:
            if last_y is None or abs(y - last_y) > threshold:
                current_floor += 1
            last_y = y
            floors[node.uid] = current_floor
        
        return floors
    
    def get_floor_graphs(self, graph: SpatialGraph) -> Dict[int, SpatialGraph]:
        """Split graph by floors, preserving inter-floor edges."""
        floors = self.assign_floors(graph)
        
        floor_graphs = {}
        for node in graph.nodes:
            floor_num = floors.get(node.uid, 1)
            if floor_num not in floor_graphs:
                floor_graphs[floor_num] = SpatialGraph(nodes=[], edges=[])
            floor_graphs[floor_num].nodes.append(node)
        
        for edge in graph.edges:
            source_floor = floors.get(edge.source_uid, 1)
            target_floor = floors.get(edge.target_uid, 1)
            if source_floor == target_floor and source_floor in floor_graphs:
                floor_graphs[source_floor].edges.append(edge)
        
        return floor_graphs


class LegacyPlanCleaner:
    """
    Clean and normalize legacy scanned plans with common issues.
    """
    
    def clean_graph(self, graph: SpatialGraph) -> SpatialGraph:
        """Apply cleaning operations to legacy graphs."""
        cleaned_nodes = []
        
        for node in graph.nodes:
            if self._is_valid_node(node):
                cleaned_nodes.append(self._cleanup_node(node))
        
        valid_uids = {n.uid for n in cleaned_nodes}
        cleaned_edges = [
            e for e in graph.edges 
            if e.source_uid in valid_uids and e.target_uid in valid_uids
        ]
        
        return SpatialGraph(nodes=cleaned_nodes, edges=cleaned_edges)
    
    def _is_valid_node(self, node: SpatialNode) -> bool:
        """Filter out invalid nodes from scanned plans."""
        area = node.area_m2
        if area < 0.5:  # Too small
            return False
        if area > 10000:  # Unrealistically large
            return False
        
        bounds = node.bounds
        width = bounds.max_x - bounds.min_x
        height = bounds.max_y - bounds.min_y
        
        if width <= 0 or height <= 0:
            return False
        if width > 500 or height > 500:  # Likely scan artifact
            return False
        
        return True
    
    def _cleanup_node(self, node: SpatialNode) -> SpatialNode:
        """Apply minor cleanup to node properties."""
        node.area_m2 = round(node.area_m2, 2)
        return node


class IndustrialBuildingAdapter:
    """
    Adapt spatial reasoning for non-EDGE building types.
    
    Building types:
    - Hospital: Large floor plates, complex adjacencies
    - Factory: High ceilings, large open spaces
    - Retail: Irregular layouts, tenant separations
    """
    
    TYPE_ADJUSTMENTS = {
        "hospital": {"height_threshold": 4.0, "min_room_area": 8},
        "factory": {"height_threshold": 8.0, "min_room_area": 20},
        "retail": {"height_threshold": 3.5, "min_room_area": 5},
        "warehouse": {"height_threshold": 10.0, "min_room_area": 50},
    }
    
    def adjust_for_type(
        self, 
        graph: SpatialGraph, 
        building_type: str = "office"
    ) -> SpatialGraph:
        """Adjust adjacency detection for building type."""
        adjustments = self.TYPE_ADJUSTMENTS.get(building_type, self.TYPE_ADJUSTMENTS["hospital"])
        
        filtered_nodes = [
            n for n in graph.nodes 
            if n.area_m2 >= adjustments["min_room_area"]
        ]
        
        valid_uids = {n.uid for n in filtered_nodes}
        filtered_edges = [
            e for e in graph.edges 
            if e.source_uid in valid_uids and e.target_uid in valid_uids
        ]
        
        return SpatialGraph(nodes=filtered_nodes, edges=filtered_edges)


floor_processor = FloorProcessor()
legacy_cleaner = LegacyPlanCleaner()
industrial_adapter = IndustrialBuildingAdapter()