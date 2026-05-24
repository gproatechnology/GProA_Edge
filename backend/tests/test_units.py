"""
Tests for units service.
"""
import pytest
from app.services.units_service import UnitsService, UnitType


def test_power_normalization():
    assert abs(UnitsService.get_power_kw(1000, "W") - 1.0) < 0.001
    assert abs(UnitsService.get_power_kw(1, "kW") - 1.0) < 0.001
    assert abs(UnitsService.get_power_kw(3412, "BTU/h") - 1.0) < 0.01


def test_flow_normalization():
    assert abs(UnitsService.get_flow_lps(1, "m³/s") - 1000.0) < 0.1
    assert abs(UnitsService.get_flow_lps(60, "L/min") - 1.0) < 0.01
    assert abs(UnitsService.get_flow_lps(35.3, "CFM") - 16.67) < 0.1


def test_area_normalization():
    assert abs(UnitsService.get_area_m2(10.76, "ft²") - 1.0) < 0.01


def test_temperature_conversion():
    assert abs(UnitsService.get_temperature_c(32, "F") - 0.0) < 0.01
    assert abs(UnitsService.get_temperature_c(273.15, "K") - 0.0) < 0.01
    assert abs(UnitsService.get_temperature_c(100, "C") - 100.0) < 0.01


def test_general_normalize():
    assert UnitsService.normalize(1, "W", UnitType.POWER) == 1.0
    assert UnitsService.normalize(1, "kW", UnitType.POWER) == 1000.0