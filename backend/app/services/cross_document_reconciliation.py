"""
Cross-document reconciliation for technical extraction.
Detects and resolves inconsistencies between multiple document sources.
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DiscrepancySeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Discrepancy:
    """Represents an inconsistency between document sources with full auditability."""
    measure: str
    field: str
    sources: Dict[str, Any]  # source_file/type -> value
    severity: DiscrepancySeverity
    description: str
    confidence: float = 0.90
    audit_trail: List[str] = field(default_factory=list)
    
    @property
    def variance_percent(self) -> float:
        """Calculate percentage variance between numerical sources."""
        numeric_values = [v for v in self.sources.values() if isinstance(v, (int, float))]
        if not numeric_values or len(numeric_values) < 2:
            return 0.0
        min_val, max_val = min(numeric_values), max(numeric_values)
        if min_val == 0:
            return 100.0 if max_val > 0 else 0.0
        return ((max_val - min_val) / min_val) * 100


@dataclass
class ReconciliationResult:
    """Result of cross-document reconciliation."""
    discrepancies: List[Discrepancy] = field(default_factory=list)
    reconciled_values: Dict[str, Any] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    @property
    def has_critical_discrepancies(self) -> bool:
        return any(d.severity == DiscrepancySeverity.CRITICAL for d in self.discrepancies)
    
    @property
    def total_variance(self) -> float:
        return sum(d.variance_percent for d in self.discrepancies)


class CrossDocumentReconciler:
    """
    Industrial-grade reconciler for technical engineering data.
    Ensures 'Single Source of Truth' by detecting and resolving 'Entity Drift'.
    """
    
    # Known acceptable tolerances per measure/field
    TOLERANCES = {
        "EEM22": {
            "total_watts": 0.15,  # 15% tolerance for lighting load
            "total_lumens": 0.15,
            "calculated_kw": 0.30,  # 30% for calculated vs panel
        },
        "WEM01": {
            "saving_percent": 0.10,  # 10% for water savings
        },
        "EEM09": {
            "cop": 0.20,  # 20% for COP
        }
    }
    
    def reconcile_entities(self, entities: List[Any]) -> ReconciliationResult:
        """
        Detect discrepancies between entities that represent the same technical reality (Entity Drift).
        """
        result = ReconciliationResult()
        # Group entities by canonical UID (Identity Resolution must run first)
        from collections import defaultdict
        grouped = defaultdict(list)
        for e in entities:
            # uid is our single source of truth from EntityBuilder
            grouped[e.uid].append(e)
            
        for uid, group in grouped.items():
            if len(group) < 2:
                continue
                
            # Compare critical properties across sources
            primary = group[0]
            for other in group[1:]:
                if primary.type != other.type:
                    result.discrepancies.append(Discrepancy(
                        measure=primary.measure,
                        field="type",
                        sources={
                            primary.provenance.source_file: primary.type,
                            other.provenance.source_file: other.type
                        },
                        severity=DiscrepancySeverity.CRITICAL,
                        description=f"Type mismatch for entity {uid}: {primary.type} vs {other.type}",
                        audit_trail=[f"Source 1: {primary.provenance.parser_used}", f"Source 2: {other.provenance.parser_used}"]
                    ))
        
        return result

    def reconcile_lighting_loads(
        self,
        lighting_calc_kw: float,
        panel_kw: float,
        exterior_kw: float = None,
        source_files: Dict[str, str] = None
    ) -> ReconciliationResult:
        """
        Regulatory-grade reconciliation for lighting loads.
        Explains gaps using industrial diversity factors.
        """
        result = ReconciliationResult()
        sources = source_files or {}
        
        # Diversity Factor Analysis (Point 8 Audit)
        if panel_kw > 0:
            ratio = lighting_calc_kw / panel_kw
            variance = abs(1.0 - ratio)
            
            # 15% - 30% is expected diversity in Industrial projects
            if 0.70 <= ratio <= 0.85:
                result.reconciled_values["diversity_factor_status"] = "Consistent (Industrial Diversity)"
                result.reconciled_values["inferred_diversity_factor"] = round(ratio, 2)
            elif variance > self.TOLERANCES["EEM22"]["calculated_kw"]:
                severity = DiscrepancySeverity.CRITICAL if variance > 0.50 else DiscrepancySeverity.WARNING
                
                result.discrepancies.append(Discrepancy(
                    measure="EEM22",
                    field="lighting_load",
                    sources={
                        "calculation_sheet": lighting_calc_kw,
                        "panel_schedule": panel_kw,
                        **({"exterior_lighting": exterior_kw} if exterior_kw else {})
                    },
                    severity=severity,
                    description=f"Lighting load gap exceeds tolerance ({variance:.1%}). Possible missing plans or mislabeled panels.",
                    audit_trail=[f"Calculated from {sources.get('calc', 'unknown')}", f"Panel from {sources.get('panel', 'unknown')}"]
                ))
        
        return result
    
    def reconcile_water_savings(
        self,
        calculated_saving: float,
        baseline_saving: float = 20.0
    ) -> ReconciliationResult:
        """Check if calculated water savings meet EDGE baseline."""
        result = ReconciliationResult()
        
        if calculated_saving < baseline_saving:
            result.discrepancies.append(Discrepancy(
                measure="WEM01",
                field="water_saving_percent",
                sources={"calculated": calculated_saving, "baseline": baseline_saving},
                severity=DiscrepancySeverity.WARNING,
                description=f"Water savings {calculated_saving}% below EDGE baseline {baseline_saving}%",
                confidence=0.95
            ))
        
        return result
    
    def reconcile_luminaire_efficacy(
        self,
        calculated_efficacy: float,
        edge_threshold: float = 90.0,
        emergency_excluded: bool = True
    ) -> ReconciliationResult:
        """Validate lighting efficacy against EDGE threshold."""
        result = ReconciliationResult()
        
        if calculated_efficacy < edge_threshold:
            severity = DiscrepancySeverity.CRITICAL
            result.discrepancies.append(Discrepancy(
                measure="EEM22",
                field="efficacy_lm_per_w",
                sources={"calculated": calculated_efficacy, "edge_min": edge_threshold},
                severity=severity,
                description=f"Efficacy {calculated_efficacy:.1f} lm/W below EDGE minimum {edge_threshold} lm/W",
                confidence=0.98
            ))
        else:
            result.reconciled_values["edge_compliant"] = True
        
        return result
    
    def get_diversity_factor_analysis(
        self,
        calculated_load: float,
        connected_load: float
    ) -> Dict[str, Any]:
        """Analyze and explain diversity factor between calculated and connected loads."""
        if connected_load <= 0:
            return {"error": "Connected load must be positive"}
        
        diversity = calculated_load / connected_load
        
        # Typical diversity factors by building type
        typical_ranges = {
            "industrial": (0.80, 0.90),
            "commercial": (0.60, 0.80),
            "residential": (0.40, 0.60),
        }
        
        building_type = "industrial" if diversity > 0.75 else "commercial" if diversity > 0.50 else "residential"
        
        return {
            "diversity_factor": round(diversity, 2),
            "building_type_estimate": building_type,
            "in_range": typical_ranges[building_type][0] <= diversity <= typical_ranges[building_type][1],
            "interpretation": f"Diversity factor {diversity:.2f} is typical for {building_type} buildings"
        }


# Singleton instance
reconciler = CrossDocumentReconciler()
