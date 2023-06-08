"""
Tests remarks elements parsing
"""

# stdlib
from typing import List, Optional

# library
import pytest

# module
from avwx import structs
from avwx.parsing import remarks

# tests
from tests.util import assert_value


@pytest.mark.parametrize("code,temp", (("1045", -4.5), ("0237", 23.7), ("0987", 98.7)))
def test_decimal_code(code: str, temp: Optional[float]):
    """Tests that a 4-digit number gets decoded into a temperature number"""
    assert remarks.decimal_code(code).value == temp


def test_bad_decimal_code():
    """Tests empty code value"""
    assert remarks.decimal_code("") is None


@pytest.mark.parametrize(
    "codes,temperature,dewpoint",
    (
        (["123"], None, None),
        (["123", "T01231234"], 12.3, -23.4),
    ),
)
def test_temp_dew_decimal(codes: List[str], temperature: float, dewpoint: float):
    """Tests extracting temperature and dewpoint decimal values"""
    codes, temp, dew = remarks.temp_dew_decimal(codes)
    assert codes == ["123"]
    assert_value(temp, temperature)
    assert_value(dew, dewpoint)


@pytest.mark.parametrize(
    "codes,maximum,minimum",
    (
        (["123"], None, None),
        (["123", "401231432"], 12.3, -43.2),
    ),
)
def test_temp_minmax(codes: List[str], maximum: float, minimum: float):
    """Tests extracting 24-hour min max temperatures"""
    codes, tmax, tmin = remarks.temp_minmax(codes)
    assert codes == ["123"]
    assert_value(tmax, maximum)
    assert_value(tmin, minimum)


@pytest.mark.parametrize(
    "codes,precipitation,snowlevel",
    (
        (["123"], None, None),
        (["123", "P1234"], 12.34, None),
        (["123", "4/123"], None, 123),
        (["123", "P0987", "4/098"], 9.87, 98),
    ),
)
def test_precip_snow(
    codes: List[str], precipitation: Optional[float], snowlevel: Optional[int]
):
    """Tests extracting hourly precipitation and snow accumulation"""
    codes, precip, snow = remarks.precip_snow(codes)
    assert codes == ["123"]
    assert_value(precip, precipitation)
    assert_value(snow, snowlevel)


@pytest.mark.parametrize(
    "codes,pressure",
    (
        (["123"], None),
        (["123", "SLP988"], 998.8),
        (["123", "SLP241"], 1024.1),
    ),
)
def test_sea_level_pressure(codes: List[str], pressure: float):
    """Tests extracting the inferred sea level pressure in mb"""
    codes, sea = remarks.sea_level_pressure(codes)
    assert codes == ["123"]
    assert_value(sea, pressure)


def test_no_sea_level_pressure():
    codes = ["123", "SLPNO"]
    new_codes, sea = remarks.sea_level_pressure(codes)
    assert codes == new_codes
    assert sea is None


@pytest.mark.parametrize(
    "code,value,text",
    (
        ("51234", 23.4, "Increasing, then steady"),
        ("54567", 56.7, "Steady"),
    ),
)
def test_parse_pressure(code: str, value: float, text: str):
    """Tests parsing a 5-digit code to PressureTendency"""
    pressure = remarks.parse_pressure(code)
    assert pressure == structs.PressureTendency(code, text, value)


@pytest.mark.parametrize(
    "code,value",
    (
        ("61234", 12.34),
        ("70123", 1.23),
        ("70012", 0.12),
    ),
)
def test_parse_precipitation(code: str, value: float):
    """Tests parsing a 5-digit precipitation amount code"""
    assert_value(remarks.parse_precipitation(code), value)


def test_parse():
    """Tests full remarks parsing"""
    assert remarks.parse("") is None
    rmk = (
        "RMK 10123 21234 51234 61234 74321 98321 "
        "T01231234 403451567 P1234 4/123 SLP998 "
        "ACFT MSHP TSB20 AO2 $"
    )
    data = remarks.parse(rmk)
    # 5-digit codes
    assert_value(data.maximum_temperature_6, 12.3)
    assert_value(data.minimum_temperature_6, -23.4)
    pressure = structs.PressureTendency("51234", "Increasing, then steady", 23.4)
    assert data.pressure_tendency == pressure
    assert_value(data.precip_36_hours, 12.34)
    assert_value(data.precip_24_hours, 43.21)
    assert_value(data.sunshine_minutes, 321)
    # Other parsed data
    assert_value(data.temperature_decimal, 12.3)
    assert_value(data.dewpoint_decimal, -23.4)
    assert_value(data.maximum_temperature_24, 34.5)
    assert_value(data.minimum_temperature_24, -56.7)
    assert_value(data.precip_hourly, 12.34)
    assert_value(data.snow_depth, 123)
    assert_value(data.sea_level_pressure, 999.8)
    # Static codes
    static_codes = [
        structs.Code("$", "ASOS requires maintenance"),
        structs.Code("ACFT MSHP", "Aircraft mishap"),
        structs.Code("AO2", "Automated with precipitation sensor"),
        structs.Code("TSB20", "Thunderstorm began at :20"),
    ]
    assert data.codes == static_codes
