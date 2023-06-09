"""
NOTAM report parsing
"""

# pylint: disable=invalid-name

# stdlib
import re
from contextlib import suppress
from datetime import datetime, timezone
from typing import List, Optional, Union

# library
from dateutil.tz import gettz
from avwx import exceptions

# module
from avwx.current.base import Reports
from avwx.parsing import core
from avwx.service import FAA_NOTAM
from avwx.static.core import SPECIAL_NUMBERS
from avwx.static.notam import (
    CODES,
    CONDITION,
    PURPOSE,
    REPORT_TYPE,
    SCOPE,
    SUBJECT,
    TRAFFIC_TYPE,
)
from avwx.structs import (
    Code,
    Coord,
    NotamData,
    Number,
    Qualifiers,
    Timestamp,
    Tuple,
    Units,
)

# https://www.navcanada.ca/en/briefing-on-the-transition-to-icao-notam-format.pdf
# https://www.faa.gov/air_traffic/flight_info/aeronav/notams/media/2021-09-07_ICAO_NOTAM_101_Presentation_for_Airport_Operators.pdf


ALL_KEYS_PATTERN = re.compile(r"\b[A-GQ]\) ")
KEY_PATTERNS = {
    "Q": re.compile(r"\b[A-G]\) "),
    "A": re.compile(r"\b[B-G]\) "),
    "B": re.compile(r"\b[C-G]\) "),
    "C": re.compile(r"\b[D-G]\) "),
    "D": re.compile(r"\b[E-G]\) "),
    "E": re.compile(r"\b[FG]\) "),
    "F": re.compile(r"\bG\) "),
    # No "G"
}


def _rear_coord(value: str) -> Optional[Coord]:
    """Convert coord strings with direction characters at the end: 5126N00036W"""
    if len(value) != 11:
        return None
    try:
        lat = float(f"{value[:2]}.{value[2:4]}")
        lon = float(f"{value[5:8]}.{value[8:10]}")
    except ValueError:
        return None
    if value[4] == "S":
        lat *= -1
    if value[10] == "W":
        lon *= -1
    return Coord(lat, lon, value)


def _split_location(
    location: Optional[str],
) -> Tuple[Optional[Coord], Optional[Number]]:
    """Identify coordinate and radius from location element"""
    if not location:
        return None, None
    coord, radius = None, None
    if len(location) == 14 and location[-3:].isdigit():
        radius = core.make_number(location[-3:])
        location = location[:-3]
    if len(location) == 11 and location[-1] in {"E", "W"}:
        coord = _rear_coord(location)
    return coord, radius


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


def _find_q_codes(
    codes: List[str],
) -> Tuple[
    Optional[Code],
    List[Code],
    List[Code],
    Optional[str],
    Optional[str],
    Optional[str],
]:
    """Identify traffic, purpose, and scope codes"""
    # The 'K' code can be both purpose and scope, but they have the same value
    traffic, lower, upper, location = None, None, None, None
    purpose: List[Code] = []
    scope: List[Code] = []
    for code in codes:
        if not code:
            continue
        # Altitudes can be int or float values
        with suppress(ValueError):
            float(code)
            if not lower:
                lower = code
            else:
                upper = code
            continue
        # location will always be the longest element if available
        if len(code) > 10:
            location = code
            continue
        # Remaining elements must match known value dictionary combinations
        if not traffic and code in TRAFFIC_TYPE:
            traffic = Code.from_dict(code, TRAFFIC_TYPE)
            continue
        if not purpose:
            purpose = Code.from_list(code, PURPOSE, exclusive=True)
        if not scope:
            scope = Code.from_list(code, SCOPE, exclusive=True)
    return traffic, purpose, scope, lower, upper, location


