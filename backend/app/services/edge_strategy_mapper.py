"""
EDGE Strategy Mapper - Determinístico mapeo de entidades a estrategias EDGE.
Mapea entidades técnicas a códigos EEM/WEM/MEM basados en señales semánticas.
"""
import re
from typing import Dict, Any, Optional, List
from enum import Enum


class EDGEEnergyMeasure(str, Enum):
    """EDGE Energy Efficiency Measures."""
    EEM01 = "EEM01"  # Building envelope - windows, insulation
    EEM09 = "EEM09"  # Efficient HVAC systems
    EEM16 = "EEM16"  # Efficient lighting
    EEM22 = "EEM22"  # On-site renewable energy
    EEM23 = "EEM23"  # Energy monitoring


class EDGEWaterMeasure(str, Enum):
    """EDGE Water Efficiency Measures."""
    WEM01 = "WEM01"  # Efficient fixtures and fittings
    WEM02 = "WEM02"  # Efficient irrigation systems


class EDGEMaterialsMeasure(str, Enum):
    """EDGE Materials Efficiency Measures."""
    MEM01 = "MEM01"  # Recycled content


class EDGEStraategyMapper:
    """
    Map entity properties to EDGE strategy codes.
    Now integrated with Spatial Reasoning for context-aware mapping.
    """
    
    # Signal patterns mapping to strategies
    STRATEGY_SIGNALS = {
        EDGEEnergyMeasure.EEM01: [
            "window", "glazing", "shgc", "u-value", "insulation", "wall",
            "roof", "floor", "envelope"
        ],
        EDGEEnergyMeasure.EEM22: [
            "led", "lumen", "watt", "lighting", "luminaire", "efficient light"
        ],
        # ... rest unchanged
        EDGEEnergyMeasure.EEM09: [
            "hvac", "heat pump", "chiller", "vrf", "inverter"
        ],
        EDGEEnergyMeasure.EEM16: [
            "lamp", "tube", "downlight", "spotlight"
        ],
        EDGEWaterMeasure.WEM01: [
            "flow rate", "faucet", "toilet", "flush", "gpm", "lpmin",
            "water fixture", "shower"
        ],
        EDGEWaterMeasure.WEM02: [
            "irrigation", "sprinkler", "drip", "landscape"
        ],
        EDGEMaterialsMeasure.MEM01: [
            "recycled", "recycled content", "scrap", "waste"
        ],
    }
    
    @classmethod
    def map_entity(cls, entity: Dict[str, Any]) -> Optional[str]:
        """
        Map a single entity to an EDGE strategy.
        
        Args:
            entity: Dict with properties, type, and properties fields
            
        Returns:
            EDGE strategy code string or None if no match
        """
        props = entity.get("properties", {})
        entity_type = entity.get("type", "")
        
        # Combine all text fields to check for signals
        text_to_check = " ".join([
            str(props.get("nombre", "")),
            str(props.get("name", "")),
            str(props.get("layer", "")),
            str(props.get("description", "")),
            entity_type,
        ]).lower()
        
        # Check each strategy's signals
        for strategy, signals in cls.STRATEGY_SIGNALS.items():
            for signal in signals:
                if signal.lower() in text_to_check:
                    return strategy.value
        
        return None
    
    @classmethod
    def map_multiple(cls, entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Map multiple entities to strategies.
        
        Returns:
            Dict mapping strategy codes to lists of matching entities
        """
        result = {}
        
        for entity in entities:
            strategy = cls.map_entity(entity)
            if strategy:
                if strategy not in result:
                    result[strategy] = []
                result[strategy].append(entity)
        
        return result
    
    @classmethod
    def get_strategy_confidence(cls, entity: Dict[str, Any], 
                                 strategy: str) -> float:
        """
        Calculate confidence for a strategy mapping.
        
        Higher confidence when multiple signals match.
        """
        props = entity.get("properties", {})
        text_to_check = " ".join([
            str(props.get("nombre", "")),
            str(props.get("name", "")),
            str(props.get("layer", "")),
            str(props.get("description", "")),
        ]).lower()
        
        signals = cls.STRATEGY_SIGNALS.get(strategy, [])
        matches = sum(1 for s in signals if s.lower() in text_to_check)
        
        if matches == 0:
            return 0.5
        elif matches == 1:
            return 0.85
        else:
            return 0.95

    @classmethod
    def map_spatial_graph(cls, graph) -> Dict[str, Any]:
        """
        Map spatial graph to EDGE strategies based on node types and adjacency.
        
        Rules:
        - corridor + adjacent room -> EEM16 (lighting)
        - large area -> EEM01 (building envelope)
        - small area count -> WEM01 (efficient fixtures)
        - many adjacencies -> EEM23 (monitoring)
        """
        result = {
            "strategies": [],
            "spaces_for_edesign": [],
            "confidence_map": {}
        }
        
        space_count = 0
        total_adjacencies = len(graph.edges)
        large_spaces = 0
        corridors = 0
        
        for node in graph.nodes:
            if node.node_type.value == "space":
                space_count += 1
                is_corridor = node.area_m2 < 10 and node.area_m2 > 0  # Narrow/shallow = corridor
                
                result["spaces_for_edesign"].append({
                    "uid": node.uid,
                    "area_m2": node.area_m2,
                    "type": "corridor" if is_corridor else node.node_type.value,
                    "area_category": "large" if node.area_m2 > 50 else "small"
                })
                
                # Corridor -> lighting
                if is_corridor:
                    corridors += 1
                    result["strategies"].append("EEM16")
                    result["confidence_map"]["EEM16"] = result["confidence_map"].get("EEM16", 0) + 0.85
                    
                # Large spaces -> envelope
                if node.area_m2 > 50:
                    large_spaces += 1
                    result["strategies"].append("EEM01")
                    result["confidence_map"]["EEM01"] = result["confidence_map"].get("EEM01", 0) + 0.90
                    
        # Multiple small spaces -> efficient fixtures
        if space_count > 5:
            result["strategies"].append("WEM01")
            result["confidence_map"]["WEM01"] = 0.80
            
        # Complex adjacency graph -> monitoring
        if total_adjacencies > space_count * 0.5:
            result["strategies"].append("EEM23")
            result["confidence_map"]["EEM23"] = 0.75
            
        result["strategies"] = list(set(result["strategies"]))
        result["summary"] = {
            "space_count": space_count,
            "corridors": corridors,
            "large_spaces": large_spaces,
            "total_adjacencies": total_adjacencies
        }
        return result


# Singleton instance
strategy_mapper = EDGEStraategyMapper()