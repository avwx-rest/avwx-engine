"""
# NBH

The NBH report is a 25-hour forecast based on the
[National Blend of Models](https://vlab.noaa.gov/web/mdl/nbm) and is only valid
for ICAO stations in the United States and Puerto Rico, and US Virgin Islands.
Reports are in 1-hour increments and are published near the top of every hour.

# NBS

The NBS report is a
short-range forecast (6-72 hours) based on the
[National Blend of Models](https://vlab.noaa.gov/web/mdl/nbm) and is only valid
for ICAO stations in the United States and Puerto Rico, and US Virgin Islands.
Reports are in 3-hour increments and published near the top of every hour.

# NBE

The NBE report is an extended-range forecast (24-192 hours) based on the
[National Blend of Models](https://vlab.noaa.gov/web/mdl/nbm) and is only valid
for ICAO stations in the United States and Puerto Rico, and US Virgin Islands.
Reports are in 12-hour increments and published near the top of every hour.

# NBX

The NBX report is a continuation of the NBE forecast (204-264 hours) based on the
[National Blend of Models](https://vlab.noaa.gov/web/mdl/nbm) and is only valid
for ICAO stations in the United States and Puerto Rico, and US Virgin Islands.
Reports are in 12-hour increments and published near the top of every hour.
"""

# Reference: https://www.weather.gov/mdl/nbm_textcard_v32

# stdlib
from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

try:
    from typing import TypeAlias
except ImportError:
    from typing import TypeAlias

# module
from avwx import structs
from avwx.forecast.base import (
    Forecast,
    _decimal_10,
    _decimal_100,
    _direction,
    _find_time_periods,
    _init_parse,
    _number_100,
    _numbers,
    _parse_lines,
    _split_line,
    _trim_lines,
)
from avwx.service.files import NoaaNbm
from avwx.static.gfs import UNITS

DataT: TypeAlias = type[structs.NbhData | structs.NbsData | structs.NbeData | structs.NbxData]
PeriodT: TypeAlias = type[structs.NbhPeriod | structs.NbsPeriod | structs.NbePeriod | structs.NbxPeriod]

_UNITS = {
    **UNITS,
    "accumulation": "in",
    "duration": "hour",
    "solar_radiation": "W/m2",
    "wave_height": "ft",
}


_CEILING = {
    # 888 is code but processed as 88800 due to postfix
    "88800": (None, "unlimited")
}
_WIND = {"NG": (0, "zero")}


def _ceiling(line: str, size: int = 3) -> list[structs.Number | None]:
    """Parse line into Number objects handling ceiling special units."""
    return _numbers(line, size, postfix="00", special=_CEILING)


def _wind(line: str, size: int = 3) -> list[structs.Number | None]:
    """Parse line into Number objects handling wind special units."""
    return _numbers(line, size, special=_WIND)


_HANDLERS: dict[str, tuple[str, Callable]] = {
    "X/N": ("temperature_minmax", _numbers),
    "TMP": ("temperature", _numbers),
    "DPT": ("dewpoint", _numbers),
    "SKY": ("sky_cover", _numbers),
    "WDR": ("wind_direction", _direction),
    "WSP": ("wind_speed", _wind),
    "GST": ("wind_gust", _wind),
    "DUR": ("precip_duration", _numbers),
    "PZR": ("freezing_precip", _numbers),
    "PSN": ("snow", _numbers),
    "PPL": ("sleet", _numbers),
    "PRA": ("rain", _numbers),
    "SLV": ("snow_level", _number_100),
    "SOL": ("solar_radiation", _numbers),
    "SWH": ("wave_height", _numbers),
}

_HOUR_HANDLERS: dict[str, tuple[str, Callable]] = {
    "P": ("precip_chance", _numbers),
    "Q": ("precip_amount", _decimal_100),
    "T": ("thunderstorm", _numbers),
    "S": ("snow_amount", _decimal_10),
    "I": ("icing_amount", _decimal_100),
}

