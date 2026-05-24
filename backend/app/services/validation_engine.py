"""
Validation Engine for EDGE Certification.
Deterministic validation rules with no LLM dependency.
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from app.schemas.technical_entity import (
    TechnicalEntity, ExtractionResult, MeasureType, EntityType
)
from app.services.edge_rules import get_rule

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    rule_name: str
    measure: str
    passed: bool
    value: Any
    threshold: Any
    message: str
    critical: bool = False


class ValidationEngine:
    """Deterministic EDGE validation engine."""
    
    EDGE_THRESHOLDS = {
        "EEM22": {
            "min_efficacy_lm_per_w": 90.0,
            "description": "Iluminación eficiente - mínimo 90 lm/W"
        },
        "EEM09": {
            "min_cop": 3.0,
            "min_seer": 12.0,
            "description": "HVAC eficiente - mínimo COP 3.0 y SEER 12.0"
        },
        "EEM16": {
            "min_renewable_percentage": 10.0,
            "description": "Energía renovable - mínimo 10% de demanda"
        },
        "WEM01": {
            "min_water_saving_percent": 20.0,
            "description": "Grifería eficiente - mínimo 20% ahorro"
        },
        "WEM02": {
            "max_flush_liters": 4.8,
            "description": "Sanitarios eficientes - máximo 4.8 L/descarga"
        },
        "EEM01": {
            "max_window_to_wall_ratio": 0.40,
            "description": "Envolvente - máximo 40% WWR"
        }
    }
    
    def __init__(self):
        self.results: List[ValidationResult] = []
    
    def validate_eem22_efficacy(self, total_lumens: float, total_watts: float) -> ValidationResult:
        """Validate EEM22 lighting efficacy >= 90 lm/W."""
        if total_watts <= 0:
            return ValidationResult(
                rule_name="EEM22_EFFICACY",
                measure="EEM22",
                passed=False,
                value=0,
                threshold=90.0,
                message="No wattage data available for efficacy calculation",
                critical=True
            )
        
        efficacy = total_lumens / total_watts
        passed = efficacy >= 90.0
        
        return ValidationResult(
            rule_name="EEM22_EFFICACY",
            measure="EEM22",
            passed=passed,
            value=round(efficacy, 2),
            threshold=90.0,
            message=f"Eficacia luminosa: {efficacy:.2f} lm/W {'CUMPLE' if passed else 'NO CUMPLE'}",
            critical=True
        )
    
    def validate_eem09_hvac(self, cop: float, seer: float) -> ValidationResult:
        """Validate EEM09 HVAC efficiency."""
        cop_pass = cop >= 3.0
        seer_pass = seer >= 12.0
        passed = cop_pass and seer_pass
        
        return ValidationResult(
            rule_name="EEM09_HVAC",
            measure="EEM09",
            passed=passed,
            value={"cop": cop, "seer": seer},
            threshold={"cop": 3.0, "seer": 12.0},
            message=f"COP: {cop} ({'OK' if cop_pass else 'FAIL'}), SEER: {seer} ({'OK' if seer_pass else 'FAIL'})",
            critical=True
        )
    
    def validate_water_savings(self, saving_percent: float) -> ValidationResult:
        """Validate WEM water savings >= 20%."""
        passed = saving_percent >= 20.0
        
        return ValidationResult(
            rule_name="WEM_WATER_SAVINGS",
            measure="WEM01",
            passed=passed,
            value=round(saving_percent, 1),
            threshold=20.0,
            message=f"Ahorro agua: {saving_percent:.1f}% {'CUMPLE' if passed else 'NO CUMPLE'}",
            critical=True
        )
    
    def validate_panel_load_consistency(self, calculated_kw: float, panel_kw: float) -> ValidationResult:
        """Validate panel load vs calculated lighting load consistency."""
        if panel_kw <= 0:
            return ValidationResult(
                rule_name="PANEL_LOAD_CHECK",
                measure="EEM22",
                passed=False,
                value=calculated_kw,
                threshold=0,
                message="No panel data available",
                critical=False
            )
        
        # Allow 15% tolerance for diversity factor
        ratio = calculated_kw / panel_kw if panel_kw > 0 else 0
        passed = 0.7 <= ratio <= 1.3
        
        return ValidationResult(
            rule_name="PANEL_LOAD_CHECK",
            measure="EEM22",
            passed=passed,
            value=round(calculated_kw, 1),
            threshold=f"±30% of {panel_kw} kW",
            message=f"Carga calculada: {calculated_kw} kW vs panel: {panel_kw} kW (ratio: {ratio:.2f})",
            critical=False
        )
    
    def validate_extraction(self, extraction: ExtractionResult) -> List[ValidationResult]:
        """Run all applicable validations on an extraction result."""
        results = []
        measure = extraction.measure.value
        
        # EEM22 lighting validation
        if measure == "EEM22" or extraction.measure == MeasureType.DESIGN:
            total_lumens = extraction.calculations.get("total_lumens", 0)
            total_watts = extraction.calculations.get("total_watts", 0)
            if total_lumens and total_watts:
                results.append(self.validate_eem22_efficacy(total_lumens, total_watts))
        
        # Panel load validation
        panel_kw = extraction.calculations.get("total_panel_kw", 0)
        calc_kw = extraction.calculations.get("calculated_kw", 0)
        if panel_kw and calc_kw:
            results.append(self.validate_panel_load_consistency(calc_kw, panel_kw))
        
        self.results.extend(results)
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        critical_passed = sum(1 for r in self.results if r.critical and r.passed)
        critical_total = sum(1 for r in self.results if r.critical)
        
        return {
            "total_validations": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "critical_passed": critical_passed,
            "critical_total": critical_total,
            "edge_compliant": critical_passed == critical_total and critical_total > 0
        }
    
    def validate_entities(self, entities: List[Dict[str, Any]]) -> List[Any]:
        """Validate a list of entity dictionaries."""
        issues = []
        for e in entities:
            if e.get("type") == "luminaire":
                watts = e.get("properties", {}).get("watts", 0)
                lumens = e.get("properties", {}).get("lumens", 0)
                if watts > 0 and lumens > 0:
                    result = self.validate_eem22_efficacy(lumens, watts)
                    issues.append(result)
        return issues

    def clear(self):
        """Clear validation results."""
        self.results = []


# Singleton instance
validator = ValidationEngine()