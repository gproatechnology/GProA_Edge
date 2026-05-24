"""
Confidence pipeline for technical extraction sources.
Provides traceability and auditability for all extracted data.
"""
from enum import Enum
from typing import Dict, Tuple


class ExtractionConfidence(Enum):
    """Confidence levels based on extraction method."""
    # DXF/DWG - Highest confidence
    DXF_LAYER_EXACT = 0.99  # Exact layer match in DXF
    DXF_DIMENSION = 0.98  # Dimension entity
    DXF_GEOMETRY = 0.95  # Closed polyline/hatch area
    
    # Vector PDF - High confidence  
    PDF_VECTOR_TABLE = 0.95  # Vector table extraction
    PDF_VECTOR_TEXT = 0.90  # Vector text with units
    PDF_VECTOR_DIMENSION = 0.92  # Dimension line
    
    # Excel - High confidence
    EXCEL_CELL_EXACT = 0.99  # Direct cell value
    EXCEL_FORMULA = 0.95  # Calculated value
    
    # CAD symbol - High confidence
    CAD_BLOCK_COUNT = 0.95  # Block instance count
    
    # Image/OCR - Lower confidence
    OCR_HIGH_CONF = 0.80  # Clear text OCR
    OCR_MEDIUM_CONF = 0.60  # Hard to read OCR
    IMAGE_VISION = 0.70  # Vision API extraction
    IMAGE_INFERENCE = 0.45  # LLM inference from image
    
    # Fallback
    UNKNOWN = 0.30


CONFIDENCE_LABELS: Dict[float, str] = {
    0.99: "Deterministic (CAD/PDF Vector/Excel)",
    0.95: "High (Vector/Text with Units)",
    0.90: "Medium-High (Text with Context)",
    0.80: "Medium (Clear OCR)",
    0.70: "Low-Medium (Image/Vision)",
    0.60: "Low (OCR Difficult)",
    0.45: "Fallback (LLM Inference)",
    0.30: "Unknown/Unreliable"
}


def get_confidence_label(confidence: float) -> str:
    """Get human-readable label for confidence score."""
    for threshold, label in sorted(CONFIDENCE_LABELS.items(), reverse=True):
        if confidence >= threshold:
            return label
    return CONFIDENCE_LABELS[0.30]


def calculate_weighted_confidence(*values: Tuple[float, float]) -> float:
    """
    Calculate weighted confidence from multiple sources.
    Higher confidence sources contribute more to final score.
    
    Args:
        *values: Tuples of (value, confidence)
    """
    if not values:
        return 0.0
    
    # Weight inversely to confidence variance
    total_conf = sum(c for _, c in values)
    if total_conf == 0:
        return 0.0
    
    # Weighted average
    weighted_sum = sum(v * c for v, c in values)
    return weighted_sum / total_conf