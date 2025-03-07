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

# stdlib
from __future__ import annotations

# module
import avwx.static.gfs as static
from avwx.forecast.base import (
    Forecast,
    _code,
    _direction,
    _find_time_periods,
    _init_parse,
    _numbers,
    _parse_lines,
    _split_line,
    _trim_lines,
)
from avwx.parsing import core
from avwx.service import NoaaGfs
from avwx.structs import (
    MavData,
    MavPeriod,
    MexData,
    MexPeriod,
    Number,
    Units,
)


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
    DT /APR  20                  /APR  21                /APR  22
    HR   00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 12 18
    N/X              46          58          44          58       37
    TMP  53 52 50 48 48 50 54 56 51 49 47 46 49 53 55 52 47 45 43 41 54
    DPT  43 41 37 35 33 30 28 27 28 30 32 34 37 39 37 32 26 23 22 18 14
    CLD  OV OV OV OV OV OV OV SC FW CL CL FW BK OV OV OV BK FW CL FW SC
    WDR  20 22 26 35 02 03 02 02 34 19 20 18 18 18 18 23 29 30 29 29 28
    WSP  20 13 07 08 11 14 14 11 05 03 04 06 11 19 25 21 22 25 20 19 22
    P06         0    12     9     1     0     1    29    68     8  2  0
    P12              12           9           2          69       15
    Q06         0     0     0     0     0     0     0     2     0  0  0
    Q12               0           0           0           2        0
    T06      0/ 4  1/ 0  1/ 0  0/ 0  0/ 0  0/ 0  5/ 3 13/13  0/ 0  0/ 8
    T12                  1/ 2        0/ 0        9/ 6       14/13  1/ 8
    POZ   0  1  1  0  0  0  0  0  0  0  0  0  0  0  0  1  0  0  0  0  0
    POS   0  0  0  0  0  2  0  6  6  9  9  0 16  8  0  4  4 47 60 67 42
    TYP   R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  S  S  R
    SNW                                       0                    0
    CIG   7  7  7  7  6  6  6  8  8  8  8  8  8  6  6  6  7  8  8  8  8
    VIS   7  7  7  7  7  7  7  7  7  7  7  7  7  7  7  6  7  7  7  7  7
    OBV   N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N
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
        self.units = Units(**static.UNITS)

    def _post_parse(self) -> None:
        if self.raw is None:
            return
        self.data = parse_mav(self.raw)
        self.units = Units(**static.UNITS)


class Mex(Forecast):
    '''
    The Mex class offers an object-oriented approach to managing MOS MEX data
    for a single station.

    Below is typical usage for fetching and pulling MAV data for KJFK.

    ```python
    >>> from avwx import Mex
    >>> kjfk = Mex("KJFK")
    >>> kjfk.station.name
    'John F Kennedy International Airport'
    >>> kjfk.update()
    True
    >>> kjfk.last_updated
    datetime.datetime(2020, 4, 20, 12, 7, 7, 393270, tzinfo=datetime.timezone.utc)
    >>> print(kjfk.raw)
    """
    KJFK   GFSX MOS GUIDANCE   4/20/2020  0000 UTC
    FHR  24| 36  48| 60  72| 84  96|108 120|132 144|156 168|180 192
    MON  20| TUE 21| WED 22| THU 23| FRI 24| SAT 25| SUN 26| MON 27 CLIMO
    X/N  57| 45  59| 37  56| 40  52| 49  58| 46  59| 48  59| 44  58 45 63
    TMP  50| 49  48| 41  49| 45  48| 52  51| 50  53| 51  52| 48  51
    DPT  31| 39  26| 17  17| 24  40| 46  43| 40  44| 43  40| 35  31
    CLD  OV| OV  OV| CL  CL| OV  OV| OV  OV| PC  OV| OV  OV| OV  OV
    WND  13| 14  26| 26  21| 16  13| 18  15| 16  12| 15  19| 19  11
    P12   9|  1  73|  7   0|  9  43| 73  63| 27  51| 64  37| 35  32 24 23
    P24    |     73|      7|     43|     77|     61|     73|     44    36
    Q12   0|  0   2|  0   0|  0   1|  5   3|  0   2|  5    |
    Q24    |      1|      0|      0|      5|      2|       |
    T12   1|  0  12|  1   0|  4   4|  8  11|  3   3| 14   7|  5   9
    T24    |  1    | 14    |  4    | 12    | 11    | 14    | 11
    PZP   0|  0   1|  0   2|  4   1|  0   0|  0   0|  0   0|  0   0
    PSN   0|  0   0| 37  25| 15   4|  0   0|  0   0|  2   0|  3   5
    PRS   0|  2   1| 32  28| 19   4|  0   1|  1   1|  1   1|  8   9
    TYP   R|  R   R| RS  RS|  R   R|  R   R|  R   R|  R   R|  R   R
    SNW    |      0|      0|      0|      0|      0|       |
    """
    >>> len(kjfk.data.forecast)
    15
    >>> kjfk.data.forecast[2].precip_chance_24
    Number(repr='73', value=73, spoken='seven three')
    ```

    The `parse` and `from_report` methods can parse a report string if you want
    to override the normal fetching process.
    '''

    report_type = "mex"
    _service_class = NoaaGfs  # type: ignore

    async def _post_update(self) -> None:
        if self.raw is None:
            return
        self.data = parse_mex(self.raw)
        self.units = Units(**static.UNITS)

    def _post_parse(self) -> None:
        if self.raw is None:
            return
        self.data = parse_mex(self.raw)
        self.units = Units(**static.UNITS)


_ThunderList = list[tuple[Number | None, Number | None] | None]


def _thunder(line: str, size: int = 3) -> _ThunderList:
    """Parse thunder line into Number tuples."""
    ret: _ThunderList = []
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


_precip_amount = _code(static.PRECIPITATION_AMOUNT)

_HANDLERS = {
    "X/N": ("temperature_minmax", _numbers),
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
