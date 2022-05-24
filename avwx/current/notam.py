"""
NOTAM report parsing
"""

# pylint: disable=invalid-name

# stdlib
import re
from datetime import datetime, timezone
from typing import List, Optional

# library
from dateutil.tz import gettz

# module
from avwx.current.base import Reports
from avwx.parsing import core
from avwx.service import FAA_NOTAM
from avwx.static.core import IN_UNITS
from avwx.static.notam import (
    CONDITION,
    PURPOSE,
    REPORT_TYPE,
    SCOPE,
    SUBJECT,
    TRAFFIC_TYPE,
)
from avwx.structs import Code, Coord, NotamData, Qualifiers, Timestamp, Tuple, Units

# https://www.navcanada.ca/en/briefing-on-the-transition-to-icao-notam-format.pdf
# https://www.faa.gov/air_traffic/flight_info/aeronav/notams/media/2021-09-07_ICAO_NOTAM_101_Presentation_for_Airport_Operators.pdf


KEY_PATTERN = re.compile(r"[A-GQ]\) ")


def _rear_coord(value: str) -> Coord:
    """Convert coord strings with direction characters at the end: 5126N00036W"""
    lat = float(f"{value[:2]}.{value[2:4]}")
    if value[4] == "S":
        lat *= -1
    lon = float(f"{value[5:8]}.{value[8:10]}")
    if value[10] == "W":
        lon *= -1
    return Coord(lat, lon, value)


def _header(value: str) -> Tuple[str, Optional[Code], Optional[str]]:
    """Parse pre-tag headers"""
    header = value.strip().split()
    replaces = None
    if len(header) == 3:
        number, type_text, replaces = header
    else:
        number, type_text = header
    report_type = Code.from_dict(type_text, REPORT_TYPE)
    return number, report_type, replaces


def _qualifiers(value: str, units: Units) -> Qualifiers:
    """Parse the NOTAM Q) line into components"""
    data = [i.strip() for i in value.strip().split("/")]
    # Some reports exclude the traffic element
    if len(data) == 7:
        fir, q_code, purpose, scope, lower, upper, location = data
        traffic = None
    else:
        fir, q_code, traffic, purpose, scope, lower, upper, location = data
    subject, condition = None, None
    if q_code.startswith("Q"):
        subject = Code.from_dict(q_code[1:3], SUBJECT)
        condition_code = q_code[3:]
        if condition_code.startswith("XX"):
            condition = Code("XX", (condition_code[2:] or "Unknown").strip())
        else:
            condition = Code.from_dict(condition_code, CONDITION)
    return Qualifiers(
        repr=value,
        fir=fir,
        subject=subject,
        condition=condition,
        traffic=Code.from_dict(traffic, TRAFFIC_TYPE),
        purpose=[i for i in (Code.from_dict(c, PURPOSE) for c in purpose) if i],
        scope=[i for i in (Code.from_dict(c, SCOPE) for c in scope) if i],
        lower=core.make_altitude(lower, units)[0],
        upper=core.make_altitude(upper, units)[0],
        coord=_rear_coord(location[:-3]),
        radius=core.make_number(location[-3:]),
    )


def _tz_offset_for(name: Optional[str]) -> Optional[timezone]:
    """Generates a timezone from tz string name"""
    if not name:
        return None
    if tz := gettz(name):
        if offset := tz.utcoffset(datetime.utcnow()):
            return timezone(offset)
    return None


def make_year_timestamp(
    value: str, repr: str, tzname: str = None  # pylint: disable=redefined-builtin
) -> Optional[Timestamp]:
    """Convert NOTAM timestamp which includes year and month"""
    value = value.strip()
    if not value:
        return None
    if value == "PERM":
        return Timestamp(repr, datetime(2100, 1, 1, tzinfo=timezone.utc))
    tz = _tz_offset_for(tzname) or timezone.utc
    raw = datetime.strptime(value, r"%y%m%d%H%M")
    date = datetime(raw.year, raw.month, raw.day, raw.hour, raw.minute, tzinfo=tz)
    return Timestamp(repr, date)


def parse_linked_times(
    start: str, end: str
) -> Tuple[Optional[Timestamp], Optional[Timestamp]]:
    """Parse start and end times sharing any found timezone"""
    start, end = start.strip(), end.strip()
    start_raw, end_raw, tzname = start, end, None
    if len(start) > 10:
        start, tzname = start[:-3], start[-3:]
    if len(end) > 10:
        end, tzname = end[:-3], end[-3:]
    return make_year_timestamp(start, start_raw, tzname), make_year_timestamp(
        end, end_raw, tzname
    )


def parse(report: str, issued: Timestamp = None) -> Tuple[NotamData, Units]:
    """Parse NOTAM report string"""
    # pylint: disable=too-many-locals
    units = Units(**IN_UNITS)
    sanitized = sanitize(report)
    qualifiers, station, start_time, end_time = None, None, None, None
    body, number, replaces, report_type = "", None, None, None
    schedule, lower, upper, text = None, None, None, sanitized
    match = KEY_PATTERN.search(text)
    # Type and number here
    if match and match.start() > 0:
        number, report_type, replaces = _header(text[: match.start()])
    start_text, end_text = "", ""
    while match:
        tag = match.group()[0]
        text = text[match.end() :]
        match = KEY_PATTERN.search(text)
        item = (text[: match.start()] if match else text).strip()
        if tag == "Q":
            qualifiers = _qualifiers(item, units)
        elif tag == "A":
            station = item
        elif tag == "B":
            start_text = item
        elif tag == "C":
            end_text = item
        elif tag == "D":
            schedule = item
        elif tag == "E":
            body = item
        elif tag == "F":
            lower = core.make_altitude(item.split()[0], units, repr=item)[0]
        elif tag == "G":
            upper = core.make_altitude(item.split()[0], units, repr=item)[0]
    start_time, end_time = parse_linked_times(start_text, end_text)
    return (
        NotamData(
            raw=report,
            sanitized=sanitized,
            station=station,
            time=issued,
            remarks=None,
            number=number,
            replaces=replaces,
            type=report_type,
            qualifiers=qualifiers,
            start_time=start_time,
            end_time=end_time,
            schedule=schedule,
            body=body,
            lower=lower,
            upper=upper,
        ),
        units,
    )


def sanitize(report: str) -> str:
    """Retuns a sanitized report ready for parsing"""
    return report.replace("\r", "").strip()


class Notams(Reports):
    """Class to handle NOTAM reports"""

    data: Optional[List[NotamData]] = None  # type: ignore
    radius: int = 10

    def __init__(self, code: str = None, coord: Coord = None):
        super().__init__(code, coord)
        self.service = FAA_NOTAM("notam")

    async def _post_update(self):
        self.data = []
        for report in self.raw:
            if "||" in report:
                issue_text, report = report.split("||")
                issued_value = datetime.strptime(issue_text, r"%m/%d/%Y %H%M")
                issued = Timestamp(issue_text, issued_value)
            else:
                issued = None
            data, units = parse(report, issued=issued)
            self.data.append(data)
        self.units = units

    def _post_parse(self):
        self.data = []
        for report in self.raw:
            data, units = parse(report)
            self.data.append(data)
        self.units = units

    @staticmethod
    def sanitize(report: str) -> str:
        """Sanitizes a NOTAM string"""
        return sanitize(report)

    async def async_update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """Async updates report data by fetching and parsing the report"""
        reports = await self.service.async_fetch(  # type: ignore
            icao=self.code, coord=self.coord, radius=self.radius, timeout=timeout
        )
        self.source = self.service.root
        return await self._update(reports, None, disable_post)
