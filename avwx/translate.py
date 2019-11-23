"""
Contains functions for translating report data
"""

from avwx import _core, remarks
from avwx.static import (
    CLOUD_TRANSLATIONS,
    ICING_CONDITIONS,
    TURBULENCE_CONDITIONS,
    WX_TRANSLATIONS,
)
from avwx.structs import (
    Cloud,
    MetarData,
    MetarTrans,
    Number,
    ReportData,
    TafData,
    TafLineTrans,
    TafTrans,
    Units,
)


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
    vardir: [Number] = None,
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
    return f"{temp.value}°{unit} ({converted})"


def altimeter(alt: Number, unit: str = "hPa") -> str:
    """
    Formats the altimeter element into a string with hPa and inHg values

    Ex: 30.11 inHg (10.20 hPa)
    """
    if not (alt and unit in ("hPa", "inHg")):
        return ""
    if unit == "hPa":
        value = alt.repr
        converted = alt.value / 33.8638866667
        converted = str(round(converted, 2)) + " inHg"
    elif unit == "inHg":
        value = alt.repr[:2] + "." + alt.repr[2:]
        converted = alt.value * 33.8638866667
        converted = str(int(round(converted))) + " hPa"
    return f"{value} {unit} ({converted})"


def clouds(clouds: [Cloud], unit: str = "ft") -> str:
    """
    Format cloud list into a readable sentence

    Returns the translation string

    Ex: Broken layer at 2200ft (Cumulonimbus), Overcast layer at 3600ft - Reported AGL
    """
    if clouds is None:
        return ""
    ret = []
    for cloud in clouds:
        if cloud.base is None:
            continue
        cloud_str = CLOUD_TRANSLATIONS[cloud.type]
        if cloud.modifier and cloud.modifier in CLOUD_TRANSLATIONS:
            cloud_str += f" ({CLOUD_TRANSLATIONS[cloud.modifier]})"
        ret.append(cloud_str.format(cloud.base * 100, unit))
    if ret:
        return ", ".join(ret) + " - Reported AGL"
    return "Sky clear"


