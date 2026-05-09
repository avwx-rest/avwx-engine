"""Functions for translating report data."""

from __future__ import annotations

from avwx.static.core import CLOUD_TRANSLATIONS
from avwx.structs import Cloud, Code, ReportTrans, SharedData, SharedRepr
from avwx.units import Measurement


def _fmt(value: float) -> str:
    """Format a float as int when it has no fractional part."""
    return str(int(value)) if value == int(value) else str(value)


def get_cardinal_direction(direction: float) -> str:
    """Return the cardinal direction (NSEW) for a degree direction.

    Wind Direction - Cheat Sheet:

    (360) -- 011/012 -- 033/034 -- (045) -- 056/057 -- 078/079 -- (090)

    (090) -- 101/102 -- 123/124 -- (135) -- 146/147 -- 168/169 -- (180)

    (180) -- 191/192 -- 213/214 -- (225) -- 236/237 -- 258/259 -- (270)

    (270) -- 281/282 -- 303/304 -- (315) -- 326/327 -- 348/349 -- (360)
    """
    ret = ""
    if not isinstance(direction, int):
        direction = int(direction)
    # Convert to range [0 360]
    while direction < 0:
        direction += 360
    direction = direction % 360
    if 304 <= direction <= 360 or 0 <= direction <= 56:
        ret += "N"
        if 304 <= direction <= 348:
            if 327 <= direction <= 348:
                ret += "N"
            ret += "W"
        elif 12 <= direction <= 56:
            if 12 <= direction <= 33:
                ret += "N"
            ret += "E"
    elif 124 <= direction <= 236:
        ret += "S"
        if 124 <= direction <= 168:
            if 147 <= direction <= 168:
                ret += "S"
            ret += "E"
        elif 192 <= direction <= 236:
            if 192 <= direction <= 213:
                ret += "S"
            ret += "W"
    elif 57 <= direction <= 123:
        ret += "E"
        if 57 <= direction <= 78:
            ret += "NE"
        elif 102 <= direction <= 123:
            ret += "SE"
    elif 237 <= direction <= 303:
        ret += "W"
        if 237 <= direction <= 258:
            ret += "SW"
        elif 282 <= direction <= 303:
            ret += "NW"
    return ret


_WIND_DIR_REPR = {"000": "Calm", "VRB": "Variable"}


def wind(
    direction: Measurement | None,
    speed: Measurement | None,
    gust: Measurement | None,
    vardir: list[Measurement] | None = None,
    direction_repr: str | None = None,
    *,
    cardinals: bool = True,
) -> str:
    """Format wind elements into a readable sentence.

    Ex: NNE-020 (variable 010 to 040) at 14kt gusting to 20kt
    """
    ret = ""
    is_calm = direction_repr == "000"
    if direction_repr and direction_repr in _WIND_DIR_REPR:
        ret += _WIND_DIR_REPR[direction_repr]
    elif direction is not None:
        if cardinals:
            ret += f"{get_cardinal_direction(direction.magnitude)}-"
        ret += direction_repr or str(int(direction.magnitude))
    if vardir and len(vardir) >= 2:
        dirs = [str(int(v.magnitude)).zfill(3) for v in vardir]
        ret += f" (variable {dirs[0]} to {dirs[1]})"
    if speed and not is_calm:
        ret += f" at {_fmt(speed.magnitude)}{speed.unit}"
    if gust and not is_calm:
        ret += f" gusting to {_fmt(gust.magnitude)}{gust.unit}"
    return ret


_VIS_REPR = {
    "P6": "Greater than 6sm ( >10km )",
    "M1/2": "Less than .5sm ( <0.8km )",
    "M1/4": "Less than .25sm ( <0.4km )",
    "M1/8": "Less than .125sm ( <0.2km )",
}


def visibility(vis: Measurement | None, vis_repr: str | None = None) -> str:
    """Format a visibility element into a string with both km and sm values.

    Ex: 8km ( 5sm )
    """
    if not vis:
        return ""
    if vis_repr and vis_repr in _VIS_REPR:
        return _VIS_REPR[vis_repr]
    unit = vis.unit
    value = vis.magnitude
    if unit == "sm":
        kilometers = value / 0.621371
        converted = str(round(kilometers, 1)).replace(".0", "") + "km"
        value_str = str(value).replace(".0", "")
        return f"{value_str}sm ({converted})"
    # meters (or km — normalise to km for display)
    if unit == "km":
        meters = value * 1000
    else:
        meters = value
    miles = meters * 0.000621371
    converted = str(round(miles, 1)).replace(".0", "") + "sm"
    value_str = str(round(meters / 1000, 1)).replace(".0", "")
    return f"{value_str}km ({converted})"


def temperature(temp: Measurement | None) -> str:
    """Format a temperature element into a string with both C and F values.

    Ex: 34°C (93°F)
    """
    if temp is None:
        return ""
    value = temp.magnitude
    unit = temp.unit
    if unit == "degC":
        fahrenheit = round(value * 1.8 + 32)
        return f"{_fmt(value)}°C ({fahrenheit}°F)"
    if unit == "degF":
        celsius = round((value - 32) / 1.8)
        return f"{_fmt(value)}°F ({celsius}°C)"
    return ""


def altimeter(alt: Measurement | None) -> str:
    """Format the altimeter element into a string with hPa and inHg values.

    Ex: 30.11 inHg (1020 hPa)
    """
    if alt is None:
        return ""
    value = alt.magnitude
    unit = alt.unit
    if unit == "hPa":
        inches = round(value / 33.8638866667, 2)
        converted = str(inches).ljust(5, "0") + " inHg"
        return f"{_fmt(value)} {unit} ({converted})"
    if unit == "inHg":
        pascals = round(value * 33.8638866667)
        value_str = str(value).ljust(5, "0")
        return f"{value_str} {unit} ({pascals} hPa)"
    return ""


def clouds(values: list[Cloud] | None) -> str:
    """Format cloud list into a readable sentence.

    Ex: Broken layer at 2200ft (Cumulonimbus), Overcast layer at 3600ft - Reported AGL
    """
    if values is None:
        return ""
    ret = []
    for cloud in values:
        if cloud.base is None:
            continue
        cloud_str = CLOUD_TRANSLATIONS.get(cloud.type, CLOUD_TRANSLATIONS[None])
        if cloud.modifier and cloud.modifier in CLOUD_TRANSLATIONS:
            cloud_str += f" ({CLOUD_TRANSLATIONS[cloud.modifier]})"
        ret.append(cloud_str.format(int(cloud.base.magnitude), cloud.base.unit))
    return ", ".join(ret) + " - Reported AGL" if ret else "Sky clear"


def wx_codes(codes: list[Code]) -> str:
    """Join WX code values."""
    return ", ".join(code.value for code in codes)


def current_shared(data: SharedData, repr: SharedRepr) -> ReportTrans:
    """Translate Visibility, Altimeter, Clouds, and Other."""
    return ReportTrans(
        visibility=visibility(data.visibility, repr.visibility),
        altimeter=altimeter(data.altimeter),
        clouds=clouds(data.clouds),
        wx_codes=wx_codes(data.wx_codes),
    )
