"""
# GFS MOS MAV

The [MAV report](https://www.nws.noaa.gov/mdl/synop/mavcard.php) is a
short-range forecast (6-72 hours) based on the [Global Forecast
System](https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/global-forcast-system-gfs)
model output and is only valid for ICAO stations in the United States, Puerto
Rico, and US Virgin Islands. Reports are published every six hours starting at
0000 UTC.

# GFS MOS MEX

The [MEX report](https://www.nws.noaa.gov/mdl/synop/mexcard.php) is an
extended-range forecast (24-192 hours) based on the [Global Forecast
System](https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/global-forcast-system-gfs)
model output and is only valid for ICAO stations in the United States, Puerto
Rico, and US Virgin Islands. Reports are published at 0000 and 1200 UTC.
"""

from __future__ import annotations

import avwx.static.gfs as static
from avwx.forecast.base import (
    Forecast,
    _code,
    _find_time_periods,
    _init_parse,
    _measurements,
    _parse_lines,
    _probabilities,
    _split_line,
    _trim_lines,
)
from avwx.service import NoaaGfs
from avwx.structs import MavData, MavPeriod, MexData, MexPeriod

# Typed line parsers
_temperature = _measurements("degF")
_direction = _measurements("degree", postfix="0")
_wind_speed = _measurements("kt")
_probability = _probabilities()

_precip_amount = _code(static.PRECIPITATION_AMOUNT)

_HANDLERS = {
    "X/N": ("temperature_minmax", _temperature),
    "TMP": ("temperature", _temperature),
    "DPT": ("dewpoint", _temperature),
    "CLD": ("cloud", _code(static.CLOUD)),
    "WDR": ("wind_direction", _direction),
    "WSP": ("wind_speed", _wind_speed),
    "P06": ("precip_chance_6", _probability),
    "P12": ("precip_chance_12", _probability),
    "P24": ("precip_chance_24", _probability),
    "Q06": ("precip_amount_6", _precip_amount),
    "Q12": ("precip_amount_12", _precip_amount),
    "Q24": ("precip_amount_24", _precip_amount),
    "TYP": ("precip_type", _code(static.PRECIPITATION_TYPE)),
}

_MAV_HANDLERS = {
    **_HANDLERS,
    "T06": ("thunderstorm_6", "severe_storm_6", None),  # replaced by _thunder below
    "T12": ("thunderstorm_12", "severe_storm_12", None),
    "POZ": ("freezing_precip", _probability),
    "POS": ("snow", _probability),
    "CIG": ("ceiling", _code(static.CEILING_HEIGHT)),
    "VIS": ("visibility", _code(static.VISIBILITY)),
    "OBV": ("vis_obstruction", _code(static.VISIBILITY_OBSTRUCTION)),
}

_MEX_HANDLERS = {
    **_HANDLERS,
    "T12": ("thunderstorm_12", _probability),
    "T24": ("thunderstorm_24", _probability),
    "PZP": ("freezing_precip", _probability),
    "PRS": ("rain_snow_mix", _probability),
    "PSN": ("snow", _probability),
    "SNW": ("snow_amount_24", _code(static.SNOWFALL_AMOUNT)),
}

_ThunderList = list[tuple[float, float] | None]


def _thunder(line: str, size: int = 3) -> _ThunderList:
    """Parse thunder line into (thunderstorm, severe_storm) probability tuples."""
    ret: _ThunderList = []
    previous: float | None = None
    for item in _split_line(line, size=size, prefix=5, strip=" /"):
        if not item:
            ret.append(None)
        elif previous is not None:
            try:
                ret.append((previous, float(item)))
            except ValueError:
                ret.append(None)
            previous = None
        else:
            ret.append(None)
            try:
                previous = float(item)
            except ValueError:
                previous = None
    return ret


# Patch the thunder handlers with the actual function
_MAV_HANDLERS["T06"] = ("thunderstorm_6", "severe_storm_6", _thunder)
_MAV_HANDLERS["T12"] = ("thunderstorm_12", "severe_storm_12", _thunder)


class Mav(Forecast):
    '''
    The Mav class offers an object-oriented approach to managing MOS MAV data
    for a single station.

    Below is typical usage for fetching and pulling MAV data for KJFK.

    ```python
    >>> from avwx import Mav
    >>> kjfk = Mav("KJFK")
    >>> kjfk.station.name
    'John F Kennedy International Airport'
    >>> kjfk.update()
    True
    >>> kjfk.last_updated
    datetime.datetime(2020, 4, 20, 1, 7, 7, 393270, tzinfo=datetime.timezone.utc)
    >>> print(kjfk.raw)
    """
    KJFK   GFS MOS GUIDANCE    4/19/2020  1800 UTC
    ...
    """
    >>> len(kjfk.data.forecast)
    21
    >>> kjfk.data.forecast[0].ceiling
    Code(repr='7', value='6600 - 12,000 feet')
    ```

    The `parse` and `from_report` methods can parse a report string if you want
    to override the normal fetching process.
    '''

    report_type = "mav"
    _service_class = NoaaGfs  # type: ignore

    async def _post_update(self) -> None:
        if self.raw is None:
            return
        self.data = parse_mav(self.raw)

    def _post_parse(self) -> None:
        if self.raw is None:
            return
        self.data = parse_mav(self.raw)


class Mex(Forecast):
    '''
    The Mex class offers an object-oriented approach to managing MOS MEX data
    for a single station.

    The `parse` and `from_report` methods can parse a report string if you want
    to override the normal fetching process.
    '''

    report_type = "mex"
    _service_class = NoaaGfs  # type: ignore

    async def _post_update(self) -> None:
        if self.raw is None:
            return
        self.data = parse_mex(self.raw)

    def _post_parse(self) -> None:
        if self.raw is None:
            return
        self.data = parse_mex(self.raw)


def parse_mav(report: str) -> MavData | None:
    """Parser for GFS MAV reports."""
    if not report:
        return None
    data, lines = _init_parse(report)
    lines = _trim_lines(lines, 2)
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


def parse_mex(report: str) -> MexData | None:
    """Parser for GFS MEX reports."""
    if not report:
        return None
    data, lines = _init_parse(report)
    lines = _trim_lines(lines, 1)
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