def wxcode(code: str) -> str:
    """
    Translates weather codes into readable strings

    Returns translated string of variable length
    """
    if not code:
        return ""
    ret = ""
    if code[0] == "+":
        ret = "Heavy "
        code = code[1:]
    elif code[0] == "-":
        ret = "Light "
        code = code[1:]
    # Return code if code is not a code, ex R03/03002V03
    if len(code) not in [2, 4, 6]:
        return code
    for _ in range(len(code) // 2):
        if code[:2] in WX_TRANSLATIONS:
            ret += WX_TRANSLATIONS[code[:2]] + " "
        else:
            ret += code[:2]
        code = code[2:]
    return ret.strip()


def other_list(wxcodes: [str]) -> str:
    """
    Translate the list of wx codes (otherList) into a readable sentence

    Returns the translation string
    """
    return ", ".join([wxcode(code) for code in wxcodes])


def wind_shear(
    shear: str, unit_alt: str = "ft", unit_wind: str = "kt", spoken: bool = False
) -> str:
    """
    Translate wind shear into a readable string

    Ex: Wind shear 2000ft from 140 at 30kt
    """
    if not shear or "WS" not in shear or "/" not in shear:
        return ""
    shear = shear[2:].rstrip(unit_wind.upper()).split("/")
    wdir = _core.spoken_number(shear[1][:3]) if spoken else shear[1][:3]
    return f"Wind shear {int(shear[0])*100}{unit_alt} from {wdir} at {shear[1][3:]}{unit_wind}"


def turb_ice(turb_ice: [str], unit: str = "ft") -> str:
    """
    Translate the list of turbulence or icing into a readable sentence

    Ex: Occasional moderate turbulence in clouds from 3000ft to 14000ft
    """
    if not turb_ice:
        return ""
    # Determine turbulence or icing
    if turb_ice[0][0] == "5":
        conditions = TURBULENCE_CONDITIONS
    elif turb_ice[0][0] == "6":
        conditions = ICING_CONDITIONS
    else:
        return ""
    # Create list of split items (type, floor, height)
    split = []
    for item in turb_ice:
        if len(item) == 6:
            split.append([item[1:2], item[2:5], item[5]])
    # Combine items that cover a layer greater than 9000ft
    for i in reversed(range(len(split) - 1)):
        if (
            split[i][2] == "9"
            and split[i][0] == split[i + 1][0]
            and int(split[i + 1][1]) == (int(split[i][1]) + int(split[i][2]) * 10)
        ):
            split[i][2] = str(int(split[i][2]) + int(split[i + 1][2]))
            split.pop(i + 1)
    # Return joined, formatted string from split items
    return ", ".join(
        "{conditions} from {low_alt}{unit} to {high_alt}{unit}".format(
            conditions=conditions[item[0]],
            low_alt=int(item[1]) * 100,
            high_alt=int(item[1]) * 100 + int(item[2]) * 1000,
            unit=unit,
        )
        for item in split
    )


def min_max_temp(temp: str, unit: str = "C") -> str:
    """
    Format the Min and Max temp elements into a readable string

    Ex: Maximum temperature of 23°C (73°F) at 18-15:00Z
    """
    if not temp or len(temp) < 7:
        return ""
    if temp[:2] == "TX":
        temp_type = "Maximum"
    elif temp[:2] == "TN":
        temp_type = "Minimum"
    else:
        return ""
    temp = temp[2:].replace("M", "-").replace("Z", "").split("/")
    if len(temp[1]) > 2:
        temp[1] = temp[1][:2] + "-" + temp[1][2:]
    temp_value = temperature(_core.make_number(temp[0]), unit)
    return f"{temp_type} temperature of {temp_value} at {temp[1]}:00Z"


def shared(wxdata: ReportData, units: Units) -> {str: str}:
    """
    Translate Visibility, Altimeter, Clouds, and Other
    """
    translations = {}
    translations["visibility"] = visibility(wxdata.visibility, units.visibility)
    translations["altimeter"] = altimeter(wxdata.altimeter, units.altimeter)
    translations["clouds"] = clouds(wxdata.clouds, units.altitude)
    translations["other"] = other_list(wxdata.other)
    return translations


def metar(wxdata: MetarData, units: Units) -> MetarTrans:
    """
    Translate the results of metar.parse

    Keys: Wind, Visibility, Clouds, Temperature, Dewpoint, Altimeter, Other
    """
    translations = shared(wxdata, units)
    translations["wind"] = wind(
        wxdata.wind_direction,
        wxdata.wind_speed,
        wxdata.wind_gust,
        wxdata.wind_variable_direction,
        units.wind_speed,
    )
    translations["temperature"] = temperature(wxdata.temperature, units.temperature)
    translations["dewpoint"] = temperature(wxdata.dewpoint, units.temperature)
    translations["remarks"] = remarks.translate(wxdata.remarks)
    return MetarTrans(**translations)


def taf(wxdata: TafData, units: Units) -> TafTrans:
    """
    Translate the results of taf.parse

    Keys: Forecast, Min-Temp, Max-Temp

    Forecast keys: Wind, Visibility, Clouds, Altimeter, Wind-Shear, Turbulence, Icing, Other
    """
    translations = {"forecast": []}
    for line in wxdata.forecast:
        trans = shared(line, units)
        trans["wind"] = wind(
            line.wind_direction, line.wind_speed, line.wind_gust, unit=units.wind_speed
        )
        trans["wind_shear"] = wind_shear(
            line.wind_shear, units.altitude, units.wind_speed
        )
        trans["turbulence"] = turb_ice(line.turbulence, units.altitude)
        trans["icing"] = turb_ice(line.icing, units.altitude)
        # Remove false 'Sky Clear' if line type is 'BECMG'
        if line.type == "BECMG" and trans["clouds"] == "Sky clear":
            trans["clouds"] = None
        translations["forecast"].append(TafLineTrans(**trans))
    translations["min_temp"] = min_max_temp(wxdata.min_temp, units.temperature)
    translations["max_temp"] = min_max_temp(wxdata.max_temp, units.temperature)
    translations["remarks"] = remarks.translate(wxdata.remarks)
    return TafTrans(**translations)
