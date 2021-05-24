"""
Functions for parsing PIREPs
"""

# stdlib
from datetime import date
from typing import List, Optional, Tuple, Union

# module
from avwx.current.base import Reports
from avwx.parsing import core, sanitization
from avwx.static.core import NA_UNITS
from avwx.structs import (
    Aircraft,
    Cloud,
    Icing,
    Location,
    Number,
    PirepData,
    Timestamp,
    Turbulence,
    Units,
)

_UNITS = Units(**NA_UNITS)


def _root(item: str) -> Tuple[Optional[str], Optional[str]]:
    """Parses report root data including station and report type"""
    # pylint: disable=redefined-argument-from-local
    report_type = None
    station = None
    for item in item.split():
        if item in ("UA", "UUA"):
            report_type = item
        elif not station:
            station = item
    return station, report_type


def _location(item: str) -> Optional[Location]:
    """Convert a location element to a Location object"""
    items = item.split()
    if not items:
        return None
    station, direction, distance = None, None, None
    direction_number, distance_number = None, None
    if len(items) == 1:
        ilen = len(item)
        # MLB
        if ilen < 5:
            station = item
        # MKK360002 or KLGA220015
        elif ilen in (9, 10) and item[-6:].isdigit():
            station, direction, distance = item[:-6], item[-6:-3], item[-3:]
    # 10 WGON
    elif items[0].isdigit():
        station, direction, distance = items[1][-3:], items[1][:-3], items[0]
    # GON 270010
    elif items[1].isdigit():
        station, direction, distance = items[0], items[1][:3], items[1][3:]
    # Convert non-null elements
    if direction:
        direction_number = core.make_number(direction, literal=True)
    if distance:
        distance_number = core.make_number(distance)
    return Location(item, station, direction_number, distance_number)


def _time(item: str, target: date = None) -> Optional[Timestamp]:
    """Convert a time element to a Timestamp"""
    return core.make_timestamp(item, time_only=True, target_date=target)


def _altitude(item: str) -> Union[Optional[Number], str]:
    """Convert reporting altitude to a Number or string"""
    if item.isdigit():
        return core.make_number(item)
    return item


def _aircraft(item: str) -> Union[Aircraft, str]:
    """Returns the Aircraft from the ICAO code"""
    try:
        return Aircraft.from_icao(item)
    except ValueError:
        return item


def _clouds(item: str) -> List[Cloud]:
    """Convert cloud element to a list of Clouds"""
    clouds = item.split()
    # BASES 004 TOPS 016
    if "BASES" in clouds and "TOPS" in clouds:
        base = clouds[clouds.index("BASES") + 1]
        top = clouds[clouds.index("TOPS") + 1]
        return [Cloud(item, base=int(base), top=int(top))]
    return [core.make_cloud(cloud) for cloud in clouds]


def _number(item: str) -> Optional[Number]:
    """Convert an element to a Number"""
    return core.make_number(item)


def _find_floor_ceiling(
    items: List[str],
) -> Tuple[List[str], Optional[Number], Optional[Number]]:
    """Extracts the floor and ceiling from item list"""
    floor: Optional[Number] = None
    ceiling: Optional[Number] = None

    for i, item in enumerate(items):
        hloc = item.find("-")
        # TRACE RIME 070-090
        if hloc > -1 and item[:hloc].isdigit() and item[hloc + 1 :].isdigit():
            floor_str, ceiling_str = items.pop(i).split("-")
            floor = core.make_number(floor_str)
            ceiling = core.make_number(ceiling_str)
            break
        # CONT LGT CHOP BLO 250
        if item == "BLO":
            ceiling = core.make_number(items[i + 1])
            items = items[:i]
            break
        # LGT RIME 025
        if item.isdigit():
            num = core.make_number(item)
            floor, ceiling = num, num
            break
    return items, floor, ceiling


def _turbulence(item: str) -> Turbulence:
    """Convert reported turbulence to a Turbulence object"""
    items, floor, ceiling = _find_floor_ceiling(item.split())
    return Turbulence(
        severity=" ".join(items),
        floor=floor,
        ceiling=ceiling,
    )


def _icing(item: str) -> Icing:
    """Convert reported icing to an Icing object"""
    items, floor, ceiling = _find_floor_ceiling(item.split())
    severity = items.pop(0)
    return Icing(
        severity=severity,
        floor=floor,
        ceiling=ceiling,
        type=items[0] if items else None,
    )


def _remarks(item: str) -> str:
    """Returns the remarks. Reserved for later parsing"""
    return item


def _wx(item: str) -> Tuple[List[str], Optional[Number]]:
    """Parses remaining weather elements"""
    # pylint: disable=redefined-argument-from-local
    wx_codes: List[str] = []
    flight_visibility = None
    items = item.split()
    for item in items:
        if len(item) > 2 and item.startswith("FV"):
            _, flight_visibility = core.get_visibility([item[2:]], _UNITS)
        else:
            wx_codes.append(item)
    return wx_codes, flight_visibility


def parse(report: str, issued: date = None) -> Optional[PirepData]:
    """Returns a PirepData object based on the given report"""
    if not report:
        return None
    sanitized = sanitization.sanitize_report_string(report)
    # NOTE: will need to implement PIREP-specific list clean
    data = sanitized.split("/")
    station, report_type = _root(data.pop(0).strip())
    time, location, altitude, aircraft = None, None, None, None
    clouds, temperature, turbulence, other = None, None, None, None
    icing, remarks, flight_visibility = None, None, None
    for item in data:
        if not item or len(item) < 2:
            continue
        tag = item[:2]
        item = item[2:].strip()
        if tag == "TM":
            time = _time(item, issued)
        elif tag == "OV":
            location = _location(item)
        elif tag == "FL":
            altitude = _altitude(item)
        elif tag == "TP":
            aircraft = _aircraft(item)
        elif tag == "SK":
            clouds = _clouds(item)
        elif tag == "TA":
            temperature = _number(item)
        elif tag == "TB":
            turbulence = _turbulence(item)
        elif tag == "IC":
            icing = _icing(item)
        elif tag == "RM":
            remarks = _remarks(item)
        elif tag == "WX":
            other, flight_visibility = _wx(item)
    return PirepData(
        raw=report,
        sanitized=sanitized,
        station=station,
        time=time,
        remarks=remarks,
        aircraft=aircraft,
        altitude=altitude,
        clouds=clouds,
        flight_visibility=flight_visibility,
        icing=icing,
        location=location,
        temperature=temperature,
        turbulence=turbulence,
        type=report_type,
        wx=other,
    )


class Pireps(Reports):
    """Class to handle pilot report data"""

    data: Optional[List[PirepData]] = None  # type: ignore

    @staticmethod
    def _report_filter(reports: List[str]) -> List[str]:
        """Removes AIREPs before updating raw_reports"""
        return [r for r in reports if not r.startswith("ARP")]

    async def _post_update(self):
        self.data = []
        for report in self.raw:
            self.data.append(parse(report, issued=self.issued))

    def _post_parse(self):
        self.data = []
        for report in self.raw:
            self.data.append(parse(report, issued=self.issued))

    @staticmethod
    def sanitize(report: str) -> str:
        """Sanitizes a PIREP string"""
        return sanitization.sanitize_report_string(report)
