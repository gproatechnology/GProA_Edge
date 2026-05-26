"""
Spatial Semantic Classifier for EOSIS.
Re-exports SemanticEvidence and SpatialSemanticClassifier from semantic_evidence.py.
"""
from app.services.semantic_evidence import (
    SemanticType,
    SemanticEvidence,
    SpatialSemanticClassifier,
    classifier
)

__all__ = ["SemanticType", "SemanticEvidence", "SpatialSemanticClassifier", "classifier"]