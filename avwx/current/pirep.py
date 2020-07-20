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


def _root(item: str) -> dict:
    """
    Parses report root data including station and report type
    """
    # pylint: disable=redefined-argument-from-local
    report_type = None
    station = None
    for item in item.split():
        if item in ("UA", "UUA"):
            report_type = item
        elif not station:
            station = item
    return {"station": station, "type": report_type}


def _location(item: str) -> Location:
    """
    Convert a location element to a Location object
    """
    items = item.split()
    if not items:
        return None
    station, direction, distance = None, None, None
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
        direction = core.make_number(direction, literal=True)
    if distance:
        distance = core.make_number(distance)
    return Location(item, station, direction, distance)


def _time(item: str, target: date = None) -> Timestamp:
    """
    Convert a time element to a Timestamp
    """
    return core.make_timestamp(item, time_only=True, target_date=target)


def _altitude(item: str) -> Union[Number, str]:
    """
    Convert reporting altitude to a Number or string
    """
    if item.isdigit():
        return core.make_number(item)
    return item


def _aircraft(item: str) -> str:
    """
    Returns the Aircraft from the ICAO code
    """
    try:
        return Aircraft.from_icao(item)
    except ValueError:
        return item


def _clouds(item: str) -> List[Cloud]:
    """
    Convert cloud element to a list of Clouds
    """
    clouds = item.split()
    # BASES 004 TOPS 016
    if "BASES" in clouds and "TOPS" in clouds:
        base = clouds[clouds.index("BASES") + 1]
        top = clouds[clouds.index("TOPS") + 1]
        return [Cloud(item, base=base, top=top)]
    return [core.make_cloud(cloud) for cloud in clouds]


def _number(item: str) -> Number:
    """
    Convert an element to a Number
    """
    return core.make_number(item)


_DIR_SIG = {"BLO": "ceiling"}


def _find_floor_ceiling(items: List[str]) -> Tuple[List[str], dict]:
    """
    Extracts the floor and ceiling from item list
    """
    ret = {"floor": None, "ceiling": None}
    for i, item in enumerate(items):
        hloc = item.find("-")
        # TRACE RIME 070-090
        if hloc > -1 and item[:hloc].isdigit() and item[hloc + 1 :].isdigit():
            for key, val in zip(("floor", "ceiling"), items.pop(i).split("-")):
                ret[key] = core.make_number(val)
            break
        # CONT LGT CHOP BLO 250
        if item in _DIR_SIG:
            ret[_DIR_SIG[item]] = core.make_number(items[i + 1])
            items = items[:i]
            break
        # LGT RIME 025
        if item.isdigit():
            num = core.make_number(item)
            ret["floor"], ret["ceiling"] = num, num
            break
    return items, ret


def _turbulence(item: str) -> Turbulence:
    """
    Convert reported turbulence to a Turbulence object
    """
    items, ret = _find_floor_ceiling(item.split())
    ret["severity"] = " ".join(items)
    return Turbulence(**ret)


def _icing(item: str) -> Icing:
    """
    Convert reported icing to an Icing object
    """
    items, ret = _find_floor_ceiling(item.split())
    ret["severity"] = items.pop(0)
    ret["type"] = items[0] if items else None
    return Icing(**ret)


def _remarks(item: str) -> str:
    """
    Returns the remarks. Reserved for later parsing
    """
    return item


def _wx(item: str) -> dict:
    """
    Parses remaining weather elements
    """
    # pylint: disable=redefined-argument-from-local
    ret = {"wx": []}
    items = item.split()
    for item in items:
        if len(item) > 2 and item.startswith("FV"):
            _, ret["flight_visibility"] = core.get_visibility([item[2:]], _UNITS)
        else:
            ret["wx"].append(item)
    return ret


_HANDLERS = {
    "OV": ("location", _location),
    "FL": ("altitude", _altitude),
    "TP": ("aircraft", _aircraft),
    "SK": ("clouds", _clouds),
    "TA": ("temperature", _number),
    "TB": ("turbulence", _turbulence),
    "IC": ("icing", _icing),
    "RM": ("remarks", _remarks),
}


_DICT_HANDLERS = {"WX": _wx}


def parse(report: str, issued: date = None) -> PirepData:
    """
    Returns a PirepData object based on the given report
    """
    if not report:
        return None
    sanitized = sanitization.sanitize_report_string(report)
    # NOTE: will need to implement PIREP-specific list clean
    resp = {"raw": report, "sanitized": sanitized, "station": None, "remarks": None}
    data = sanitized.split("/")
    resp.update(_root(data.pop(0).strip()))
    for item in data:
        if not item or len(item) < 2:
            continue
        tag = item[:2]
        item = item[2:].strip()
        if tag == "TM":
            resp["time"] = _time(item, issued)
        elif tag in _HANDLERS:
            key, handler = _HANDLERS[tag]
            resp[key] = handler(item)
        elif tag in _DICT_HANDLERS:
            resp.update(_DICT_HANDLERS[tag](item))
    return PirepData(**resp)


class Pireps(Reports):
    """
    Class to handle pilot report data
    """

    data: Optional[List[PirepData]] = None

    @staticmethod
    def _report_filter(reports: List[str]) -> List[str]:
        """
        Removes AIREPs before updating raw_reports
        """
        return [r for r in reports if not r.startswith("ARP")]

    def _post_update(self):
        self.data = []
        for report in self.raw:
            self.data.append(parse(report, issued=self.issued))

    @staticmethod
    def sanitize(report: str) -> str:
        """
        Sanitizes a PIREP string
        """
        return sanitization.sanitize_report_string(report)
