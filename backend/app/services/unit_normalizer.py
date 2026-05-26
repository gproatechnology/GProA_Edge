"""
Unit Normalization Layer for EOSIS Edge v1.0.
Normalizes diverse measurement formats to canonical units.
"""
import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum


class UnitType(str, Enum):
    """Canonical unit types for EDGE certification."""
    AREA = "area"
    POWER = "power"
    FLOW = "flow"
    EFFICIENCY = "efficiency"
    LENGTH = "length"
    DIMENSIONLESS = "dimensionless"


class UnitNormalizer:
    """
    Normalizes technical units to canonical forms.
    
    Examples:
        "15,24 m2" → (15.24, "m2")
        "15.24 m²" → (15.24, "m2")
        "120 W" → (120.0, "W")
        "1200 lm" → (1200.0, "lm")
    """
    
    AREA_PATTERNS = [
        (r'm²', 'm2'),
        (r'sq\.?m', 'm2'),
        (r'sq\s*m', 'm2'),
        (r'ft²', 'ft2'),
        (r'sq\.?ft', 'ft2'),
    ]
    
    POWER_PATTERNS = [
        (r'kw', 'kW'),
        (r'w', 'W'),
        (r'watts?', 'W'),
        (r'kv', 'kV'),
    ]
    
    FLOW_PATTERNS = [
        (r'gpm', 'gpm'),
        (r'lhs', 'l/s'),
        (r'lpmin', 'l/min'),
        (r'l/min', 'l/min'),
        (r'm3/h', 'm3/h'),
        (r'm3h', 'm3/h'),
    ]
    
    EFFICIENCY_PATTERNS = [
        (r'lm/w', 'lm/W'),
        (r'lumens?/watt', 'lm/W'),
    ]
    
    def normalize_value(self, value_str: str) -> Tuple[float, str]:
        """
        Normalize a value+unit string to (numeric_value, canonical_unit).
        
        Args:
            value_str: String like "15,24 m2", "120 W", "25 ft²"
            
        Returns:
            Tuple of (float_value, canonical_unit_string)
        """
        if not value_str:
            return (0.0, UnitType.DIMENSIONLESS)
        
        value_str = value_str.strip()
        
        # Handle decimal comma
        value_str = value_str.replace(',', '.')
        
        # Extract numeric value and unit
        match = re.match(r'([\d.]+)\s*([^\d.].*)?', value_str, re.IGNORECASE)
        if not match:
            return (0.0, UnitType.DIMENSIONLESS)
        
        try:
            value = float(match.group(1))
        except ValueError:
            return (0.0, UnitType.DIMENSIONLESS)
        
        unit = match.group(2) or ""
        unit = unit.strip().lower()
        
        # Normalize unit
        canonical_unit = self._normalize_unit(unit)
        
        return (value, canonical_unit)
    
    def _normalize_unit(self, unit: str) -> str:
        """Convert unit to canonical form."""
        original = unit
        
        # Area normalization
        for pattern, canonical in self.AREA_PATTERNS:
            if re.search(pattern, unit, re.IGNORECASE):
                return canonical
        
        # Power normalization
        for pattern, canonical in self.POWER_PATTERNS:
            if re.search(pattern, unit, re.IGNORECASE):
                return canonical
        
        # Flow normalization
        for pattern, canonical in self.FLOW_PATTERNS:
            if re.search(pattern, unit, re.IGNORECASE):
                return canonical
        
        # Efficiency normalization
        for pattern, canonical in self.EFFICIENCY_PATTERNS:
            if re.search(pattern, unit, re.IGNORECASE):
                return canonical
        
        return original if original else UnitType.DIMENSIONLESS
    
    def normalize_entity_value(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize value fields in an entity.
        
        Args:
            entity: Dict with properties like area_m2, value, watts, etc.
            
        Returns:
            Entity with normalized numeric values and canonical units
        """
        result = entity.copy()
        props = result.get("properties", {}).copy()
        
        # Area normalization
        if "area_m2" in props:
            val, unit = self.normalize_value(str(props["area_m2"]))
            props["area_m2"] = val
            if unit != "m2" and "ft2" in unit:
                props["area_m2"] = val * 0.092903  # ft² to m²
                props["unit_original"] = unit
        
        # Power normalization
        if "watts" in props or "value" in props:
            power_fields = ["watts", "value"]
            for field in power_fields:
                if field in props:
                    val, unit = self.normalize_value(str(props[field]))
                    if unit == "kW":
                        val *= 1000
                    props[field] = val
                    if "unit_original" not in props:
                        props["unit_original"] = unit
        
        result["properties"] = props
        return result


normalizer = UnitNormalizer()