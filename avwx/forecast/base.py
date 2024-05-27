"""Forecast report shared resources."""

# stdlib
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

# module
from avwx.base import ManagedReport
from avwx.parsing import core
from avwx.structs import Code, Number, ReportData, Timestamp

if TYPE_CHECKING:
    from collections.abc import Callable

    from avwx.service import Service


def _trim_lines(lines: list[str], target: int) -> list[str]:
    """Trim all lines to match the trimmed length of the target line."""
    length = len(lines[target].strip())
    return [line[:length] for line in lines]


def _split_line(line: str, size: int = 3, prefix: int = 4, strip: str = " |") -> list[str]:
    """Evenly split a string while stripping elements."""
    line = line[prefix:]
    ret = []
    while len(line) >= size:
        ret.append(line[:size].strip(strip))
        line = line[size:]
    if line := line.strip(strip):
        ret.append(line)
    return ret


def _timestamp(line: str) -> Timestamp:
    """Return the report timestamp from the first line."""
    start = line.find("GUIDANCE") + 11
    text = line[start : start + 16].strip()
    timestamp = datetime.strptime(text, r"%m/%d/%Y  %H%M").replace(tzinfo=timezone.utc)
    return Timestamp(text, timestamp.replace(tzinfo=timezone.utc))


def _find_time_periods(line: list[str], timestamp: datetime | None) -> list[dict]:
    """Find and create the empty time periods."""
    periods: list[Timestamp | None] = []
    if timestamp is None:
        periods = [None] * len(line)
    else:
        previous = timestamp.hour
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


def _init_parse(report: str) -> tuple[ReportData, list[str]]:
    """Return the meta data and lines from a report string."""
    report = report.strip()
    lines = report.split("\n")
    struct = ReportData(
        raw=report,
        sanitized=report,
        station=report[:4],
        time=_timestamp(lines[0]),
        remarks=None,
    )
    return struct, lines


def _numbers(
    line: str,
    size: int = 3,
    prefix: str = "",
    postfix: str = "",
    *,
    decimal: int | None = None,
    literal: bool = False,
    special: dict | None = None,
) -> list[Number | None]:
    """Parse line into Number objects.

    Prefix, postfix, and decimal location are applied to value, not repr.

    Decimal is applied after prefix and postfix.
    """
    ret = []
    for item in _split_line(line, size=size):
        value = None
        if item:
            value = prefix + item + postfix
            if decimal is not None:
                if abs(decimal) > len(value):
                    value = value.zfill(abs(decimal))
                value = f"{value[:decimal]}.{value[decimal:]}"
        ret.append(core.make_number(value, repr=item, literal=literal, special=special))
    return ret


def _decimal_10(line: str, size: int = 3) -> list[Number | None]:
    """Parse line into Number objects with 10ths decimal location."""
    return _numbers(line, size, decimal=-1)


def _decimal_100(line: str, size: int = 3) -> list[Number | None]:
    """Parse line into Number objects with 100ths decimal location."""
    return _numbers(line, size, decimal=-2)


def _number_10(line: str, size: int = 3) -> list[Number | None]:
    """Parse line into Number objects in tens."""
    return _numbers(line, size, postfix="0")


def _number_100(line: str, size: int = 3) -> list[Number | None]:
    """Parse line into Number objects in hundreds."""
    return _numbers(line, size, postfix="00")


def _direction(line: str, size: int = 3) -> list[Number | None]:
    """Parse line into Number objects in hundreds."""
    return _numbers(line, size, postfix="0", literal=True)


def _code(mapping: dict) -> Callable:
    """Generate a conditional code mapping function."""

    def func(line: str, size: int = 3) -> list[Code | str | None]:
        ret: list[Code | str | None] = []
        for key in _split_line(line, size=size):
            try:
                ret.append(Code(key, mapping[key]))
            except KeyError:
                ret.append(key or None)
        return ret

    return func


def _parse_lines(
    periods: list[dict],
    lines: list[str],
    handlers: dict | Callable,
    size: int = 3,
) -> None:
    """Add data to time periods by parsing each line (element type).

    Adds data in place.
    """
    for line in lines:
        try:
            key = line[:3]
            *keys, handler = handlers[key] if isinstance(handlers, dict) else handlers(key)
        except (IndexError, KeyError):
            continue
        values = handler(line, size=size)
        values += [None] * (len(periods) - len(values))
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


class Forecast(ManagedReport):
    """Forecast base class."""

    report_type: str
    _service_class: Service

    def __init__(self, code: str):
        super().__init__(code)
        self.service: Service = self._service_class(self.report_type)  # type: ignore
