"""TAF data translation handlers."""

from __future__ import annotations

import avwx.parsing.translate.base as _trans
from avwx.parsing.translate import remarks
from avwx.static.taf import ICING_CONDITIONS, TURBULENCE_CONDITIONS
from avwx.structs import TafData, TafLineTrans, TafRepr, TafTrans
from avwx.units import Measurement


def wind_shear(shear: str | None) -> str:
    """Translate wind shear into a readable string.

    Ex: Wind shear 2000ft from 140 at 30kt
    """
    if not shear or "WS" not in shear or "/" not in shear:
        return ""
    raw = shear[2:]  # strip "WS"
    unit_wind = "KMH" if raw.endswith("KMH") else "KT"
    raw = raw[: -len(unit_wind)]
    altitude, wind = raw.split("/")
    return f"Wind shear {int(altitude) * 100}ft from {wind[:3]} at {wind[3:]}{unit_wind.lower()}"


def turb_ice(values: list[str]) -> str:
    """Translate the list of turbulence or icing into a readable sentence.

    Ex: Occasional moderate turbulence in clouds from 3000ft to 14000ft
    """
    if not values:
        return ""
    if values[0][0] == "5":
        conditions = TURBULENCE_CONDITIONS
    elif values[0][0] == "6":
        conditions = ICING_CONDITIONS
    else:
        return ""
    split = [[item[1:2], item[2:5], item[5]] for item in values if len(item) == 6]
    # Combine items covering a layer greater than 9000ft
    for i in reversed(range(len(split) - 1)):
        if (
            split[i][2] == "9"
            and split[i][0] == split[i + 1][0]
            and int(split[i + 1][1]) == (int(split[i][1]) + int(split[i][2]) * 10)
        ):
            split[i][2] = str(int(split[i][2]) + int(split[i + 1][2]))
            split.pop(i + 1)
    return ", ".join(
        f"{conditions[item[0]]} from {int(item[1]) * 100}ft to {int(item[1]) * 100 + int(item[2]) * 1000}ft"
        for item in split
    )


def min_max_temp(temp: str | None) -> str:
    """Format the Min and Max temp elements into a readable string.

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
    value, time = temp[2:].replace("M", "-").replace("Z", "").replace("//", "/").strip("/").split("/")
    if len(time) > 2:
        time = f"{time[:2]}-{time[2:]}"
    measurement = Measurement(float(value), "degC")
    return f"{temp_type} temperature of {_trans.temperature(measurement)} at {time}:00Z"


def translate_taf(data: TafData, repr: TafRepr) -> TafTrans:
    """Return translations for a TafData object."""
    forecast: list[TafLineTrans] = []
    for line, line_repr in zip(data.forecast, repr.forecast, strict=False):
        shared = _trans.current_shared(line, line_repr)
        # Remove false 'Sky Clear' if line type is 'BECMG'
        cloud_str = shared.clouds
        if line.type == "BECMG" and cloud_str == "Sky clear":
            cloud_str = ""
        struct = TafLineTrans(
            altimeter=shared.altimeter,
            clouds=cloud_str,
            wx_codes=shared.wx_codes,
            visibility=shared.visibility,
            wind=_trans.wind(
                line.wind_direction,
                line.wind_speed,
                line.wind_gust,
                line.wind_variable_direction,
                direction_repr=line_repr.wind_direction,
            ),
            wind_shear=wind_shear(line.wind_shear),
            turbulence=turb_ice(line.turbulence),
            icing=turb_ice(line.icing),
        )
        forecast.append(struct)
    return TafTrans(
        forecast=forecast,
        max_temp=min_max_temp(data.max_temp),
        min_temp=min_max_temp(data.min_temp),
        remarks=remarks.translate(data.remarks, data.remarks_info),
    )
