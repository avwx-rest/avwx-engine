"""
Parsing for NOAA NBM forecasts
"""

# Reference: https://www.weather.gov/mdl/nbm_textcard_v32

# stdlib
from typing import List

# module
from avwx.service.files import NOAA_NBM
from avwx.static.gfs import UNITS
from avwx.structs import NbsData, NbsPeriod, Number, NbsUnits
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


_CEILING_SPECIAL = {
    # 888 is code but processed as 88800 due to postfix
    "88800": (None, "unlimited")
}


def _ceiling(line: str, size: int = 3) -> List[Number]:
    """
    Parse line into Number objects handling ceiling special units
    """
    return _numbers(line, size, postfix="00", special=_CEILING_SPECIAL)


_HANDLERS = {
    "TMP": ("temperature", _numbers),
    "DPT": ("dewpoint", _numbers),
    "SKY": ("sky_cover", _numbers),
    "WDR": ("wind_direction", _direction),
    "WSP": ("wind_speed", _numbers),
    "GST": ("wind_gust", _numbers),
    "P06": ("precip_chance_6", _numbers),
    "P12": ("precip_chance_12", _numbers),
    "Q06": ("precip_amount_6", _decimal_100),
    "Q12": ("precip_amount_12", _decimal_100),
    "DUR": ("precip_duration", _numbers),
    "T03": ("thunder_storm_3", _numbers),
    "T12": ("thunder_storm_12", _numbers),
    "PZR": ("freezing_precip", _numbers),
    "PSN": ("snow", _numbers),
    "PPL": ("sleet", _numbers),
    "PRA": ("rain", _numbers),
    "S06": ("snow_amount_6", _decimal_10),
    "SLV": ("snow_level", _number_100),
    "I06": ("icing_amount_6", _decimal_100),
    "CIG": ("ceiling", _ceiling),
    "VIS": ("visibility", _decimal_10),
    "LCB": ("cloud_base", _number_100),
    "MHT": ("mixing_height", _number_100),
    "TWD": ("transport_wind_direction", _direction),
    "TWS": ("transport_wind_speed", _numbers),
    "HID": ("haines", _numbers),
    "SOL": ("solar_radiation", _numbers),
    "SWH": ("wave_height", _numbers),
}


def parse_nbs(report: str):
    """
    Parser for NBM NBS reports
    """
    if not report:
        return None
    data, lines = _init_parse(report)
    periods = _split_line(lines[2])
    periods = _find_time_periods(periods, data["time"].dt)
    _parse_lines(periods, lines[3:], _HANDLERS)
    data["forecast"] = [NbsPeriod(**p) for p in periods]
    return NbsData(**data)


class Nbs(Forecast):
    """
    Class to handle NBM NBS report data
    """

    report_type = "nbs"
    _service_class = NOAA_NBM

    def _post_update(self):
        self.data = parse_nbs(self.raw)
        self.units = NbsUnits(**UNITS)
