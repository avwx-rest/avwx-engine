"""
METAR data translation handlers
"""

import avwx.parsing.translate.base as _trans
from avwx.parsing import remarks
from avwx.structs import MetarData, MetarTrans, Units


def translate_metar(wxdata: MetarData, units: Units) -> MetarTrans:
    """
    Returns translations for a MetarData object
    """
    data = _trans.current_shared(wxdata, units)
    data["wind"] = _trans.wind(
        wxdata.wind_direction,
        wxdata.wind_speed,
        wxdata.wind_gust,
        wxdata.wind_variable_direction,
        units.wind_speed,
    )
    data["temperature"] = _trans.temperature(wxdata.temperature, units.temperature)
    data["dewpoint"] = _trans.temperature(wxdata.dewpoint, units.temperature)
    data["remarks"] = remarks.translate(wxdata.remarks)
    return MetarTrans(**data)
