"""
Tests for SpatialSemanticClassifier and SemanticEvidence.
"""
import pytest
from app.services.semantic_evidence import (
    SemanticEvidence, SpatialSemanticClassifier, SemanticType
)


def test_cad_dimension_classification():
    """Test that CAD patterns like '15.24' are classified as DIMENSION."""
    classifier = SpatialSemanticClassifier()
    
    # Isolated numeric with CAD spacing context
    evidence = classifier.classify('15.24', None, {'neighbor_text': '12.19 15.24 12.19'})
    
    assert evidence.candidate_type == SemanticType.DIMENSION
    assert evidence.confidence >= 0.95
    assert 'cad_spacing_pattern' in evidence.reasons
    assert 'no_area_context' in evidence.reasons


def test_area_value_with_context():
    """Test area values with 'm2' context are not classified as dimensions."""
    classifier = SpatialSemanticClassifier()
    
    evidence = classifier.classify('25.0', 25.0, {'neighbor_text': 'Electrical Room 25.0 m2'})
    
    # Should NOT be DIMENSION because it has area context
    assert evidence.candidate_type != SemanticType.DIMENSION or evidence.confidence < 0.7


def test_global_area_threshold():
    """Test values > 10000 are classified as GLOBAL_AREA."""
    classifier = SpatialSemanticClassifier()
    
    # Use a token with text that won't trigger numeric bleedthrough
    # and has value > 10000
    evidence = classifier.classify('AREA-TOTAL', 11523.0, {})
    
    # Value > 10000 should be classified as GLOBAL_AREA
    assert evidence.candidate_type == SemanticType.GLOBAL_AREA
    assert 'value_exceeds_threshold' in evidence.reasons


def test_room_label_classification():
    """Test room labels are classified as ARCH_SPACE."""
    classifier = SpatialSemanticClassifier()
    
    evidence = classifier.classify('Electrical Room', None, {})
    
    assert evidence.candidate_type == SemanticType.ARCH_SPACE
    assert 'contains_space_keyword' in evidence.reasons


def test_semantic_evidence_to_dict():
    """Test SemanticEvidence serialization."""
    evidence = SemanticEvidence(
        token='test',
        candidate_type=SemanticType.DIMENSION,
        confidence=0.97,
        reasons=['test_reason'],
        context={'bbox': [0, 0, 100, 100]}
    )
    
    d = evidence.to_dict()
    
    assert d['token'] == 'test'
    assert d['candidate_type'] == 'dimension'
    assert d['confidence'] == 0.97
    assert d['reasons'] == ['test_reason']
    assert d['context']['bbox'] == [0, 0, 100, 100]


def test_empty_token():
    """Test empty token handling."""
    classifier = SpatialSemanticClassifier()
    
    evidence = classifier.classify('', None, {})
    
    assert evidence.candidate_type == SemanticType.UNKNOWN
    assert evidence.confidence == 0.0
    assert 'empty_token' in evidence.reasons