_NBHS_HANDLERS: dict[str, tuple[str, Callable]] = {
    "CIG": ("ceiling", _ceiling),
    "VIS": ("visibility", _decimal_10),
    "LCB": ("cloud_base", _number_100),
    "MHT": ("mixing_height", _number_100),
    "TWD": ("transport_wind_direction", _direction),
    "TWS": ("transport_wind_speed", _numbers),
    "HID": ("haines", _numbers),
}


def _parse_factory(
    data_class: DataT,
    period_class: PeriodT,
    handlers: dict[str, tuple[str, Callable]],
    hours: int = 2,
    size: int = 3,
    prefix: int = 4,
) -> Callable:
    """Create handler function for static and computed keys."""

    handlers = {**_HANDLERS, **handlers}

    def handle(key: str) -> tuple[str, Callable]:
        """Return response key(s) and value handler for a line key."""
        with suppress(KeyError):
            return handlers[key]
        if not key[1:].isdigit():
            raise KeyError
        root, handler = _HOUR_HANDLERS[key[0]]
        return f"{root}_{key[1:].lstrip('0')}", handler

    def parse(report: str) -> structs.ReportData | None:
        """Parser for NBM reports."""
        if not report:
            return None
        data, lines = _init_parse(report)
        lines = _trim_lines(lines, 2)
        period_strings = _split_line(lines[hours], size, prefix)
        timestamp = data.time.dt if data.time else None
        periods = _find_time_periods(period_strings, timestamp)
        data_lines = lines[hours + 1 :]
        # Normalize line prefix length
        if prefix != 4:
            indexes = (4, prefix)
            start, end = min(indexes), max(indexes)
            data_lines = [line[:start] + line[end:] for line in data_lines]
        _parse_lines(periods, data_lines, handle, size)
        return data_class(
            raw=data.raw,
            sanitized=data.sanitized,
            station=data.station,
            time=data.time,
            remarks=data.remarks,
            forecast=[period_class(**p) for p in periods],  # type: ignore
        )

    return parse


parse_nbh: Callable[[str], structs.NbhData] = _parse_factory(
    structs.NbhData,
    structs.NbhPeriod,
    _NBHS_HANDLERS,
    hours=1,
)
parse_nbs: Callable[[str], structs.NbsData] = _parse_factory(
    structs.NbsData,
    structs.NbsPeriod,
    _NBHS_HANDLERS,
)
parse_nbe: Callable[[str], structs.NbeData] = _parse_factory(
    structs.NbeData,
    structs.NbePeriod,
    {},
    size=4,
    prefix=5,
)
parse_nbx: Callable[[str], structs.NbxData] = _parse_factory(
    structs.NbxData,
    structs.NbxPeriod,
    {},
    size=4,
    prefix=4,
)


class _Nbm(Forecast):
    units = structs.NbmUnits(**_UNITS)
    _service_class = NoaaNbm  # type: ignore
    _parser: staticmethod

    async def _post_update(self) -> None:
        self.data = self._parser(self.raw)

    def _post_parse(self) -> None:
        self.data = self._parser(self.raw)


