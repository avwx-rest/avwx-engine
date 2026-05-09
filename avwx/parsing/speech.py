"""Contains functions for converting translations into a speech string.
Currently only supports METAR.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import avwx.parsing.translate.base as translate_base
import avwx.parsing.translate.taf as translate_taf
from avwx.parsing import core
from avwx.static.core import SPOKEN_UNITS
from avwx.units import Measurement

if TYPE_CHECKING:
    from avwx.structs import Code, MetarData, MetarRepr, TafData, TafLineData, TafLineRepr, TafRepr, Timestamp


def ordinal(n: int) -> str | None:
    """Convert an int to its spoken ordinal representation."""
    if n < 0:
        return None
    return str(n) + "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4]


def _format_plural_unit(value: str, unit: str) -> str:
    spoken = SPOKEN_UNITS.get(unit, unit)
    value = re.sub(r"(?<=\b1)" + unit, f" {spoken}", value)
    return re.sub(r"(?<=\d)+" + unit, f" {spoken}s", value)


def wind(
    direction: Measurement | None,
    speed: Measurement | None,
    gust: Measurement | None,
    vardir: list[Measurement] | None = None,
    direction_repr: str | None = None,
) -> str:
    """Format wind details into a spoken word string."""
    ret = ""
    unit = speed.unit if speed else "kt"
    is_calm = direction_repr == "000"
    # Direction
    if direction_repr in ("000", "VRB"):
        ret += {"000": "Calm", "VRB": "Variable"}[direction_repr]
    elif direction is not None:
        ret += core.spoken_number(str(int(direction.magnitude)), literal=True)
    # Variable direction range
    if vardir and len(vardir) >= 2:
        dirs = [core.spoken_number(str(int(v.magnitude)).zfill(3), literal=True) for v in vardir]
        ret += f" (variable {dirs[0]} to {dirs[1]})"
    # Speed and gust use numeric values (e.g. "12kt"), then _format_plural_unit converts to "12 knots"
    if speed and not is_calm:
        from avwx.parsing.translate.base import _fmt  # noqa: PLC0415

        ret += f" at {_fmt(speed.magnitude)}{unit}"
    if gust and not is_calm:
        from avwx.parsing.translate.base import _fmt  # noqa: PLC0415

        ret += f" gusting to {_fmt(gust.magnitude)}{unit}"
    if ret and unit in SPOKEN_UNITS:
        ret = _format_plural_unit(ret, unit)
    return "Winds " + (ret or "unknown")


def temperature(header: str, temp: Measurement | None) -> str:
    """Format temperature details into a spoken word string."""
    if temp is None:
        return f"{header} unknown"
    unit = SPOKEN_UNITS.get(temp.unit, temp.unit)
    spoken = core.spoken_measurement(temp, literal=True)
    use_s = "" if spoken in ("one", "minus one") else "s"
    return " ".join((header, spoken, f"degree{use_s}", unit))


_VIS_REPR_SPOKEN: dict[str, str] = {
    "P6": "greater than six miles",
    "M1/2": "less than one half of a mile",
    "M1/4": "less than one quarter of a mile",
    "M1/8": "less than one eighth of a mile",
    "3/4": "three quarters of a mile",
    "3/2": "one and one half miles",
    "1/2": "one half of a mile",
    "1/4": "one quarter of a mile",
}


def visibility(vis: Measurement | None, vis_repr: str | None = None) -> str:
    """Format visibility details into a spoken word string."""
    if not vis:
        return "Visibility unknown"
    unit = vis.unit
    # Special and fractional repr values handled by lookup table
    if vis_repr and vis_repr in _VIS_REPR_SPOKEN:
        return f"Visibility {_VIS_REPR_SPOKEN[vis_repr]}"
    # Fraction repr not in lookup (e.g. "7/8")
    if vis_repr and "/" in vis_repr:
        fraction_spoken = core.spoken_number(vis_repr)
        ret = f"Visibility {fraction_spoken}"
        if unit in SPOKEN_UNITS:
            if "half" not in ret:
                ret += " of a"
            ret += f" {SPOKEN_UNITS[unit]}"
            if ("one half" not in ret or " and " in ret) and "of a" not in ret:
                ret += "s"
        else:
            ret += unit
        return ret
    # Numeric visibility — compute spoken value from magnitude
    value = vis.magnitude
    display_unit = "km" if unit in ("m", "km") else unit
    if unit == "m":
        value = value / 1000
    spoken_val = core.spoken_number(core.remove_leading_zeros(str(round(value, 1)).replace(".0", "")))
    ret = f"Visibility {spoken_val}"
    if display_unit in SPOKEN_UNITS:
        ret += f" {SPOKEN_UNITS[display_unit]}s"
    else:
        ret += display_unit
    return ret


def altimeter(alt: Measurement | None) -> str:
    """Format altimeter details into a spoken word string."""
    ret = "Altimeter "
    if not alt:
        return ret + "unknown"
    unit = alt.unit
    if unit == "inHg":
        ret += core.spoken_number(str(alt.magnitude).ljust(5, "0"), literal=True)
    elif unit == "hPa":
        ret += core.spoken_number(str(int(alt.magnitude)).zfill(4), literal=True)
    return ret


def wx_codes(codes: list[Code]) -> str:
    """Format wx codes into a spoken word string."""
    ret = []
    for code in codes:
        item = code.value
        if item.startswith("Vicinity"):
            item = item.removeprefix("Vicinity ") + " in the Vicinity"
        ret.append(item)
    return ". ".join(ret)


def type_and_times(
    type: str | None,  # noqa: A002
    start: Timestamp | None,
    end: Timestamp | None,
    probability: float | None = None,
) -> str:
    """Format line type and times into the beginning of a spoken line string."""
    if not type:
        return ""
    start_time = start.dt.hour if start and start.dt else "an unknown start time"
    end_time = end.dt.hour if end and end.dt else "an unknown end time"
    if type == "BECMG":
        return f"At {start_time or 'midnight'} zulu becoming"
    ret = f"From {start_time or 'midnight'} to {end_time or 'midnight'} zulu,"
    if probability is not None:
        ret += f" there's a {int(probability)}% chance for"
    if type == "INTER":
        ret += " intermittent"
    elif type == "TEMPO":
        ret += " temporary"
    return ret


def wind_shear(shear: str | None) -> str:
    """Format wind shear string into a spoken word string."""
    value = translate_taf.wind_shear(shear)
    if not value:
        return "Wind shear unknown"
    # Speak the 3-digit direction after "from "
    if "from " in value:
        parts = value.split("from ", 1)
        after = parts[1]
        # direction is the next 3 digits before " at"
        if " at" in after:
            dir_str, rest = after.split(" at", 1)
            spoken_dir = core.spoken_number(dir_str.strip(), literal=True)
            value = f"{parts[0]}from {spoken_dir} at{rest}"
    for unit in ("kt", "KMH"):
        if unit in SPOKEN_UNITS:
            value = _format_plural_unit(value, unit)
    return value


def metar(data: MetarData, repr: MetarRepr) -> str:
    """Convert MetarData into a string for text-to-speech."""
    speech = []
    if data.wind_direction and data.wind_speed:
        speech.append(
            wind(
                data.wind_direction,
                data.wind_speed,
                data.wind_gust,
                data.wind_variable_direction,
                direction_repr=repr.wind_direction,
            )
        )
    if data.visibility:
        speech.append(visibility(data.visibility, repr.visibility))
    speech.append(translate_base.clouds(data.clouds).replace(" - Reported AGL", ""))
    if data.wx_codes:
        speech.append(wx_codes(data.wx_codes))
    if data.temperature:
        speech.append(temperature("Temperature", data.temperature))
    if data.dewpoint:
        speech.append(temperature("Dew point", data.dewpoint))
    if data.altimeter:
        speech.append(altimeter(data.altimeter))
    return (". ".join([el for el in speech if el])).replace(",", ".")


def taf_line(line: TafLineData, line_repr: TafLineRepr) -> str:
    """Convert TafLineData into a string for text-to-speech."""
    speech = []
    start = type_and_times(line.type, line.start_time, line.end_time, line.probability)
    if line.wind_direction and line.wind_speed:
        speech.append(
            wind(
                line.wind_direction,
                line.wind_speed,
                line.wind_gust,
                line.wind_variable_direction,
                direction_repr=line_repr.wind_direction,
            )
        )
    if line.wind_shear:
        speech.append(wind_shear(line.wind_shear))
    if line.visibility:
        speech.append(visibility(line.visibility, line_repr.visibility))
    if line.altimeter:
        speech.append(altimeter(line.altimeter))
    if line.wx_codes:
        speech.append(wx_codes(line.wx_codes))
    if line.clouds:
        speech.append(translate_base.clouds(line.clouds).replace(" - Reported AGL", ""))
    if line.turbulence:
        speech.append(translate_taf.turb_ice(line.turbulence))
    if line.icing:
        speech.append(translate_taf.turb_ice(line.icing))
    return f"{start} " + (". ".join([el for el in speech if el])).replace(",", ".")


def taf(data: TafData, repr: TafRepr) -> str:
    """Convert TafData into a string for text-to-speech."""
    try:
        month = data.start_time.dt.strftime(r"%B")  # type: ignore
        day = ordinal(data.start_time.dt.day) or "Unknown"  # type: ignore
        ret = f"Starting on {month} {day} - "
    except AttributeError:
        ret = ""
    return ret + ". ".join(
        [taf_line(line, line_repr) for line, line_repr in zip(data.forecast, repr.forecast)]
    )
