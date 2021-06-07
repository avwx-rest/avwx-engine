"""
Remarks data translation handlers
"""

# stdlib
from typing import Dict, Optional
from avwx.structs import Number, PressureTendency, RemarksData


def temp_minmax(label: str, code: Number) -> str:
    """Translates a minimum or maximum temperature value"""
    return f"6-hour {label} temperature {code.value}°C"


def pressure_tendency(pressure: PressureTendency, unit: str = "mb") -> str:
    """Translates a pressure outlook value

    Ex: "50123" -> 12.3 mb: Increasing, then decreasing
    """
    value = f"{pressure.change} {unit} - {pressure.tendency}"
    return "3-hour pressure difference: +/- " + value


def precip(label: str, code: Number, unit: str = "in") -> str:
    """Translates a labelled precipitation value"""
    return f"Precipitation in the last {label}: {code.value} {unit}"


def sunshine_duration(code: Number, unit: str = "minutes") -> str:
    """Translates a sunlight duration value"""
    return f"Duration of sunlight: {code.value} {unit}"


def snow_depth(code: Number, unit: str = "in") -> str:
    """Translates a snow accumulation value"""
    return f"Snow accumulation: {code.value} {unit}"


def sea_level_pressure(code: Number) -> str:
    """Translates a sea level pressure value"""
    return f"Sea level pressure: {code.value} hPa"


def remarks_data(data: RemarksData) -> Dict[str, str]:
    """Extract translations from parsed remarks data"""
    ret = {}
    if data.temperature_decimal and data.dewpoint_decimal:
        temp, dew = data.temperature_decimal, data.dewpoint_decimal
        key = f"T{temp.repr}{dew.repr}"
        ret[key] = f"Temperature {temp.value}°C and dewpoint {dew.value}°C"
    if data.minimum_temperature_24 and data.maximum_temperature_24:
        minimum, maximum = data.minimum_temperature_24, data.maximum_temperature_24
        key = f"4{minimum.repr}{maximum.repr}"
        ret[key] = f"24-hour temperature: max {maximum.value} min {minimum.value}"
    if data.maximum_temperature_6:
        key = data.maximum_temperature_6.repr
        ret[key] = temp_minmax("maximum", data.maximum_temperature_6)
    if data.minimum_temperature_6:
        key = data.minimum_temperature_6.repr
        ret[key] = temp_minmax("minimum", data.minimum_temperature_6)
    if data.precip_36_hours:
        ret[data.precip_36_hours.repr] = precip("3/6 hours", data.precip_36_hours)
    if data.precip_24_hours:
        ret[data.precip_24_hours.repr] = precip("24 hours", data.precip_24_hours)
    if data.precip_hourly:
        ret[data.precip_hourly.repr] = precip("hour", data.precip_hourly)
    if data.pressure_tendency:
        ret[data.pressure_tendency.repr] = pressure_tendency(data.pressure_tendency)
    if data.sunshine_minutes:
        ret[data.sunshine_minutes.repr] = sunshine_duration(data.sunshine_minutes)
    if data.snow_depth:
        ret[data.snow_depth.repr] = snow_depth(data.snow_depth)
    if data.sea_level_pressure:
        ret[data.sea_level_pressure.repr] = sea_level_pressure(data.sea_level_pressure)
    return ret


def translate(raw: Optional[str], data: Optional[RemarksData]) -> Dict[str, str]:
    """Translates elements in the remarks string"""
    if not (raw and data):
        return {}
    ret = {}
    # Add static codes
    for code in data.codes:
        ret[code.repr] = code.value
    # Add features from the parsed remarks data
    ret.update(remarks_data(data))
    return ret
