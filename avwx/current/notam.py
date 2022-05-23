"""
NOTAM report parsing
"""

# stdlib
import re
from datetime import datetime
from typing import List, Optional

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
    if value[5] == "S":
        lat *= -1
    lon = float(f"{value[5:7]}.{value[7:9]}")
    if value[9] == "W":
        lon *= -1
    return Coord(lat, lon, value)


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
            condition = Code("XX", condition_code[2:])
        else:
            condition = Code.from_dict(condition_code, CONDITION)
    return Qualifiers(
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


def make_year_timestamp(timestamp: str) -> Optional[Timestamp]:
    """Convert NOTAM timestamp which includes year and month"""
    timestamp = timestamp.strip()
    if not timestamp:
        return None
    if timestamp == "PERM":
        date_obj = datetime(2100, 1, 1)
    else:
        dt_format = r"%y%m%d%H%M" if len(timestamp) == 10 else r"%y%m%d%H%M%Z"
        date_obj = datetime.strptime(timestamp, dt_format)
    return Timestamp(timestamp, date_obj)


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
        header = text[: match.start()].strip().split()
        if len(header) == 3:
            number, type_text, replaces = header
        else:
            number, type_text = header
        report_type = Code.from_dict(type_text, REPORT_TYPE)
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
            start_time = make_year_timestamp(item)
        elif tag == "C":
            end_time = make_year_timestamp(item)
        elif tag == "D":
            schedule = item
        elif tag == "E":
            body = item
        elif tag == "F":
            lower = core.make_altitude(item.split()[0], units, repr=item)[0]
        elif tag == "G":
            upper = core.make_altitude(item.split()[0], units, repr=item)[0]
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