class Nbh(_Nbm):
    '''
    Class to handle NBM NBH report data

    Below is typical usage for fetching and pulling NBH data for KJFK.

    ```python
    >>> from avwx import Nbh
    >>> kjfk = Nbh("KJFK")
    >>> kjfk.station.name
    'John F Kennedy International Airport'
    >>> kjfk.update()
    True
    >>> kjfk.last_updated
    datetime.datetime(2020, 7, 26, 20, 37, 42, 352220, tzinfo=datetime.timezone.utc)
    >>> print(kjfk.raw)
    """
    KJFK   NBM V3.2 NBH GUIDANCE    7/26/2020  1900 UTC
    UTC  20 21 22 23 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20
    TMP  90 89 88 87 85 84 82 81 81 80 79 78 77 76 76 78 81 84 87 89 90 91 92 92 93
    DPT  69 68 66 66 65 65 65 66 66 66 66 67 67 66 67 67 67 67 67 68 67 67 67 67 67
    SKY   9 14 41 58 61 71 66 55 39 37 39 43 40 38 29 21 19 26 24 27 22 14 22 26 26
    WDR  22 22 23 24 25 25 25 25 25 25 25 26 26 26 26 26 26 26 25 24 24 23 23 22 23
    WSP  10  9  9  8  7  6  5  5  5  6  5  5  5  5  4  4  5  5  7  8  8  9 10 10 10
    GST  17 16 16 15 14 12 11 12 12 12 12 11 11  9  9  9  9 10 11 13 14 15 16 17 17
    P01   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    P06                                 0                 0                 0
    Q01   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    DUR                                                   0
    T01   1  1  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    PZR   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    PSN   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    PPL   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    PRA 100100100100100100100100100100100100100100100100100100100100100100100100100
    S01   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    SLV  99101102103105105105106105104106104104104104103102100 99 98 98 99100101102
    I01   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    CIG 888888888360360350340888888888888888888888888888888888888888888888888888888
    VIS 110120120140140130120120120120110110110110110120130140150150150150150150150
    LCB  80 60999999999999999999999999999999999999999999999999999999999999999999999
    MHT  26 26 20 19  8  7  6  4  4  5  5  5  6  4  5  6  6 11 20 27 37 39 43 39 31
    TWD  24 26 26 27 26 26 24 23 24 26 26 26 27 27 28 27 27 27 27 26 26 26 25 25 24
    TWS  15 14 14 13 11 11 11 10 11 11 10 11 10  8  8  7  8  9 12 13 14 15 17 17 16
    HID                                 6                 5                 6
    SOL 710500430250110  0 30  0  0  0  0  0  0  0 30160330500650760830870870850720
    """
    >>> len(kjfk.data.forecast)
    25
    >>> kjfk.data.forecast[0].snow_level
    Number(repr='99', value=9900, spoken='nine nine hundred')
    >>> print(kjfk.data.forecast[0].solar_radiation.value, kjfk.units.solar_radiation)
    710 W/m2
    ```

    The `parse` and `from_report` methods can parse a report string if you want
    to override the normal fetching process.
    '''

    report_type = "nbh"
    _parser = staticmethod(parse_nbh)


