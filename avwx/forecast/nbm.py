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

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from avwx import structs
from avwx.forecast.base import (
    Forecast,
    _find_time_periods,
    _init_parse,
    _measurements,
    _parse_lines,
    _probabilities,
    _split_line,
    _trim_lines,
)
from avwx.service.files import NoaaNbm
from avwx.units import Measurement

DataT = type[structs.NbhData | structs.NbsData | structs.NbeData | structs.NbxData]
PeriodT = type[structs.NbhPeriod | structs.NbsPeriod | structs.NbePeriod | structs.NbxPeriod]

# Typed line parsers
_temperature = _measurements("degF")
_direction = _measurements("degree", postfix="0")
_wind_speed = _measurements("kt")
_probability = _probabilities()

_CEILING_SPECIAL: dict[str, Measurement | None] = {"888": None}  # unlimited ceiling
_WIND_SPECIAL: dict[str, Measurement | None] = {"NG": Measurement(0, "kt")}


def _ceiling(line: str, size: int = 3) -> list[Measurement | None]:
    """Parse ceiling line with special 888 (unlimited) value."""
    return _measurements("ft", postfix="00", special=_CEILING_SPECIAL)(line, size)


def _wind(line: str, size: int = 3) -> list[Measurement | None]:
    """Parse wind speed line with 'NG' (negligible = 0kt) special value."""
    return _measurements("kt", special=_WIND_SPECIAL)(line, size)


_HANDLERS: dict[str, tuple] = {
    "X/N": ("temperature_minmax", _temperature),
    "TMP": ("temperature", _temperature),
    "DPT": ("dewpoint", _temperature),
    "SKY": ("sky_cover", _probability),
    "WDR": ("wind_direction", _direction),
    "WSP": ("wind_speed", _wind),
    "GST": ("wind_gust", _wind),
    "DUR": ("precip_duration", _probability),
    "PZR": ("freezing_precip", _probability),
    "PSN": ("snow", _probability),
    "PPL": ("sleet", _probability),
    "PRA": ("rain", _probability),
    "SLV": ("snow_level", _measurements("ft", postfix="00")),
    "SOL": ("solar_radiation", _probability),
    "SWH": ("wave_height", _measurements("ft")),
}

_HOUR_HANDLERS: dict[str, tuple[str, Callable]] = {
    "P": ("precip_chance", _probability),
    "Q": ("precip_amount", _measurements("in", decimal=-2)),
    "T": ("thunderstorm", _probability),
    "S": ("snow_amount", _measurements("in", decimal=-1)),
    "I": ("icing_amount", _measurements("in", decimal=-2)),
}

_NBHS_HANDLERS: dict[str, tuple] = {
    "CIG": ("ceiling", _ceiling),
    "VIS": ("visibility", _measurements("sm", decimal=-1)),
    "LCB": ("cloud_base", _measurements("ft", postfix="00")),
    "MHT": ("mixing_height", _measurements("ft", postfix="00")),
    "TWD": ("transport_wind_direction", _direction),
    "TWS": ("transport_wind_speed", _wind_speed),
    "HID": ("haines", _probability),
}


def _parse_factory(
    data_class: DataT,
    period_class: PeriodT,
    handlers: dict[str, tuple],
    hours: int = 2,
    size: int = 3,
    prefix: int = 4,
) -> Callable:
    """Create handler function for static and computed keys."""

    all_handlers = {**_HANDLERS, **handlers}

    def handle(key: str) -> tuple:
        """Return response key(s) and value handler for a line key."""
        with suppress(KeyError):
            return all_handlers[key]
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
    _service_class = NoaaNbm  # type: ignore
    _parser: staticmethod

    async def _post_update(self) -> None:
        self.data = self._parser(self.raw)

    def _post_parse(self) -> None:
        self.data = self._parser(self.raw)


class Nbh(_Nbm):
    """Class to handle NBM NBH report data."""

    report_type = "nbh"
    _parser = staticmethod(parse_nbh)


class Nbs(_Nbm):
    """Class to handle NBM NBS report data."""

    report_type = "nbs"
    _parser = staticmethod(parse_nbs)


class Nbe(_Nbm):
    """Class to handle NBM NBE report data."""

    report_type = "nbe"
    _parser = staticmethod(parse_nbe)


class Nbx(_Nbm):
    """Class to handle NBM NBX report data."""

    report_type = "nbx"
    _parser = staticmethod(parse_nbx)
