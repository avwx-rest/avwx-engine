"""
"""

# stdlib
from datetime import datetime, timedelta, timezone

# module
from avwx.forecast.base import Forecast
from avwx.parsing import core
from avwx.structs import MavData, MavPeriod, MexData, MexPeriod, Timestamp


def _split_line(line: str, size: int = 3, prefix: int = 4, strip: str = " |") -> [str]:
    """
    """
    line = line[prefix:]
    ret = []
    while len(line) >= size:
        ret.append(line[:size].strip(strip))
        line = line[size:]
    return ret


def _timestamp(line: str) -> Timestamp:
    """
    Returns the report timestamp from the first line
    """
    text = line[27:42]
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
    """
    return [core.make_number(item + postfix) for item in _split_line(line, size=size)]


def _wind_direction(line: str, size: int = 3) -> ["Number"]:
    """
    """
    return _numbers(line, size, postfix="0")


def _thunder(line: str, size: int = 3):
    """
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


_HANDLERS = {
    "TMP": ("temperature", _numbers),
    "DPT": ("dewpoint", _numbers),
    "CLD": ("cloud", _split_line),
    "WDR": ("wind_direction", _wind_direction),
    "WSP": ("wind_speed", _numbers),
    "P06": ("precip_chance_6", _numbers),
    "P12": ("precip_chance_12", _numbers),
    "P24": ("precip_chance_24", _numbers),
    "Q06": ("precip_amount_6", _numbers),
    "Q12": ("precip_amount_12", _numbers),
    "Q24": ("precip_amount_24", _numbers),
    "POZ": ("freezing_precip", _numbers),
    "POS": ("snow", _numbers),
    "TYP": ("precip_type", _split_line),
    "CIG": ("ceiling", _numbers),
    "VIS": ("visibility", _numbers),
    "OBV": ("vis_obstruction", _split_line),
}


# Secondary dicts for conflicting handlers
_SHORT_HANDLERS = {
    "T06": ("thunder_storm_6", "severe_storm_6", _thunder),
    "T12": ("thunder_storm_12", "severe_storm_12", _thunder),
}

_LONG_HANDLERS = {
    "T12": ("thunder_storm_12", _numbers),
    "T24": ("thunder_storm_24", _numbers),
}


def _parse_lines(periods: [dict], lines: [str], size: int = 3, handlers: dict = None):
    """
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


def parse_short(report: str) -> MavData:
    """
    """
    if not report:
        return
    data, lines = _init_parse(report)
    periods = _split_line(lines[2])
    periods = _find_time_periods(periods, data["time"].dt)
    _parse_lines(periods, lines[3:], handlers=_SHORT_HANDLERS)
    data["forecast"] = [MavPeriod(**p) for p in periods]
    return MavData(**data)


def parse_long(report: str):
    """
    """
    if not report:
        return
    data, lines = _init_parse(report)
    periods = _split_line(lines[1], size=4, prefix=4)
    periods = _find_time_periods(periods, data["time"].dt)
    _parse_lines(periods, lines[3:], size=4, handlers=_LONG_HANDLERS)
    data["forecast"] = periods
    return data


class Mav(Forecast):
    """
    """

    report_type = "mav"

    def _post_update(self):
        self.data = parse_short(self.raw)


class Mex(Forecast):
    """
    """

    report_type = "mex"

    def _post_update(self):
        self.data = parse_long(self.raw)
