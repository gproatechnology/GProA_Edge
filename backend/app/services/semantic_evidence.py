"""
Semantic Evidence Model for EOSIS Edge.
Provides evidential classification without destroying data early.
Based on GPT: "NO destruir evidencia tempranamente; solo degradar confianza"
"""
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class SemanticType(str, Enum):
    DIMENSION = "dimension"
    GLOBAL_AREA = "global_area"
    ARCH_SPACE = "arch_space"
    AREA_SUMMARY = "area_summary"
    UNKNOWN = "unknown"


@dataclass
class SemanticEvidence:
    """
    Evidential classification of a token's semantic meaning.
    This is the FIRST epistemological layer of the system.
    """
    token: str
    candidate_type: SemanticType
    confidence: float = 0.95
    reasons: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "spatial_pattern"
    
    def __post_init__(self):
        if not self.reasons:
            self.reasons = self._infer_reasons()
    
    def _infer_reasons(self) -> List[str]:
        reasons = []
        if self._is_isolated_numeric():
            reasons.append("isolated_numeric")
        if self._matches_cad_pattern():
            reasons.append("cad_spacing_pattern")
        if self._has_area_context():
            reasons.append("area_unit_nearby")
        if self._has_room_label_nearby():
            reasons.append("room_label_nearby")
        return reasons
    
    def _is_isolated_numeric(self) -> bool:
        return bool(re.match(r'^\d+(\.\d+)?$', self.token))
    
    def _matches_cad_pattern(self) -> bool:
        return bool(re.match(r'^\d{1,3}\.\d{2}$', self.token))
    
    def _has_area_context(self) -> bool:
        text = self.context.get("neighbor_text", "")
        return bool(re.search(r'\b(m2|m²|sqm|MT2)\b', text, re.IGNORECASE))
    
    def _has_room_label_nearby(self) -> bool:
        text = self.context.get("neighbor_text", "")
        keywords = ["room", "area", "production", "office", "restroom"]
        return any(kw in text.lower() for kw in keywords)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "candidate_type": self.candidate_type.value,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "context": self.context,
            "source": self.source
        }


class SpatialSemanticClassifier:
    """
    Clasifica el significado semántico de tokens extraídos de planos.
    NO decide verdad - SOLO etiqueta evidencia para TAL/UAKG.
    """
    
    DIMENSION_PATTERN = re.compile(r'^\d{1,3}\.\d{2}$')
    SPACE_KEYWORDS = {
        "ROOM", "AREA", "PRODUCTION", "OFFICE", "RESTROOM", "STORAGE",
        "MECHANICAL", "ELECTRICAL", "CORRIDOR", "LOBBY", "KITCHEN",
        "BATHROOM", "BEDROOM", "LIVING", "GARAGE", "PATIO",
        "EXTERNAL", "CARPARKING", "LIGHTING", "OPTIMIZING", "PUMPS", "HOUSE"
    }
    
    def classify(self, token: str, value: Optional[float] = None,
                 context: Optional[Dict[str, Any]] = None) -> SemanticEvidence:
        """
        Clasifica un token y retorna evidencia semántica.
        
        Args:
            token: Texto extraído (ej: "15.24", "Electrical Room", "AREA")
            value: Valor numérico asociado (si aplica)
            context: Contexto espacial (bbox, vecinos, texto cercano)
        
        Returns:
            SemanticEvidence con tipo candidato, confianza y razones
        """
        if not token:
            return SemanticEvidence(
                token=token or "",
                candidate_type=SemanticType.UNKNOWN,
                confidence=0.0,
                reasons=["empty_token"],
                context=context or {}
            )
        
        context = context or {}
        neighbor_text = context.get("neighbor_text", "")
        token_upper = token.upper()
        
        # SPRINT: Enhanced heuristics for false positive reduction
        
        # 0. Reject truncated labels (PRIORITY 1)
        if len(token.strip()) <= 2 and token.strip().isalpha():
            return SemanticEvidence(
                token=token,
                candidate_type=SemanticType.UNKNOWN,
                confidence=0.1,
                reasons=["truncated_label_rejected", "ocr_fragment"],
                context=context,
                source="quality_filter"
            )
        
        # 0b. Reject numeric names (numeric bleedthrough)
        token_clean = token.replace(".", "").replace("-", "").replace(",", "")
        if token_clean.isdigit() and value is not None:
            return SemanticEvidence(
                token=token,
                candidate_type=SemanticType.UNKNOWN,
                confidence=0.1,
                reasons=["numeric_bleedthrough_rejected"],
                context=context,
                source="quality_filter"
            )
        
        # 1. Detect dimensiones CAD con contexto mejorado
        if self.DIMENSION_PATTERN.match(token):
            has_spacing_pattern = self._check_spacing_context(token, neighbor_text)
            has_m2_context = "m2" in neighbor_text.lower() or "m²" in neighbor_text.lower()
            
            # SPRINT: Only classify as dimension if truly isolated (no area context)
            if has_spacing_pattern and not has_m2_context:
                # Check for neighboring tokens that indicate this might be a name
                neighboring = context.get("neighboring_tokens", [])
                has_space_keyword = any(kw in str(neighboring).upper() for kw in self.SPACE_KEYWORDS)
                
                if not has_space_keyword:
                    return SemanticEvidence(
                        token=token,
                        candidate_type=SemanticType.DIMENSION,
                        confidence=0.97,
                        reasons=["isolated_numeric", "cad_spacing_pattern", "no_area_context", "no_space_nearby"],
                        context=context,
                        source="spatial_pattern"
                    )
        
        # 2. Detect área global (> 10,000 m² probablemente es total del edificio)
        if value is not None and value > 10000:
            return SemanticEvidence(
                token=token,
                candidate_type=SemanticType.GLOBAL_AREA,
                confidence=0.95,
                reasons=["value_exceeds_threshold", "building_total_candidate"],
                context=context,
                source="numeric_threshold"
            )
        
        # 3. Detect labels arquitectónicos
        for keyword in self.SPACE_KEYWORDS:
            if keyword in token_upper:
                return SemanticEvidence(
                    token=token,
                    candidate_type=SemanticType.ARCH_SPACE,
                    confidence=0.90,
                    reasons=["contains_space_keyword", f"keyword={keyword.lower()}"],
                    context=context,
                    source="keyword_match"
                )
        
        # 4. Detect summary labels
        if any(word in token_upper for word in ["TOTAL", "SUM", "SUMMARY"]):
            return SemanticEvidence(
                token=token,
                candidate_type=SemanticType.AREA_SUMMARY,
                confidence=0.85,
                reasons=["summary_keyword_detected"],
                context=context,
                source="summary_pattern"
            )
        
        # Default: unknown with basic reasoning
        return SemanticEvidence(
            token=token,
            candidate_type=SemanticType.UNKNOWN,
            confidence=0.50,
            reasons=["no_classification_match"],
            context=context,
            source="default"
        )
    
    def _check_spacing_context(self, token: str, neighbor_text: str) -> bool:
        """Check if token appears in CAD dimension spacing context."""
        val = float(token)
        # Common CAD spacing patterns
        spacing_values = [3.05, 6.10, 9.14, 12.19, 15.24, 18.29, 21.34, 24.38, 27.43]
        return any(abs(val - s) < 0.01 for s in spacing_values)


# Singleton instance
classifier = SpatialSemanticClassifier()