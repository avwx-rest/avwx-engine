"""
Parsing for NOAA GFS forecasts
"""

# stdlib
from typing import List, Optional, Tuple

# module
import avwx.static.gfs as static
from avwx.parsing import core
from avwx.service import NOAA_GFS
from avwx.structs import (
    MavData,
    MavPeriod,
    MexData,
    MexPeriod,
    Number,
    Units,
)
from .base import (
    Forecast,
    _code,
    _direction,
    _find_time_periods,
    _init_parse,
    _numbers,
    _parse_lines,
    _split_line,
)


ThunderList = List[Optional[Tuple[Optional[Number], Optional[Number]]]]


def _thunder(line: str, size: int = 3) -> ThunderList:
    """Parse thunder line into Number tuples"""
    ret: ThunderList = []
    previous = None
    for item in _split_line(line, size=size, prefix=5, strip=" /"):
        if not item:
            ret.append(None)
        elif previous:
            ret.append((previous, core.make_number(item)))
            previous = None
        else:
            ret.append(None)
            previous = core.make_number(item)
    return ret


# pylint: disable=invalid-name
_precip_amount = _code(static.PRECIPITATION_AMOUNT)

_HANDLERS = {
    "TMP": ("temperature", _numbers),
    "DPT": ("dewpoint", _numbers),
    "CLD": ("cloud", _code(static.CLOUD)),
    "WDR": ("wind_direction", _direction),
    "WSP": ("wind_speed", _numbers),
    "P06": ("precip_chance_6", _numbers),
    "P12": ("precip_chance_12", _numbers),
    "P24": ("precip_chance_24", _numbers),
    "Q06": ("precip_amount_6", _precip_amount),
    "Q12": ("precip_amount_12", _precip_amount),
    "Q24": ("precip_amount_24", _precip_amount),
    "TYP": ("precip_type", _code(static.PRECIPITATION_TYPE)),
}


# Secondary dicts for conflicting handlers
_MAV_HANDLERS = {
    **_HANDLERS,
    "T06": ("thunderstorm_6", "severe_storm_6", _thunder),
    "T12": ("thunderstorm_12", "severe_storm_12", _thunder),
    "POZ": ("freezing_precip", _numbers),
    "POS": ("snow", _numbers),
    "CIG": ("ceiling", _code(static.CEILING_HEIGHT)),
    "VIS": ("visibility", _code(static.VISIBILITY)),
    "OBV": ("vis_obstruction", _code(static.VISIBILITY_OBSTRUCTION)),
}

_MEX_HANDLERS = {
    **_HANDLERS,
    "T12": ("thunderstorm_12", _numbers),
    "T24": ("thunderstorm_24", _numbers),
    "PZP": ("freezing_precip", _numbers),
    "PRS": ("rain_snow_mix", _numbers),
    "PSN": ("snow", _numbers),
    "SNW": ("snow_amount_24", _code(static.SNOWFALL_AMOUNT)),
}


def parse_mav(report: str) -> Optional[MavData]:
    """Parser for GFS MAV reports"""
    if not report:
        return None
    data, lines = _init_parse(report)
    period_strings = _split_line(lines[2])
    timestamp = data.time.dt if data.time else None
    periods = _find_time_periods(period_strings, timestamp)
    _parse_lines(periods, lines[3:], _MAV_HANDLERS)
    return MavData(
        raw=data.raw,
        sanitized=data.sanitized,
        station=data.station,
        time=data.time,
        remarks=data.remarks,
        forecast=[MavPeriod(**p) for p in periods],
    )


def parse_mex(report: str) -> Optional[MexData]:
    """Parser for GFS MEX reports"""
    if not report:
        return None
    data, lines = _init_parse(report)
    period_strings = _split_line(lines[1], size=4, prefix=4)
    timestamp = data.time.dt if data.time else None
    periods = _find_time_periods(period_strings, timestamp)
    _parse_lines(periods, lines[3:], _MEX_HANDLERS, size=4)
    return MexData(
        raw=data.raw,
        sanitized=data.sanitized,
        station=data.station,
        time=data.time,
        remarks=data.remarks,
        forecast=[MexPeriod(**p) for p in periods],
    )


class Mav(Forecast):
    """Class to handle GFS MAV report data"""

    report_type = "mav"
    _service_class = NOAA_GFS  # type: ignore

    async def _post_update(self):
        self.data = parse_mav(self.raw)
        self.units = Units(**static.UNITS)

    def _post_parse(self):
        self.data = parse_mav(self.raw)
        self.units = Units(**static.UNITS)


class Mex(Forecast):
    """Class to handle GFS MAV report data"""

    report_type = "mex"
    _service_class = NOAA_GFS  # type: ignore

    async def _post_update(self):
        self.data = parse_mex(self.raw)
        self.units = Units(**static.UNITS)

    def _post_parse(self):
        self.data = parse_mex(self.raw)
        self.units = Units(**static.UNITS)
