"""
Contains functions for translating report data
"""

# stdlib
from typing import Dict, List

# module
from avwx.static.core import CLOUD_TRANSLATIONS
from avwx.structs import Cloud, Code, Number, SharedData, Units


def get_cardinal_direction(direction: int) -> str:
    """
    Returns the cardinal direction (NSEW) for a degree direction

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


WIND_DIR_REPR = {"000": "Calm", "VRB": "Variable"}


def wind(
    direction: Number,
    speed: Number,
    gust: Number,
    vardir: List[Number] = None,
    unit: str = "kt",
    cardinals: bool = True,
    spoken: bool = False,
) -> str:
    """
    Format wind elements into a readable sentence

    Returns the translation string

    Ex: NNE-020 (variable 010 to 040) at 14kt gusting to 20kt
    """
    ret = ""
    target = "spoken" if spoken else "repr"
    # Wind direction
    if direction:
        if direction.repr in WIND_DIR_REPR:
            ret += WIND_DIR_REPR[direction.repr]
        elif direction.value is None:
            ret += direction.repr
        else:
            if cardinals:
                ret += get_cardinal_direction(direction.value) + "-"
            ret += getattr(direction, target)
    # Variable direction
    if vardir and isinstance(vardir, list):
        vardir = [getattr(var, target) for var in vardir]
        ret += " (variable {} to {})".format(*vardir)
    # Speed
    if speed and speed.value:
        ret += f" at {speed.value}{unit}"
    # Gust
    if gust and gust.value:
        ret += f" gusting to {gust.value}{unit}"
    return ret


VIS_REPR = {
    "P6": "Greater than 6sm ( >10km )",
    "M1/4": "Less than .25sm ( <0.4km )",
    "M1/8": "Less than .125sm ( <0.2km )",
}


def visibility(vis: Number, unit: str = "m") -> str:
    """
    Formats a visibility element into a string with both km and sm values

    Ex: 8km ( 5sm )
    """
    if not (vis and unit in ("m", "sm")):
        return ""
    if vis.repr in VIS_REPR:
        return VIS_REPR[vis.repr]
    if unit == "m":
        converted = vis.value * 0.000621371
        converted = str(round(converted, 1)).replace(".0", "") + "sm"
        value = str(round(vis.value / 1000, 1)).replace(".0", "")
        unit = "km"
    elif unit == "sm":
        converted = vis.value / 0.621371
        converted = str(round(converted, 1)).replace(".0", "") + "km"
        value = str(vis.value).replace(".0", "")
    else:
        return ""
    return f"{value}{unit} ({converted})"


def temperature(temp: Number, unit: str = "C") -> str:
    """
    Formats a temperature element into a string with both C and F values

    Used for both Temp and Dew

    Ex: 34°C (93°F)
    """
    unit = unit.upper()
    if not (temp and unit in ("C", "F")):
        return ""
    if unit == "C":
        converted = temp.value * 1.8 + 32
        converted = str(int(round(converted))) + "°F"
    elif unit == "F":
        converted = (temp.value - 32) / 1.8
        converted = str(int(round(converted))) + "°C"
    else:
        return ""
    return f"{temp.value}°{unit} ({converted})"


def altimeter(alt: Number, unit: str = "hPa") -> str:
    """
    Formats the altimeter element into a string with hPa and inHg values

    Ex: 30.11 inHg (10.20 hPa)
    """
    if not (alt and unit in ("hPa", "inHg")):
        return ""
    if unit == "hPa":
        value = alt.value
        converted = round(alt.value / 33.8638866667, 2)
        converted = str(converted).ljust(5, "0") + " inHg"
    elif unit == "inHg":
        value = str(alt.value).ljust(5, "0")
        converted = alt.value * 33.8638866667
        converted = str(int(round(converted))) + " hPa"
    else:
        return ""
    return f"{value} {unit} ({converted})"


def clouds(values: List[Cloud], unit: str = "ft") -> str:
    """
    Format cloud list into a readable sentence

    Returns the translation string

    Ex: Broken layer at 2200ft (Cumulonimbus), Overcast layer at 3600ft - Reported AGL
    """
    if values is None:
        return ""
    ret = []
    for cloud in values:
        if cloud.base is None:
            continue
        cloud_str = CLOUD_TRANSLATIONS[cloud.type]
        if cloud.modifier and cloud.modifier in CLOUD_TRANSLATIONS:
            cloud_str += f" ({CLOUD_TRANSLATIONS[cloud.modifier]})"
        ret.append(cloud_str.format(cloud.base * 100, unit))
    if ret:
        return ", ".join(ret) + " - Reported AGL"
    return "Sky clear"


def wx_codes(codes: List[Code]) -> str:
    """
    Join WX code values

    Returns the translation string
    """
    return ", ".join(code.value for code in codes)


def current_shared(wxdata: SharedData, units: Units) -> Dict[str, str]:
    """
    Translate Visibility, Altimeter, Clouds, and Other
    """
    data = {}
    data["visibility"] = visibility(wxdata.visibility, units.visibility)
    data["altimeter"] = altimeter(wxdata.altimeter, units.altimeter)
    data["clouds"] = clouds(wxdata.clouds, units.altitude)
    data["wx_codes"] = wx_codes(wxdata.wx_codes)
    return data
