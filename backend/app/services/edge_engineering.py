"""
Deterministic engineering service for EDGE calculations.
Implements Point 11 of GPT: Decouples business logic from AI extraction.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EdgeEngineeringService:
    """
    Handles all deterministic calculations for EDGE measures.
    Zero AI dependency.
    """
    
    @staticmethod
    def calculate_lighting_efficiency(luminarias: List[Dict[str, Any]]) -> Dict[str, Any]:
        """EEM22: Calculate global efficacy (Lm/W)."""
        total_lumens_weighted = 0
        total_watts_weighted = 0
        total_qty = 0

        for lum in luminarias:
            qty = lum.get("cantidad", 1) or 1
            lumens = lum.get("lumens", 0.0) or 0.0
            watts = lum.get("watts", 0.0) or 0.0
            
            total_lumens_weighted += lumens * qty
            total_watts_weighted += watts * qty
            total_qty += qty
            
            if watts > 0:
                lum["eficiencia"] = round(lumens / watts, 2)
            else:
                lum["eficiencia"] = 0.0

        eficacia_global = round(total_lumens_weighted / total_watts_weighted, 2) if total_watts_weighted > 0 else 0

        return {
            "eficacia_global": eficacia_global,
            "total_lumens": total_lumens_weighted,
            "total_watts": total_watts_weighted,
            "total_luminarias": total_qty,
            "cumple_edge": eficacia_global >= 90.0,
            "luminarias_procesadas": luminarias
        }

    @staticmethod
    def calculate_water_savings(fixtures: List[Dict[str, Any]], baselines: Dict[str, float]) -> Dict[str, Any]:
        """WEM01/02: Calculate water savings against baselines."""
        total_flow = 0
        total_qty = 0
        savings_detail = []

        for item in fixtures:
            qty = item.get("cantidad", 1) or 1
            flow = item.get("flujo_lpm", 0.0) or 0.0
            tipo = item.get("tipo", "").lower()
            
            # Determine baseline from provided map
            baseline = 6.0 # Default
            if "ducha" in tipo or "shower" in tipo: baseline = baselines.get("Showers", 10.0)
            elif "inodoro" in tipo or "toilet" in tipo or "sanitario" in tipo: baseline = baselines.get("Toilets", 6.0)
            elif "urinario" in tipo or "urinal" in tipo: baseline = baselines.get("Urinals", 1.0)
            elif "cocina" in tipo or "kitchen" in tipo: baseline = baselines.get("KitchenFaucets", 6.0)
            else: baseline = baselines.get("Faucets", 6.0)

            saving = ((baseline - flow) / baseline) * 100 if baseline > 0 else 0
            
            item["baseline"] = baseline
            item["saving_percent"] = round(saving, 1)
            
            total_flow += flow * qty
            total_qty += qty
            savings_detail.append(saving)

        flujo_promedio = round(total_flow / total_qty, 2) if total_qty > 0 else 0
        ahorro_global = round(sum(savings_detail) / len(savings_detail), 1) if savings_detail else 0
        
        return {
            "flujo_promedio": flujo_promedio,
            "ahorro_global_estimado": ahorro_global,
            "cumple_edge": ahorro_global >= 20.0,
            "aparatos_procesados": fixtures
        }

# Singleton
engineering = EdgeEngineeringService()
