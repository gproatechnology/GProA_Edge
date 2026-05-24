"""
Semantic ID Generator for deterministic entity identification.
Generates persistent, meaningful IDs based on entity properties.
"""
import re
from typing import Dict, Any, Optional


class SemanticIDGenerator:
    """
    Generate semantic IDs for technical entities.
    Format: {TYPE}-{DISCIPLINE}-{SEQUENCE:03d}
    
    Examples:
    - LUM-ARCH-001 (First luminaire)
    - PAN-ELEC-001 (First panel)
    - CIR-ELEC-001 (First circuit)
    - ARE-ARCH-001 (First area)
    - HVAC-HVAC-001 (First HVAC unit)
    """
    
    PREFIX_MAP = {
        "luminaire": "LUM",
        "panel": "PAN",
        "circuit": "CIR",
        "area": "ARE",
        "hvac_unit": "HVAC",
        "fixture": "FIX",
        "water_heater": "WH",
        "pump": "PMP",
    }
    
    DISCIPLINE_MAP = {
        "luminaire": "ARCH",
        "panel": "ELEC",
        "circuit": "ELEC",
        "area": "ARCH",
        "hvac_unit": "HVAC",
        "fixture": "WATR",
        "water_heater": "WATR",
        "pump": "MECH",
    }
    
    def __init__(self):
        self._counters: Dict[str, int] = {}
    
    def generate(self, entity_type: str, properties: Dict[str, Any] = None, 
                 discipline: str = None) -> str:
        """Generate semantic ID for entity."""
        prefix = self.PREFIX_MAP.get(entity_type, entity_type[:3].upper())
        disc = self.DISCIPLINE_MAP.get(entity_type, (discipline or "GEN")[:4].upper())
        
        key = f"{prefix}-{disc}"
        self._counters[key] = self._counters.get(key, 0) + 1
        seq = self._counters[key]
        
        return f"{prefix}-{disc}-{seq:03d}"
    
    def generate_from_name(self, entity_type: str, name: str = None,
                          properties: Dict[str, Any] = None) -> str:
        """Generate semantic ID with optional name context."""
        base_id = self.generate(entity_type, properties)
        
        if name:
            normalized = self._normalize_name(name)
            if normalized:
                return f"{base_id}-{normalized[:4]}"
        
        return base_id
    
    def _normalize_name(self, name: str) -> str:
        """Normalize entity name for ID."""
        name = name.upper()
        name = re.sub(r'[^A-Z0-9]', '', name)
        return name
    
    def parse(self, semantic_id: str) -> Dict[str, Any]:
        """Parse semantic ID into components."""
        parts = semantic_id.split('-')
        
        if len(parts) >= 3:
            return {
                "prefix": parts[0],
                "discipline": parts[1],
                "sequence": int(parts[2]) if parts[2].isdigit() else 0,
                "suffix": parts[3] if len(parts) > 3 else None
            }
        
        return {"raw": semantic_id}
    
    def reset_counters(self):
        """Reset sequence counters (for testing)."""
        self._counters.clear()


id_generator = SemanticIDGenerator()