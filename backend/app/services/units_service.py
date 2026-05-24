"""
Unit conversion service for technical engineering values.
Ensures all measurements are normalized for validation.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class UnitType(str, Enum):
    POWER = "power"
    ENERGY = "energy"
    FLOW = "flow"
    AREA = "area"
    EFFICACY = "efficacy"
    LENGTH = "length"
    TEMPERATURE = "temperature"
    PERCENT = "percent"


class UnitSystem(str, Enum):
    SI = "si"
    IP = "ip"


CONVERSION_FACTORS = {
    UnitType.POWER: {
        "W": 1.0, "kW": 1000.0, "MW": 1e6,
        "BTU/h": 0.293071, "TR": 3516.85, "HP": 745.7
    },
    UnitType.ENERGY: {
        "J": 1.0, "kJ": 1000.0, "MJ": 1e6, "GJ": 1e9,
        "kWh": 3.6e6, "BTU": 1055.056
    },
    UnitType.FLOW: {
        "m³/s": 1.0, "L/s": 0.001, "L/min": 1.6667e-5,
        "CFM": 0.0004719, "m³/h": 0.0002778
    },
    UnitType.AREA: {
        "m²": 1.0, "ft²": 0.092903, "cm²": 0.0001
    },
    UnitType.EFFICACY: {
        "lm/W": 1.0, "lm/kW": 0.001
    },
    UnitType.LENGTH: {
        "m": 1.0, "mm": 0.001, "cm": 0.01, "km": 1000.0,
        "ft": 0.3048, "in": 0.0254
    },
    UnitType.TEMPERATURE: {
        "C": 1.0, "F": 1.0, "K": 1.0, "R": 1.0
    },
}


class UnitConversion(BaseModel):
    value: float
    unit: str
    system: UnitSystem = UnitSystem.SI
    normalized_value: Optional[float] = None


class UnitsService:
    """Normalize and convert engineering units."""
    
    @classmethod
    def normalize(cls, value: float, unit: str, unit_type: UnitType) -> float:
        """Convert value to SI base unit."""
        factors = CONVERSION_FACTORS.get(unit_type, {})
        if unit in factors:
            return value * factors[unit]
        return value
    
    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str, 
                unit_type: UnitType) -> float:
        """Convert between compatible units."""
        factors = CONVERSION_FACTORS.get(unit_type, {})
        if from_unit not in factors or to_unit not in factors:
            return value
        
        si_base = value * factors[from_unit]
        return si_base / factors[to_unit]
    
    @classmethod
    def get_power_kw(cls, value: Any, unit: str) -> float:
        """Ensure power is in kW."""
        if isinstance(value, dict):
            value = value.get("value", value.get("watts", 0))
            unit = value.get("unit", "W")
        return cls.normalize(float(value), unit, UnitType.POWER) / 1000.0
    
    @classmethod
    def get_flow_lps(cls, value: Any, unit: str) -> float:
        """Ensure flow is in L/s."""
        return cls.normalize(float(value), unit, UnitType.FLOW) / 0.001
    
    @classmethod
    def get_area_m2(cls, value: Any, unit: str) -> float:
        """Ensure area is in m²."""
        return cls.normalize(float(value), unit, UnitType.AREA)
    
    @classmethod
    def get_temperature_c(cls, value: Any, unit: str) -> float:
        """Ensure temperature is in Celsius."""
        temp = float(value)
        if unit == "F":
            return (temp - 32) * 5 / 9
        elif unit == "K":
            return temp - 273.15
        return temp


units = UnitsService()