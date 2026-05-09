"""Remarks data translation handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from avwx.structs import PressureTendency, RemarksData
    from avwx.units import Measurement


def _temp_str(m: Measurement) -> str:
    return f"{m.magnitude}°C"


def temp_minmax(label: str, temp: Measurement) -> str:
    """Translate a minimum or maximum temperature value."""
    return f"6-hour {label} temperature {_temp_str(temp)}"


def pressure_tendency(pressure: PressureTendency) -> str:
    """Translate a pressure outlook value.

    Ex: "50123" -> 12.3 hPa: Increasing, then decreasing
    """
    value = f"{pressure.change.magnitude} {pressure.change.unit} - {pressure.tendency}"
    return f"3-hour pressure difference: +/- {value}"


def precip(label: str, amount: Measurement) -> str:
    """Translate a labelled precipitation value."""
    return f"Precipitation in the last {label}: {amount.magnitude} {amount.unit}"


def sunshine_duration(minutes: float) -> str:
    """Translate a sunlight duration value."""
    return f"Duration of sunlight: {minutes} minutes"


def snow_depth(depth: Measurement) -> str:
    """Translate a snow accumulation value."""
    return f"Snow accumulation: {depth.magnitude} {depth.unit}"


def sea_level_pressure(pressure: Measurement) -> str:
    """Translate a sea level pressure value."""
    return f"Sea level pressure: {pressure.magnitude} {pressure.unit}"


def remarks_data(data: RemarksData) -> dict[str, str]:
    """Extract translations from parsed remarks data."""
    ret: dict[str, str] = {}
    if data.temperature_decimal:
        temp = data.temperature_decimal
        dew_str = (
            f" and dewpoint {_temp_str(data.dewpoint_decimal)}" if data.dewpoint_decimal else ""
        )
        ret["temperature_decimal"] = f"Temperature {_temp_str(temp)}{dew_str}"
    if data.minimum_temperature_24 and data.maximum_temperature_24:
        minimum, maximum = data.minimum_temperature_24, data.maximum_temperature_24
        ret["temperature_24h"] = (
            f"24-hour temperature: max {_temp_str(maximum)} min {_temp_str(minimum)}"
        )
    if data.maximum_temperature_6:
        ret["maximum_temperature_6h"] = temp_minmax("maximum", data.maximum_temperature_6)
    if data.minimum_temperature_6:
        ret["minimum_temperature_6h"] = temp_minmax("minimum", data.minimum_temperature_6)
    if data.precip_36_hours:
        ret["precip_36h"] = precip("3/6 hours", data.precip_36_hours)
    if data.precip_24_hours:
        ret["precip_24h"] = precip("24 hours", data.precip_24_hours)
    if data.precip_hourly:
        ret["precip_hourly"] = precip("hour", data.precip_hourly)
    if data.pressure_tendency:
        ret[data.pressure_tendency.repr] = pressure_tendency(data.pressure_tendency)
    if data.sunshine_minutes is not None:
        ret["sunshine_minutes"] = sunshine_duration(data.sunshine_minutes)
    if data.snow_depth:
        ret["snow_depth"] = snow_depth(data.snow_depth)
    if data.sea_level_pressure:
        ret["sea_level_pressure"] = sea_level_pressure(data.sea_level_pressure)
    return ret


def translate(raw: str | None, data: RemarksData | None) -> dict[str, str]:
    """Translate elements in the remarks string."""
    if not (raw and data):
        return {}
    ret = {code.repr: code.value for code in data.codes}
    ret |= remarks_data(data)
    return ret
