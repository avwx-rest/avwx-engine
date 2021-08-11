"""
GFS data translation handlers
"""

# pylint: skip-file
# mypy: ignore-errors

raise NotImplementedError()

from typing import List

import avwx.parsing.translate.base as _trans
from avwx.structs import (
    GfsPeriod,
    GfsPeriodTrans,
    MavData,
    MavPeriodTrans,
    MexData,
    MexPeriodTrans,
    Units,
)


def _gfs_shared(
    line: GfsPeriod, units: Units, dataobj: GfsPeriodTrans
) -> GfsPeriodTrans:
    """"""
    data = {}
    data["temperature"] = _trans.temperature(line.temperature, units.temperature)
    data["dewpoint"] = _trans.temperature(line.dewpoint, units.temperature)
    data["cloud"] = None
    return dataobj(**data)


def translate_mav(wxdata: MavData, units: Units) -> List[MavPeriodTrans]:
    """Returns translations for a TafData object"""
    data = []
    for line in wxdata.forecast:
        _data = _gfs_shared(line, units, MavPeriodTrans)
    return data


def translate_mex(wxdata: MexData, units: Units) -> List[MexPeriodTrans]:
    """Returns translations for a TafData object"""
    data = []
    return data
