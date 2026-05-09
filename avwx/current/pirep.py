"""PIREP parsing.

A PIREP (Pilot Report) is an observation made by pilots inflight.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from avwx import exceptions
from avwx.current.base import Reports, get_wx_codes
from avwx.parsing import core
from avwx.parsing.sanitization.pirep import clean_pirep_string
from avwx.service.scrape import NoaaApiList
from avwx.static.core import CARDINALS, CLOUD_LIST
from avwx.structs import (
    Aircraft,
    Cloud,
    Code,
    Coord,
    Icing,
    Location,
    PirepData,
    Sanitization,
    Turbulence,
)
from avwx.units import Measurement

if TYPE_CHECKING:
    from datetime import date

    from avwx.structs import Timestamp


class Pireps(Reports):
    """Manages multiple PIREP reports for a single station."""

    data: list[PirepData | None] | None = None  # type: ignore
    sanitization: list[Sanitization | None] | None = None  # type: ignore

    def __init__(self, code: str | None = None, coord: Coord | None = None):
        super().__init__(code, coord)
        self.service = NoaaApiList("pirep")

    @staticmethod
    def _report_filter(reports: list[str]) -> list[str]:
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
            except Exception as exc:  # noqa: BLE001
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
        return sanitize(report)[0]


def _root(report: str) -> tuple[str | None, str | None]:
    report_type = None
    station = None
    for item in report.split():
        if item in ("UA", "UUA"):
            report_type = item
        elif not station:
            station = item
    return station, report_type


def _location(item: str) -> Location | None:
    items = item.split()
    for target in ("MILES", "OF"):
        with suppress(ValueError):
            items.remove(target)
    if not items:
        return None
    station: str | None = None
    direction: Measurement | None = None
    distance: Measurement | None = None
    if len(items) == 1:
        ilen = len(item)
        if ilen < 5:
            station = item
        elif ilen in {9, 10} and item[-6:].isdigit():
            station = item[:-6]
            dir_str, dist_str = item[-6:-3], item[-3:]
            if dir_str.isdigit():
                direction = Measurement(int(dir_str), "degree")
            distance = Measurement(int(dist_str), "nmi")
    elif items[0].isdigit():
        if items[1] in CARDINALS:
            dist_str, dir_tok = items[0], items[1]
            distance = Measurement(int(dist_str), "nmi")
            direction = Measurement(CARDINALS[dir_tok], "degree")
            if len(items) == 3:
                station = items[2]
        else:
            station = items[1][-3:]
            if items[1][:-3].isdigit():
                direction = Measurement(int(items[1][:-3]), "degree")
            distance = Measurement(int(items[0]), "nmi")
    elif len(items) >= 2 and items[1].isdigit():
        station = items[0]
        direction = Measurement(int(items[1][:3]), "degree")
        if len(items[1]) > 3:
            distance = Measurement(int(items[1][3:]), "nmi")
    return Location(repr=item, station=station, direction=direction, distance=distance)


def _time(item: str | None, target: date | None = None) -> Timestamp | None:
    return core.make_timestamp(item, time_only=True, target_date=target)


def _altitude(item: str) -> Measurement | str | None:
    if item.isdigit():
        return Measurement(int(item) * 100, "ft")
    return item or None


def _aircraft(item: str) -> Aircraft | str:
    try:
        return Aircraft.from_icao(item)
    except ValueError:
        return item


def _non_digit_cloud(cloud: str) -> tuple[str | None, str]:
    if cloud.endswith("FT"):
        cloud = cloud[:-2]
        if cloud.isdigit():
            return None, cloud
    if "-" not in cloud:
        return cloud[:3], cloud[3:]
    parts = cloud.split("-")
    return (None, parts[-1]) if parts[0].isdigit() else (parts[0][:3], parts[-1])


def _clouds(item: str) -> list[Cloud]:
    clouds_raw = item.replace(",", "").split()
    if "BASES" in clouds_raw and "TOPS" in clouds_raw:
        cloud_type: str | None = None
        base_tok = clouds_raw[clouds_raw.index("BASES") + 1]
        top_tok = clouds_raw[clouds_raw.index("TOPS") + 1]
        if not base_tok.isdigit():
            cloud_type, base_tok = _non_digit_cloud(base_tok)
        if not top_tok.isdigit():
            cloud_type, top_tok = _non_digit_cloud(top_tok)
        base = Measurement(int(base_tok) * 100, "ft") if base_tok.isdigit() else None
        top = Measurement(int(top_tok) * 100, "ft") if top_tok.isdigit() else None
        return [Cloud(type=cloud_type, base=base, top=top)]
    result = []
    for cloud in clouds_raw:
        c, _ = core.make_cloud(cloud)
        result.append(c)
    return result


def _floor_ceiling_from_str(s: str) -> tuple[Measurement | None, Measurement | None]:
    if "-" in s and all(p.isdigit() for p in s.split("-")):
        floor_s, ceil_s = s.split("-")
        floor = Measurement(int(floor_s) * 100, "ft")
        ceiling = Measurement(int(ceil_s) * 100, "ft")
        if floor.magnitude > ceiling.magnitude:
            return ceiling, floor
        return floor, ceiling
    if s.isdigit():
        alt = Measurement(int(s) * 100, "ft")
        return alt, alt
    return None, None


def _find_floor_ceiling(
    items: list[str],
) -> tuple[list[str], Measurement | None, Measurement | None]:
    floor: Measurement | None = None
    ceiling: Measurement | None = None
    for i, item in enumerate(items):
        hloc = item.find("-")
        if hloc > -1 and item[:hloc].isdigit() and item[hloc + 1 :].isdigit():
            floor, ceiling = _floor_ceiling_from_str(items.pop(i))
            break
        if item == "BLO":
            altitude = items[i + 1] if i + 1 < len(items) else ""
            floor, ceiling = _floor_ceiling_from_str(altitude)
            items = items[:i]
            break
        if item.isdigit():
            alt = Measurement(int(item) * 100, "ft")
            floor, ceiling = alt, alt
            break
    return items, floor, ceiling


def _turbulence(item: str) -> Turbulence:
    items, floor, ceiling = _find_floor_ceiling(item.split())
    return Turbulence(severity=" ".join(items), floor=floor, ceiling=ceiling)


def _icing(item: str) -> Icing:
    items, floor, ceiling = _find_floor_ceiling(item.split())
    severity = items.pop(0) if items else ""
    return Icing(severity=severity, floor=floor, ceiling=ceiling, type=items[0] if items else None)


def _wx(report: str) -> tuple[list[Code], Measurement | None, list[str]]:
    other: list[str] = []
    flight_visibility: Measurement | None = None
    for item in report.split():
        if len(item) > 2 and item.startswith("FV"):
            _, vis, _, _ = core.get_visibility([item[2:]])
            flight_visibility = vis
        else:
            other.append(item)
    other, wx_codes = get_wx_codes(other)
    return wx_codes, flight_visibility, other


def _sanitize_report_list(data: list[str], sans: Sanitization) -> list[str]:
    for i, item in reversed(list(enumerate(data))):
        if (
            item.startswith("TOP")
            and item != "TOPS"
            and i > 0
            and len(data[i - 1]) >= 6
            and (data[i - 1][:3] in CLOUD_LIST or data[i - 1].startswith("BASE"))
        ):
            key = f"{data[i-1]} {item}"
            data[i - 1] += f"-{data.pop(i)}"
            sans.log(key, data[i - 1])
        elif item in CLOUD_LIST and i + 1 < len(data) and data[i + 1].isdigit():
            data[i] = item + data.pop(i + 1)
            sans.extra_spaces_found = True
    deduped = core.dedupe(data, only_neighbors=True)
    if len(data) != len(deduped):
        sans.duplicates_found = True
    return deduped


def sanitize(report: str) -> tuple[str, Sanitization]:
    sans = Sanitization()
    clean = clean_pirep_string(report, sans)
    data = _sanitize_report_list(clean.split(), sans)
    return " ".join(data), sans


def parse(
    report: str, issued: date | None = None
) -> tuple[PirepData | None, Sanitization | None]:
    """Parse a PIREP string into a :class:`~avwx.structs.PirepData` model."""
    if not report:
        return None, None
    sanitized, sans = sanitize(report)
    data = sanitized.split("/")
    station, report_type = _root(data.pop(0).strip())
    time: Timestamp | None = None
    location: Location | None = None
    altitude: Measurement | str | None = None
    aircraft: Aircraft | str | None = None
    clouds: list[Cloud] | None = None
    temperature: Measurement | None = None
    turbulence: Turbulence | None = None
    icing: Icing | None = None
    remarks: str | None = None
    flight_visibility: Measurement | None = None
    wx_codes: list[Code] | None = None
    other: list[str] | None = None

    for item in data:
        if not item or len(item) < 2:
            continue
        tag = item[:2]
        item = item[2:].strip()  # noqa: PLW2901
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
            temperature = Measurement(float(item.replace("M", "-")), "degC") if item else None
        elif tag == "TB":
            turbulence = _turbulence(item)
        elif tag == "IC":
            icing = _icing(item)
        elif tag == "RM":
            remarks = item
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
