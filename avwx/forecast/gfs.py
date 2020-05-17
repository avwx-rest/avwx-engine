"""
Parsing for NOAA GFS forecasts
"""

# stdlib
from datetime import datetime, timedelta, timezone
from typing import Callable

# module
import avwx.static.gfs as static
from avwx.forecast.base import Forecast
from avwx.parsing import core
from avwx.structs import Code, MavData, MavPeriod, MexData, MexPeriod, Timestamp, Units


def _split_line(line: str, size: int = 3, prefix: int = 4, strip: str = " |") -> [str]:
    """
    Evenly split a string while stripping elements
    """
    line = line[prefix:]
    ret = []
    while len(line) >= size:
        ret.append(line[:size].strip(strip))
        line = line[size:]
    line = line.strip(strip)
    if line:
        ret.append(line)
    return ret


def _timestamp(line: str) -> Timestamp:
    """
    Returns the report timestamp from the first line
    """
    text = line[26:43].strip()
    timestamp = datetime.strptime(text, r"%m/%d/%Y  %H%M")
    return Timestamp(text, timestamp.replace(tzinfo=timezone.utc))


def _find_time_periods(line: [str], timestamp: datetime) -> [dict]:
    """
    Find and create the empty time periods
    """
    previous = timestamp.hour
    periods = []
    for hourstr in line:
        if not hourstr:
            continue
        hour = int(hourstr)
        previous, difference = hour, hour - previous
        if difference < 0:
            difference += 24
        timestamp += timedelta(hours=difference)
        periods.append(Timestamp(hourstr, timestamp))
    return [{"time": time} for time in periods]


def _init_parse(report: str) -> (dict, [str]):
    """
    Returns the meta data and lines from a report string
    """
    report = report.strip()
    lines = report.split("\n")
    data = {
        "raw": report,
        "station": report[:4],
        "time": _timestamp(lines[0]),
        "remarks": None,
    }
    return data, lines


def _numbers(line: str, size: int = 3, postfix: str = "") -> ["Number"]:
    """
    Parse line into Number objects
    """
    return [
        core.make_number(item + postfix if item else item, repr=item)
        for item in _split_line(line, size=size)
    ]


def _wind_direction(line: str, size: int = 3) -> ["Number"]:
    """
    Parse wind direction line into Number objects
    """
    return _numbers(line, size, postfix="0")


def _thunder(line: str, size: int = 3) -> list:
    """
    Parse thunder line into Number tuples
    """
    ret = []
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


def _code(mapping: dict) -> Callable:
    """
    Generates a conditional code mapping function
    """

    def func(line: str, size: int = 3) -> list:
        ret = []
        for key in _split_line(line, size=size):
            try:
                value = Code(key, mapping[key])
            except KeyError:
                value = key or None
            ret.append(value)
        return ret

    return func


# pylint: disable=invalid-name
_precip_amount = _code(static.PRECIPITATION_AMOUNT)


_HANDLERS = {
    "TMP": ("temperature", _numbers),
    "DPT": ("dewpoint", _numbers),
    "CLD": ("cloud", _code(static.CLOUD)),
    "WDR": ("wind_direction", _wind_direction),
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
    "T06": ("thunder_storm_6", "severe_storm_6", _thunder),
    "T12": ("thunder_storm_12", "severe_storm_12", _thunder),
    "POZ": ("freezing_precip", _numbers),
    "POS": ("snow", _numbers),
    "CIG": ("ceiling", _code(static.CEILING_HEIGHT)),
    "VIS": ("visibility", _code(static.VISIBILITY)),
    "OBV": ("vis_obstruction", _code(static.VISIBILITY_OBSTRUCTION)),
}

_MEX_HANDLERS = {
    "T12": ("thunder_storm_12", _numbers),
    "T24": ("thunder_storm_24", _numbers),
    "PZP": ("freezing_precip", _numbers),
    "PRS": ("rain_snow_mix", _numbers),
    "PSN": ("snow", _numbers),
    "SNW": ("snow_amount_24", _code(static.SNOWFALL_AMOUNT)),
}


def _parse_lines(periods: [dict], lines: [str], size: int = 3, handlers: dict = None):
    """
    Add data to time periods by parsing each line (element type)

    Adds data in place
    """
    if handlers is not None:
        handlers = {**_HANDLERS, **handlers}
    else:
        handlers = _HANDLERS
    for line in lines:
        try:
            *keys, handler = handlers[line[:3]]
        except (IndexError, KeyError):
            continue
        values = handler(line, size=size)
        values += [None] * (len(periods) - len(values))
        # pylint: disable=consider-using-enumerate
        for i in range(len(periods)):
            value = values[i]
            if not value:
                continue
            if isinstance(value, tuple):
                for j, key in enumerate(keys):
                    if value[j]:
                        periods[i][key] = value[j]
            else:
                periods[i][keys[0]] = value


def parse_mav(report: str) -> MavData:
    """
    Parser for GFS MAV reports
    """
    if not report:
        return None
    data, lines = _init_parse(report)
    periods = _split_line(lines[2])
    periods = _find_time_periods(periods, data["time"].dt)
    _parse_lines(periods, lines[3:], handlers=_MAV_HANDLERS)
    data["forecast"] = [MavPeriod(**p) for p in periods]
    return MavData(**data)


def parse_mex(report: str) -> MexData:
    """
    Parser for GFS MEX reports
    """
    if not report:
        return None
    data, lines = _init_parse(report)
    # Remove CLIMO data for now
    if len(lines) >= 3:
        climo_index = lines[2].find(" CLIMO")
        if climo_index >= 0:
            lines = [l[:climo_index] for l in lines]
    periods = _split_line(lines[1], size=4, prefix=4)
    periods = _find_time_periods(periods, data["time"].dt)
    _parse_lines(periods, lines[3:], size=4, handlers=_MEX_HANDLERS)
    data["forecast"] = [MexPeriod(**p) for p in periods]
    return MexData(**data)


class Mav(Forecast):
    """
    Class to handle GFS MAV report data
    """

    report_type = "mav"

    def _post_update(self):
        self.data = parse_mav(self.raw)
        self.units = Units(**static.UNITS)


class Mex(Forecast):
    """
    Class to handle GFS MAV report data
    """

    report_type = "mex"

    def _post_update(self):
        self.data = parse_mex(self.raw)
        self.units = Units(**static.UNITS)
