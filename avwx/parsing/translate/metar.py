"""
METAR data translation handlers
"""

import avwx.parsing.translate.base as _trans
from avwx.parsing.translate import remarks
from avwx.structs import MetarData, MetarTrans, Units


def translate_metar(wxdata: MetarData, units: Units) -> MetarTrans:
    """Returns translations for a MetarData object"""
    shared = _trans.current_shared(wxdata, units)
    return MetarTrans(
        altimeter=shared.altimeter,
        clouds=shared.clouds,
        visibility=shared.visibility,
        wx_codes=shared.wx_codes,
        wind=_trans.wind(
            wxdata.wind_direction,
            wxdata.wind_speed,
            wxdata.wind_gust,
            wxdata.wind_variable_direction,
            units.wind_speed,
        ),
        temperature=_trans.temperature(wxdata.temperature, units.temperature),
        dewpoint=_trans.temperature(wxdata.dewpoint, units.temperature),
        remarks=remarks.translate(wxdata.remarks, wxdata.remarks_info),
    )
