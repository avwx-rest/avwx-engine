"""
Parsing for NOAA NBM forecasts
"""

# Reference: https://www.weather.gov/mdl/nbm_textcard_v32

# pylint: disable=too-many-arguments

# stdlib
from contextlib import suppress
from typing import Callable, Dict, List, Optional, Tuple

# module
from avwx import structs
from avwx.service.files import NOAA_NBM
from avwx.static.gfs import UNITS
from .base import (
    Forecast,
    _decimal_10,
    _decimal_100,
    _direction,
    _find_time_periods,
    _init_parse,
    _numbers,
    _number_100,
    _parse_lines,
    _split_line,
)

UNITS = {
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


def _ceiling(line: str, size: int = 3) -> List[Optional[structs.Number]]:
    """Parse line into Number objects handling ceiling special units"""
    return _numbers(line, size, postfix="00", special=_CEILING)


def _wind(line: str, size: int = 3) -> List[Optional[structs.Number]]:
    """Parse line into Number objects handling wind special units"""
    return _numbers(line, size, special=_WIND)


_HANDLERS: Dict[str, Tuple[str, Callable]] = {
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

_HOUR_HANDLERS: Dict[str, Tuple[str, Callable]] = {
    "P": ("precip_chance", _numbers),
    "Q": ("precip_amount", _decimal_100),
    "T": ("thunderstorm", _numbers),
    "S": ("snow_amount", _decimal_10),
    "I": ("icing_amount", _decimal_100),
}

_NBHS_HANDLERS: Dict[str, Tuple[str, Callable]] = {
    "CIG": ("ceiling", _ceiling),
    "VIS": ("visibility", _decimal_10),
    "LCB": ("cloud_base", _number_100),
    "MHT": ("mixing_height", _number_100),
    "TWD": ("transport_wind_direction", _direction),
    "TWS": ("transport_wind_speed", _numbers),
    "HID": ("haines", _numbers),
}


def _parse_factory(
    data_class,
    period_class,
    handlers: Dict[str, Tuple[str, Callable]],
    hours: int = 2,
    size: int = 3,
    prefix: int = 4,
) -> Callable:
    """Creates handler function for static and computed keys"""

    handlers = {**_HANDLERS, **handlers}

    def handle(key: str) -> Tuple:
        """Returns response key(s) and value handler for a line key"""
        with suppress(KeyError):
            return handlers[key]
        if not key[1:].isdigit():
            raise KeyError
        root, handler = _HOUR_HANDLERS[key[0]]
        return f"{root}_{key[1:].lstrip('0')}", handler

    def parse(report: str):
        """Parser for NBM reports"""
        if not report:
            return None
        data, lines = _init_parse(report)
        period_strings = _split_line(lines[hours], size, prefix)
        timestamp = data.time.dt if data.time else None
        periods = _find_time_periods(period_strings, timestamp)
        data_lines = lines[hours + 1 :]
        # Normalize line prefix length
        if prefix != 4:
            indexes = (4, prefix)
            start, end = min(indexes), max(indexes)
            data_lines = [l[:start] + l[end:] for l in data_lines]
        _parse_lines(periods, data_lines, handle, size)
        return data_class(
            raw=data.raw,
            sanitized=data.sanitized,
            station=data.station,
            time=data.time,
            remarks=data.remarks,
            forecast=[period_class(**p) for p in periods],
        )

    return parse


parse_nbh: Callable[[str], structs.NbhData] = _parse_factory(
    structs.NbhData, structs.NbhPeriod, _NBHS_HANDLERS, hours=1
)
parse_nbs: Callable[[str], structs.NbsData] = _parse_factory(
    structs.NbsData, structs.NbsPeriod, _NBHS_HANDLERS
)
parse_nbe: Callable[[str], structs.NbeData] = _parse_factory(
    structs.NbeData, structs.NbePeriod, {}, size=4, prefix=5
)


class _Nbm(Forecast):
    units = structs.NbmUnits(**UNITS)
    _service_class = NOAA_NBM  # type: ignore
    _parser: staticmethod

    async def _post_update(self):
        self.data = self._parser(self.raw)

    def _post_parse(self):
        self.data = self._parser(self.raw)


class Nbh(_Nbm):
    """Class to handle NBM NBH report data"""

    report_type = "nbh"
    _parser = staticmethod(parse_nbh)


class Nbs(_Nbm):
    """Class to handle NBM NBS report data"""

    report_type = "nbs"
    _parser = staticmethod(parse_nbs)


class Nbe(_Nbm):
    """Class to handle NBM NBE report data"""

    report_type = "nbe"
    _parser = staticmethod(parse_nbe)