class Nbs(_Nbm):
    '''
    Class to handle NBM NBS report data

    Below is typical usage for fetching and pulling Nbs data for KJFK.

    ```python
    >>> from avwx import Nbs
    >>> kjfk = Nbs("KJFK")
    >>> kjfk.station.name
    'John F Kennedy International Airport'
    >>> kjfk.update()
    True
    >>> kjfk.last_updated
    datetime.datetime(2020, 7, 28, 1, 3, 46, 447635, tzinfo=datetime.timezone.utc)
    >>> print(kjfk.raw)
    """
    KJFK    NBM V3.2 NBS GUIDANCE    7/27/2020  2300 UTC
    DT /JULY 28               /JULY 29                /JULY 30
    UTC  03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21
    FHR  04 07 10 13 16 19 22 25 28 31 34 37 40 43 46 49 52 55 58 61 64 67 70
    N/X           79          93          76          91          76
    TMP  85 82 80 83 89 91 89 84 81 79 77 80 85 89 87 83 81 79 77 80 86 88 86
    DPT  70 70 71 72 72 72 73 72 72 71 69 69 68 67 68 69 68 67 68 69 68 69 70
    SKY   4 10  2  4 12 23 38 61 53 62 51 26 19  9 21 24 25 34 32 45 57 70 79
    WDR  23 24 23 24 24 22 23 27 28 28 34 35 21 20 19 22 23 25 26 26 23 20 20
    WSP   8  8  5  6  8  9  7  5  3  2  1  2  3  6  9  7  4  4  3  3  4  7  8
    GST  16 15 11 11 13 15 15 11  9  5  4  4  6 12 15 13 11 11  8  6  7 13 15
    P06      0     1    15    48    17    11     8     8     1     0     5
    P12            1          48          17           8           1
    Q06      0     0     0    11     0     0     0     0     0     0     0
    Q12            0          11           0           0           0
    DUR            0           2           0           0           0
    T03   2  3  1  1  2 10 27 30 21 13  8  5  1  0  2  3  4  3  2  3  1  3  7
    T12            4          48          33           6           8
    PZR   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    PSN   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    PPL   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    PRA 100100100100100100100100100100100100100100100100100100100100100100100
    S06      0     0     0     0     0     0     0     0     0     0     0
    SLV 108112113133135139141139137134124113102 99107115114118118119118118118
    I06      0     0     0     0     0     0     0     0     0     0     0
    CIG 888888888888888888888170888150888888888888888888888888888888888888888
    VIS 120120110120130130130110110110110130110110110120120120110110110110110
    LCB  60 70999 90 90999 50 60 60 60 60 60 22999999200230 70 80 60 60150 60
    MHT   7  6  5 13 30 46 19 15  7  7 10 16 40 35 13  4  4  4  9 18 31 27 13
    TWD  23 24 23 27 25 24 27 27 28 21 34  6 26 23 20 19 26 23 27 29 24 20 18
    TWS  17 16  9 11 13 16 12  9  5  5  4  3  4  8 11 10  8 10 10  6  6  9 13
    HID      4     4     4     4     3     4     4     5     5     3     4
    SOL   0  0  0320700760360100  0  0  0320720830620190  0  0  0230480570540
    """
    >>> len(kjfk.data.forecast)
    23
    >>> kjfk.data.forecast[0].ceiling
    Number(repr='888', value=None, spoken='unlimited')
    >>> print(kjfk.data.forecast[7].precip_amount_12.value, kjfk.units.accumulation)
    0.11 in
    ```

    The `parse` and `from_report` methods can parse a report string if you want
    to override the normal fetching process.
    '''

    report_type = "nbs"
    _parser = staticmethod(parse_nbs)


class Nbe(_Nbm):
    '''
    Class to handle NBM NBE report data

    Below is typical usage for fetching and pulling NBE data for KJFK.

    ```python
    >>> from avwx import Nbe
    >>> kjfk = Nbe("KJFK")
    >>> kjfk.station.name
    'John F Kennedy International Airport'
    >>> kjfk.update()
    True
    >>> kjfk.last_updated
    datetime.datetime(2020, 7, 28, 1, 23, 4, 909939, tzinfo=datetime.timezone.utc)
    >>> print(kjfk.raw)
    """
    KJFK    NBM V3.2 NBE GUIDANCE    7/28/2020  0000 UTC
           WED 29| THU 30| FRI 31| SAT 01| SUN 02| MON 03| TUE 04|WED CLIMO
    UTC    00  12| 00  12| 00  12| 00  12| 00  12| 00  12| 00  12| 00
    FHR    24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192
    X/N    93  76| 91  76| 90  74| 86  72| 87  73| 85  74| 86  72| 84 68 83
    TMP    84  80| 83  80| 81  78| 78  76| 78  78| 78  78| 78  76| 76
    DPT    72  69| 68  69| 71  68| 67  66| 68  69| 70  71| 70  68| 69
    SKY    61  21| 23  47| 80  73| 47  31| 30  54| 68  65| 66  59| 32
    WDR    25  35| 20  26| 20   2| 16   1| 16   7| 16  24| 22  34| 18
    WSP     5   2|  6   3|  5   4|  3   5|  7   4|  6   4|  5   4|  4
    GST    11   4| 13   6| 13  10|  9  10| 13   7| 13   9| 16   9| 12
    P12    48  23|  8   1| 23  28| 28  16| 18  17| 30  41| 46  31| 32 19 18
    Q12    10   0|  0   0|  0   0|  0   0|  0   0|  0  64| 77  81| 83
    Q24          |  0    |  0    |  0    |  0    |  0    |141    |164
    DUR     2   1|  0   0|  0   0|  0   0|  0   0|  2  12| 12  12| 12
    T12    46  32|  6   8| 21  22| 17   5|  6   5| 25  23| 19  18| 18
    PZR     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
    PSN     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
    PPL     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
    PRA   100 100|100 100|100 100|100 100|100 100|100 100|100 100|100
    S12     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
    SLV   138 114|111 119|119 121|113 101|108 117|134 132|124 123|121
    I12     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
    S24          |  0    |  0    |  0    |  0    |  0    |  0    |  0
    SOL   100 320|190 230|270 250|360 290|370  30|190 260|250 230|450
    """
    >>> len(kjfk.data.forecast)
    25
    >>> kjfk.data.forecast[0].wind_direction
    Number(repr='25', value=250, spoken='two five zero')
    >>> print(kjfk.data.forecast[1].precip_duration.value, kjfk.units.duration)
    1 hour
    ```

    The `parse` and `from_report` methods can parse a report string if you want
    to override the normal fetching process.
    '''

    report_type = "nbe"
    _parser = staticmethod(parse_nbe)


