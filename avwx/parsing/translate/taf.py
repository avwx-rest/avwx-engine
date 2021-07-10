"""
TAF data translation handlers
"""

# stdlib
from typing import List, Optional

# module
import avwx.parsing.translate.base as _trans
from avwx.parsing import core

from avwx.parsing.translate import remarks
from avwx.static.taf import ICING_CONDITIONS, TURBULENCE_CONDITIONS
from avwx.structs import TafData, TafLineTrans, TafTrans, Units


def wind_shear(
    shear: Optional[str],
    unit_alt: str = "ft",
    unit_wind: str = "kt",
    spoken: bool = False,
) -> str:
    """Translate wind shear into a readable string

    Ex: Wind shear 2000ft from 140 at 30kt
    """
    if not shear or "WS" not in shear or "/" not in shear:
        return ""
    altitude, wind = shear[2:].rstrip(unit_wind.upper()).split("/")
    wdir = core.spoken_number(wind[:3], True) if spoken else wind[:3]
    return (
        f"Wind shear {int(altitude)*100}{unit_alt} from {wdir} at {wind[3:]}{unit_wind}"
    )


def turb_ice(values: List[str], unit: str = "ft") -> str:
    """Translate the list of turbulence or icing into a readable sentence

    Ex: Occasional moderate turbulence in clouds from 3000ft to 14000ft
    """
    if not values:
        return ""
    # Determine turbulence or icing
    if values[0][0] == "5":
        conditions = TURBULENCE_CONDITIONS
    elif values[0][0] == "6":
        conditions = ICING_CONDITIONS
    else:
        return ""
    # Create list of split items (type, floor, height)
    split = []
    for item in values:
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


def min_max_temp(temp: Optional[str], unit: str = "C") -> str:
    """Format the Min and Max temp elements into a readable string

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
    value, time = temp[2:].replace("M", "-").replace("Z", "").strip("/").split("/")
    if len(time) > 2:
        time = time[:2] + "-" + time[2:]
    translation = _trans.temperature(core.make_number(value), unit)
    return f"{temp_type} temperature of {translation} at {time}:00Z"


def translate_taf(wxdata: TafData, units: Units) -> TafTrans:
    """Returns translations for a TafData object"""
    forecast: List[TafLineTrans] = []
    for line in wxdata.forecast:
        shared = _trans.current_shared(line, units)
        # Remove false 'Sky Clear' if line type is 'BECMG'
        clouds = shared.clouds
        if line.type == "BECMG" and clouds == "Sky clear":
            clouds = ""
        struct = TafLineTrans(
            altimeter=shared.altimeter,
            clouds=clouds,
            wx_codes=shared.wx_codes,
            visibility=shared.visibility,
            wind=_trans.wind(
                line.wind_direction,
                line.wind_speed,
                line.wind_gust,
                unit=units.wind_speed,
            ),
            wind_shear=wind_shear(line.wind_shear, units.altitude, units.wind_speed),
            turbulence=turb_ice(line.turbulence, units.altitude),
            icing=turb_ice(line.icing, units.altitude),
        )
        forecast.append(struct)
    return TafTrans(
        forecast=forecast,
        max_temp=min_max_temp(wxdata.max_temp, units.temperature),
        min_temp=min_max_temp(wxdata.min_temp, units.temperature),
        remarks=remarks.translate(wxdata.remarks, wxdata.remarks_info),
    )
