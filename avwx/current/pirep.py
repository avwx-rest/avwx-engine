"""
Functions for parsing PIREPs
"""

# pylint: disable=too-many-boolean-expressions

# stdlib
from contextlib import suppress
from datetime import date
from typing import List, Optional, Tuple, Union

# module
from avwx import exceptions
from avwx.current.base import Reports, get_wx_codes
from avwx.parsing import core, sanitization
from avwx.service import NOAA_ADDS
from avwx.static.core import CARDINALS, CLOUD_LIST, NA_UNITS
from avwx.structs import (
    Aircraft,
    Cloud,
    Code,
    Coord,
    Icing,
    Location,
    Number,
    PirepData,
    Sanitization,
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
    for target in ("MILES", "OF"):
        with suppress(ValueError):
            items.remove(target)
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
    # 10 EAST
    # 15 SW LRP
    elif items[0].isdigit():
        if items[1] in CARDINALS:
            distance, direction = items[0], items[1]
            if len(items) == 3:
                station = items[2]
        else:
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


def _time(item: str, target: Optional[date] = None) -> Optional[Timestamp]:
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


def _non_digit_cloud(cloud: str) -> Tuple[Optional[str], str]:
    """Returns cloud type and altitude for non-digit TOPS BASES cloud elements"""
    # 5000FT
    if cloud.endswith("FT"):
        cloud = cloud[:-4]
        if cloud.isdigit():
            return None, cloud
    # SCT030-035
    if "-" in cloud:
        parts = cloud.split("-")
        if not parts[0].isdigit():
            return parts[0][:3], parts[-1]
        return None, parts[-1]
    return cloud[:3], cloud[3:]


def _clouds(item: str) -> List[Cloud]:
    """Convert cloud element to a list of Clouds"""
    clouds = item.replace(",", "").split()
    # BASES 004 TOPS 016
    # BASES SCT030 TOPS SCT058
    if "BASES" in clouds and "TOPS" in clouds:
        cloud_type = None
        base = clouds[clouds.index("BASES") + 1]
        top = clouds[clouds.index("TOPS") + 1]
        if not base.isdigit():
            cloud_type, base = _non_digit_cloud(base)
        if not top.isdigit():
            cloud_type, top = _non_digit_cloud(top)
        return [Cloud(item, cloud_type, base=int(base), top=int(top))]
    return [core.make_cloud(cloud) for cloud in clouds]


def _number(item: str) -> Optional[Number]:
    """Convert an element to a Number"""
    value = item.strip("CF ")
    if " " in value:
        return None
    return core.make_number(value, item)


def _separate_floor_ceiling(item: str) -> Tuple[Optional[Number], Optional[Number]]:
    """Extract floor and ceiling numbers from hyphen string"""
    floor_str, ceiling_str = item.split("-")
    floor = core.make_number(floor_str)
    ceiling = core.make_number(ceiling_str)
    if (
        floor
        and ceiling
        and floor.value
        and ceiling.value
        and floor.value > ceiling.value
    ):
        return ceiling, floor
    return floor, ceiling


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
            floor, ceiling = _separate_floor_ceiling(items.pop(i))
            break
        # CONT LGT CHOP BLO 250
        if item == "BLO":
            altitude = items[i + 1]
            if "-" in altitude:
                floor, ceiling = _separate_floor_ceiling(altitude)
            else:
                ceiling = core.make_number(altitude)
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
    severity = items.pop(0) if items else ""
    return Icing(
        severity=severity,
        floor=floor,
        ceiling=ceiling,
        type=items[0] if items else None,
    )


def _remarks(item: str) -> str:
    """Returns the remarks. Reserved for later parsing"""
    return item


def _wx(item: str) -> Tuple[List[Code], Optional[Number], List[str]]:
    """Parses remaining weather elements"""
    # pylint: disable=redefined-argument-from-local
    other: List[str] = []
    flight_visibility = None
    for item in item.split():
        if len(item) > 2 and item.startswith("FV"):
            _, flight_visibility = core.get_visibility([item[2:]], _UNITS)
        else:
            other.append(item)
    other, wx_codes = get_wx_codes(other)
    return wx_codes, flight_visibility, other


def _sanitize_report_list(data: List[str], sans: Sanitization) -> List[str]:
    """Fixes report elements based on neighbor values"""
    for i, item in reversed(list(enumerate(data))):
        # Fix spaced cloud top Ex: BKN030 TOP045   BASE020 TOPS074
        # But not BASES SCT014 TOPS SCT021
        if (
            item.startswith("TOP")
            and item != "TOPS"
            and i > 0
            and len(data[i - 1]) >= 6
            and (data[i - 1][:3] in CLOUD_LIST or data[i - 1].startswith("BASE"))
        ):
            key = f"{data[i-1]} {item}"
            data[i - 1] += "-" + data.pop(i)
            sans.log(key, data[i - 1])
        # Fix separated clouds Ex: BASES OVC 049 TOPS 055
        elif item in CLOUD_LIST and i + 1 < len(data) and data[i + 1].isdigit():
            data[i] = item + data.pop(i + 1)
            sans.extra_spaces_found = True
    deduped = core.dedupe(data, only_neighbors=True)
    if len(data) != len(deduped):
        sans.duplicates_found = True
    return deduped


def sanitize(report: str) -> Tuple[str, Sanitization]:
    """Returns a sanitized report ready for parsing"""
    sans = Sanitization()
    clean = sanitization.sanitize_report_string(report, sans)
    data = _sanitize_report_list(clean.split(), sans)
    return " ".join(data), sans


def parse(
    report: str, issued: Optional[date] = None
) -> Tuple[Optional[PirepData], Optional[Sanitization]]:
    """Returns a PirepData object based on the given report"""
    # pylint: disable=too-many-locals,too-many-branches
    if not report:
        return None, None
    sanitized, sans = sanitize(report)
    data = sanitized.split("/")
    station, report_type = _root(data.pop(0).strip())
    time, location, altitude, aircraft = None, None, None, None
    clouds, temperature, turbulence, other = None, None, None, None
    icing, remarks, flight_visibility, wx_codes = None, None, None, None
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
            wx_codes, flight_visibility, other = _wx(item)
    return (
        PirepData(
            aircraft=aircraft,
            altitude=altitude,
            clouds=clouds,
            flight_visibility=flight_visibility,
            icing=icing,
            location=location,
            other=other or [],
            raw=report,
            remarks=remarks,
            sanitized=sanitized,
            station=station,
            temperature=temperature,
            time=time,
            turbulence=turbulence,
            type=report_type,
            wx_codes=wx_codes or [],
        ),
        sans,
    )


class Pireps(Reports):
    """Class to handle pilot report data"""

    data: Optional[List[Optional[PirepData]]] = None  # type: ignore
    sanitization: Optional[List[Optional[Sanitization]]] = None  # type: ignore

    def __init__(self, code: Optional[str] = None, coord: Optional[Coord] = None):
        super().__init__(code, coord)
        self.service = NOAA_ADDS("aircraftreport")

    @staticmethod
    def _report_filter(reports: List[str]) -> List[str]:
        """Removes AIREPs before updating raw_reports"""
        return [r for r in reports if not r.startswith("ARP")]

    async def _post_update(self) -> None:
        self.data, self.sanitization = [], []
        if self.raw is None:
            return
        for report in self.raw:
            try:
                data, sans = parse(report, issued=self.issued)
                self.data.append(data)
                self.sanitization.append(sans)
            except Exception as exc:  # pylint: disable=broad-except
                exceptions.exception_intercept(exc, raw=report)  # type: ignore

    def _post_parse(self) -> None:
        self.data, self.sanitization = [], []
        if self.raw is None:
            return
        for report in self.raw:
            data, sans = parse(report, issued=self.issued)
            self.data.append(data)
            self.sanitization.append(sans)

    @staticmethod
    def sanitize(report: str) -> str:
        """Sanitizes a PIREP string"""
        return sanitize(report)[0]