def _qualifiers(value: str, units: Units) -> Qualifiers:
    """Parse the NOTAM Q) line into components"""
    # pylint: disable=too-many-locals
    fir, q_code, *codes = [i.strip() for i in re.split("/| ", value.strip())]
    traffic, purpose, scope, lower, upper, location = _find_q_codes(codes)
    subject, condition = None, None
    if q_code.startswith("Q"):
        subject = Code.from_dict(q_code[1:3], SUBJECT)
        condition_code = q_code[3:]
        if condition_code.startswith("XX"):
            condition = Code("XX", (condition_code[2:] or "Unknown").strip())
        else:
            condition = Code.from_dict(condition_code, CONDITION, error=False)
    coord, radius = _split_location(location)
    return Qualifiers(
        repr=value,
        fir=fir,
        subject=subject,
        condition=condition,
        traffic=traffic,
        purpose=purpose,
        scope=scope,
        lower=make_altitude(lower, units),
        upper=make_altitude(upper, units),
        coord=coord,
        radius=radius,
    )


def _tz_offset_for(name: Optional[str]) -> Optional[timezone]:
    """Generates a timezone from tz string name"""
    if not name:
        return None
    if tz := gettz(name):
        if offset := tz.utcoffset(datetime.now(timezone.utc)):
            return timezone(offset)
    return None


def make_year_timestamp(
    value: str,
    repr: str,  # pylint: disable=redefined-builtin
    tzname: Optional[str] = None,
) -> Union[Timestamp, Code, None]:
    """Convert NOTAM timestamp which includes year and month"""
    values = value.strip().split()
    if not values:
        return None
    value = values[0]
    if code := CODES.get(value):
        return Code(value, code)
    tz = _tz_offset_for(tzname) or timezone.utc
    raw = datetime.strptime(value[:10], r"%y%m%d%H%M")
    date = datetime(raw.year, raw.month, raw.day, raw.hour, raw.minute, tzinfo=tz)
    return Timestamp(repr, date)


def parse_linked_times(
    start: str, end: str
) -> Tuple[Union[Timestamp, Code, None], Union[Timestamp, Code, None]]:
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


def make_altitude(value: Optional[str], units: Units) -> Optional[Number]:
    """Parse NOTAM altitudes"""
    if not value:
        return None
    if trimmed := value.split()[0].strip(" ."):
        if trimmed in SPECIAL_NUMBERS or trimmed[0].isdigit():
            return core.make_altitude(trimmed, units, repr=value)[0]
    return None


def parse(report: str, issued: Optional[Timestamp] = None) -> Tuple[NotamData, Units]:
    """Parse NOTAM report string"""
    # pylint: disable=too-many-locals
    units = Units.international()
    sanitized = sanitize(report)
    qualifiers, station, start_time, end_time = None, None, None, None
    body, number, replaces, report_type = "", None, None, None
    schedule, lower, upper, text = None, None, None, sanitized
    match = ALL_KEYS_PATTERN.search(text)
    # Type and number here
    if match and match.start() > 0:
        number, report_type, replaces = _header(text[: match.start()])
    start_text, end_text = "", ""
    while match:
        tag = match.group()[0]
        text = text[match.end() :]
        try:
            match = KEY_PATTERNS[tag].search(text)
        except KeyError:
            match = None
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
            lower = make_altitude(item, units)
        elif tag == "G":
            upper = make_altitude(item, units)
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

    def __init__(self, code: Optional[str] = None, coord: Optional[Coord] = None):
        super().__init__(code, coord)
        self.service = FAA_NOTAM("notam")

    async def _post_update(self) -> None:
        self._post_parse()

    def _post_parse(self) -> None:
        self.data, units = [], None
        if self.raw is None:
            return
        for report in self.raw:
            if "||" in report:
                issue_text, report = report.split("||")
                issued_value = datetime.strptime(issue_text, r"%m/%d/%Y %H%M")
                issued = Timestamp(issue_text, issued_value)
            else:
                issued = None
            try:
                data, units = parse(report, issued=issued)
                self.data.append(data)
            except Exception as exc:  # pylint: disable=broad-except
                exceptions.exception_intercept(exc, raw=report)  # type: ignore
        if units:
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