class Nbx(_Nbm):
    '''
    Class to handle NBM NBX report data

    Below is typical usage for fetching and pulling NBX data for KJFK.

    ```python
    >>> from avwx import Nbx
    >>> kjfk = Nbx("KJFK")
    >>> kjfk.station.name
    'John F Kennedy International Airport'
    >>> kjfk.update()
    True
    >>> kjfk.last_updated
    datetime.datetime(2023, 10, 17, 4, 0, 0, 909939, tzinfo=datetime.timezone.utc)
    >>> print(kjfk.raw)
    """
    086092  NBM V4.1 NBX GUIDANCE   10/17/2023  0300 UTC
    WED 25 |THU 26 |FRI 27 |SAT 28
    UTC 12 |00  12 |00  12 |00
    FHR 201|213 225|237 249|261
    TXN  76| 81  75| 81  75| 81
    XND   1|  1   1|  2   1|  0
    TMP  77| 77  77| 78  76| 78
    TSD   1|  2   1|  1   2|  1
    DPT  67| 67  69| 68  70| 69
    DSD   1|  2   1|  1   2|  1
    SKY  34| 46  27| 50  26| 37
    SSD  12| 22  13| 22  12|  7
    WDR   7|  7   7|  6   5|  5
    WSP  15| 16  15| 17  15| 17
    WSD   3|  4   3|  3   4|  3
    GST  22| 24  22| 25  22| 25
    GSD   2|  2   2|  1   1|  1
    P12   8|  8   9|  7   7|  7
    Q12   0|  0   0|  3   0|  0
    Q24   0|      0|      3|
    DUR   0|  0   0|  0   0|  0
    PZR   0|  0   0|  0   0|  0
    PSN   0|  0   0|  0   0|  0
    PPL   0|  0   0|  0   0|  0
    PRA   7| 16  14| 10   6| 11
    S12   0|  0   0|  0   0|  0
    I12   0|  0   0|  0   0|  0
    SOL   1| 35   1| 15   1| 38
    """
    >>> len(kjfk.data.forecast)
    25
    >>> kjfk.data.forecast[0].wind_speed
    Number(repr='15', value=150, spoken='one five zero')
    >>> print(kjfk.data.forecast[1].solar_radiation.value, kjfk.units.solar_radiation)
    35 W/m2
    ```

    The `parse` and `from_report` methods can parse a report string if you want
    to override the normal fetching process.
    '''

    report_type = "nbx"
    _parser = staticmethod(parse_nbx)
