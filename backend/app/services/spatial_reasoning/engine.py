"""Main Spatial Reasoning Engine orchestrating graph construction."""
import logging
from typing import Dict, Any, List
from app.services.spatial_reasoning.graph import (
    SpatialNode, SpatialEdge, SpatialGraph, 
    SpatialNodeType, SpatialEdgeType
)
from app.services.spatial_reasoning.clustering import GeometryClusterer
from app.services.spatial_reasoning.adjacency_optimized import OptimizedAdjacencyDetector
from app.services.spatial_reasoning.classification import SpaceClassifier

logger = logging.getLogger(__name__)


class SpatialReasoningEngine:
    """
    Transform extracted geometry into structured Spatial Knowledge Graph.
    
    Integration point: Consumes output from parsers, feeds to EDGE Strategy Mapper.
    """

    def __init__(self):
        self.clusterer = GeometryClusterer()
        self.adjacency_detector = OptimizedAdjacencyDetector()
        self.classifier = SpaceClassifier()

    def build_graph(
        self, 
        polygons: List[Dict[str, Any]], 
        metadata: Dict[str, Any] = None
    ) -> SpatialGraph:
        """
        Build complete spatial graph from geometry.
        
        Args:
            polygons: List of polygon dicts from CAD parser
            metadata: Source file metadata
            
        Returns:
            Complete SpatialGraph with nodes and edges
        """
        if not polygons:
            return SpatialGraph()

        # Step 1: Cluster polygons into spatial nodes
        logger.info(f"Clustering {len(polygons)} polygons into spatial nodes")
        nodes = self.clusterer.cluster_from_polygons(polygons)
        
        # Step 2: Detect adjacencies
        logger.info("Detecting spatial adjacencies")
        edges = self.adjacency_detector.detect_adjacencies(nodes)
        
        # Step 3: Classify space types
        logger.info("Classifying space types")
        for node in nodes:
            self.classifier.classify(node)

        # Build graph
        graph = SpatialGraph(
            nodes=nodes,
            edges=edges,
            geometry_metadata={
                "polygon_count": len(polygons),
                "layer": metadata.get("layer") if metadata else None,
                "units": metadata.get("units") if metadata else None,
            }
        )

        logger.info(f"Built spatial graph: {len(nodes)} nodes, {len(edges)} edges")
        return graph

    def build_graph_from_extraction_result(
        self, 
        extraction_result: Any
    ) -> SpatialGraph:
        """
        Build graph from ExtractionResult (full pipeline integration).
        
        Uses geometry_normalizer to convert parser output into spatial polygons.
        This is the key integration point for the Spatial Reasoning Layer.
        
        Args:
            extraction_result: Result from TechnicalExtractionEngine
            
        Returns:
            SpatialGraph derived from extracted entities and areas
        """
        from app.services.spatial_reasoning.geometry_normalizer import normalize_extraction_to_polygons
        
        polygons = normalize_extraction_to_polygons(extraction_result)
        
        if not polygons:
            logger.warning("No polygons extracted from extraction result")
            return SpatialGraph()
        
        logger.info(f"Building graph from {len(polygons)} normalized polygons")
        return self.build_graph(polygons, extraction_result.source_metadata)

    def _extract_bounds(self, coordinates: Dict[str, Any]) -> Dict[str, float]:
        """Extract bounding box from coordinates."""
        points = coordinates.get("points", [])
        if not points:
            return None

        x_vals = [p.get("x", p[0]) if isinstance(p, dict) else p[0] for p in points]
        y_vals = [p.get("y", p[1]) if isinstance(p, dict) else p[1] for p in points]

        return {
            "min_x": min(x_vals),
            "min_y": min(y_vals),
            "max_x": max(x_vals),
            "max_y": max(y_vals),
        }


# Singleton instance
engine = SpatialReasoningEngine()