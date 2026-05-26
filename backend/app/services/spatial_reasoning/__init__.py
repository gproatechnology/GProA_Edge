"""Spatial Reasoning Engine for EOSIS Edge."""
from .graph import (
    SpatialNode, SpatialEdge, SpatialGraph, 
    SpatialBounds, SpatialNodeType, SpatialEdgeType
)
from .engine import SpatialReasoningEngine
from .clustering import GeometryClusterer
from .adjacency import AdjacencyDetector
from .classification import SpaceClassifier
from .geometry_normalizer import GeometryNormalizer, normalize_extraction_to_polygons
from .quality_evaluator import SpatialGraphQualityEvaluator
from .error_classifier import ErrorClassifier, ErrorType
from .feedback_loop import SpatialGraphFeedbackLoop
from .ground_truth import GroundTruthDataset, GroundTruthSpace, create_office_ground_truth, create_classroom_ground_truth, create_residential_ground_truth, GROUND_TRUTH_DATASETS
from .graph_comparator import SpatialGraphComparator, comparator
from .node_alignment import NodeMatcher, NodeAlignmentEvaluator, node_matcher, alignment_evaluator
from .scale_extensions import FloorProcessor, LegacyPlanCleaner, IndustrialBuildingAdapter

__all__ = [
    "SpatialNode",
    "SpatialEdge", 
    "SpatialGraph",
    "SpatialBounds",
    "SpatialNodeType",
    "SpatialEdgeType",
    "SpatialReasoningEngine",
    "GeometryClusterer",
    "AdjacencyDetector",
    "SpaceClassifier",
    "GeometryNormalizer",
    "normalize_extraction_to_polygons",
    "SpatialGraphQualityEvaluator",
    "ErrorClassifier",
    "ErrorType",
    "SpatialGraphFeedbackLoop",
    "GroundTruthDataset",
    "GroundTruthSpace",
    "create_office_ground_truth",
    "create_classroom_ground_truth",
    "create_residential_ground_truth",
    "GROUND_TRUTH_DATASETS",
    "SpatialGraphComparator",
    "comparator",
    "NodeMatcher",
    "NodeAlignmentEvaluator",
    "node_matcher",
    "alignment_evaluator",
    "FloorProcessor",
    "LegacyPlanCleaner",
    "IndustrialBuildingAdapter",
]