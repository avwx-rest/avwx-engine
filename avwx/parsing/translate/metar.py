"""METAR data translation handlers."""

import avwx.parsing.translate.base as _trans
from avwx.parsing.translate import remarks
from avwx.structs import MetarData, MetarRepr, MetarTrans


def translate_metar(data: MetarData, repr: MetarRepr) -> MetarTrans:
    """Return translations for a MetarData object."""
    shared = _trans.current_shared(data, repr)
    return MetarTrans(
        altimeter=shared.altimeter,
        clouds=shared.clouds,
        visibility=shared.visibility,
        wx_codes=shared.wx_codes,
        wind=_trans.wind(
            data.wind_direction,
            data.wind_speed,
            data.wind_gust,
            data.wind_variable_direction,
            direction_repr=repr.wind_direction,
        ),
        temperature=_trans.temperature(data.temperature),
        dewpoint=_trans.temperature(data.dewpoint),
        remarks=remarks.translate(data.remarks, data.remarks_info),
    )
