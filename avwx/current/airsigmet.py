"""
A SIGMET (Significant Meteorological Information) is a weather advisory for the
safety of all aircraft. They are divided into:

- Convective - thunderstorms, hail, and cyclones
- Non-Convective - turbulence, icing, dust clouds, volcanic activity, and radiation

An AIRMET (Airman's Meteorological Information) is a weather advisory for
smaller aircraft or VFR navigation. They are divided into:

- Sierra - IFR conditions like low ceilings and mountain obscuration
- Tango - turbulence and high surface winds
- Zulu - icing and freezing levels

Both types share a similar report format and therefore are combined into a
single handling class. The `Bulletin` and weather type can be used to classify
each as a SIGMET or AIRMET for filtering purposes.
"""

# stdlib
from __future__ import annotations

import asyncio as aio
import re
from contextlib import suppress
from datetime import date, datetime, timezone
from itertools import chain

# library
from geopy.distance import distance as geo_distance  # type: ignore

# module
from avwx import exceptions
from avwx.base import AVWXBase
from avwx.exceptions import MissingExtraModule
from avwx.flight_path import to_coordinates
from avwx.load_utils import LazyLoad
from avwx.parsing import core
from avwx.service.bulk import NoaaBulk, NoaaIntl, Service
from avwx.static.airsigmet import BULLETIN_TYPES, INTENSITY, WEATHER_TYPES
from avwx.static.core import CARDINAL_DEGREES, CARDINALS
from avwx.structs import (
    AirSigmetData,
    AirSigObservation,
    Bulletin,
    Code,
    Coord,
    Movement,
    Number,
    Timestamp,
    Units,
)

try:
    from shapely.geometry import LineString  # type: ignore
except ModuleNotFoundError:
    LineString = None


class AirSigmet(AVWXBase):
    """
    In addition to the manager, you can use the `avwx.AirSigmet` class like any
    other report when you supply the report string via `parse` or
    `from_report`.

    ```python
    >>> from avwx import AirSigmet
    >>> report = 'WSPR31 SPJC 270529 SPIM SIGMET 3 VALID 270530/270830 SPJC- SPIM LIMA FIR EMBD TS OBS AT 0510Z NE OF LINE S0406 W07103 - S0358 W07225 - S0235 W07432 - S0114 W07503 TOP FL410 MOV SW NC='
    >>> sigmet = AirSigmet.from_report(report)
    True
    >>> sigmet.last_updated
    datetime.datetime(2022, 3, 27, 6, 29, 33, 300935, tzinfo=datetime.timezone.utc)
    >>> sigmet.data.observation.coords
    [Coord(lat=-4.06, lon=-71.03, repr='S0406 W07103'),
    Coord(lat=-3.58, lon=-72.25, repr='S0358 W07225'),
    Coord(lat=-2.35, lon=-74.32, repr='S0235 W07432'),
    Coord(lat=-1.14, lon=-75.03, repr='S0114 W07503')]
    >>> sigmet.data.observation.intensity
    Code(repr='NC', value='No change')
    >>> sigmet.data.observation.ceiling
    Number(repr='FL410', value=410, spoken='flight level four one zero')
    ```
    """

    data: AirSigmetData | None = None

    def _post_parse(self) -> None:
        if self.raw:
            self.data, self.units = parse(self.raw, self.issued)

    @staticmethod
    def sanitize(report: str) -> str:
        """Sanitizes the report string"""
        return sanitize(report)

    def intersects(self, path: LineString) -> bool:
        """Returns True if the report area intersects a flight path"""
        if LineString is None:
            extra = "shape"
            raise MissingExtraModule(extra)
        if not self.data:
            return False
        for data in (self.data.observation, self.data.forecast):
            if data:
                poly = data.poly
                if poly and path.intersects(poly):
                    return True
        return False

    def contains(self, coord: Coord) -> bool:
        """Returns True if the report area contains a coordinate"""
        if not self.data:
            return False
        for data in (self.data.observation, self.data.forecast):
            if data:
                poly = data.poly
                if poly and coord.point.within(poly):
                    return True
        return False


class AirSigManager:
    """
    Because of the global nature of these report types, we don't initialize a
    report class with a station ident like the other report types. Instead, we
    use a class to manage and update the list of all active SIGMET and AIRMET
    reports.

    ```python
    >>> from avwx import AirSigManager
    >>> from avwx.structs import Coord
    >>> manager = AirSigManager()
    >>> manager.update()
    True
    >>> manager.last_updated
    datetime.datetime(2022, 3, 27, 5, 54, 21, 516741, tzinfo=datetime.timezone.utc)
    >>> len(manager.reports)
    113
    >>> len(manager.contains(Coord(lat=33.12, lon=-105)))
    5
    >>> manager.reports[0].data.bulletin.type
    Code(repr='WA', value='airmet')
    >>> manager.reports[0].data.type
    'AIRMET SIERRA FOR IFR AND MTN OBSCN'
    ```
    """

    _services: list[Service]
    _raw: list[tuple[str, str | None]]
    last_updated: datetime | None = None
    raw: list[str]
    reports: list[AirSigmet] | None = None

    def __init__(self):  # type: ignore
        self._services = [NoaaBulk("airsigmet"), NoaaIntl("airsigmet")]
        self._raw, self.raw = [], []

    async def _update(self, index: int, timeout: int) -> list[tuple[str, str | None]]:
        source = self._services[index].root
        reports = await self._services[index].async_fetch(timeout=timeout)  # type: ignore
        raw: list[tuple[str, str | None]] = [(report, source) for report in reports if report]
        return raw

    def update(self, timeout: int = 10, *, disable_post: bool = False) -> bool:
        """Updates fetched reports and returns whether they've changed"""
        return aio.run(self.async_update(timeout, disable_post=disable_post))

    async def async_update(self, timeout: int = 10, *, disable_post: bool = False) -> bool:
        """Updates fetched reports and returns whether they've changed"""
        coros = [self._update(i, timeout) for i in range(len(self._services))]
        data = await aio.gather(*coros)
        raw = list(chain.from_iterable(data))
        reports = [i[0] for i in raw]
        if raw == self._raw:
            return False
        self._raw, self.raw = raw, reports
        self.last_updated = datetime.now(tz=timezone.utc)
        # Parse reports if not disabled
        if not disable_post:
            parsed = []
            for report, source in raw:
                try:
                    if obj := AirSigmet.from_report(report):
                        obj.source = source
                        parsed.append(obj)
                except Exception as exc:  # noqa: BLE001
                    exceptions.exception_intercept(exc, raw={"report": report})
            self.reports = parsed
        return True

    def along(self, coords: list[Coord]) -> list[AirSigmet]:
        """Returns available reports the intersect a flight path"""
        if LineString is None:
            extra = "shape"
            raise MissingExtraModule(extra)
        if self.reports is None:
            return []
        path = LineString([c.pair for c in coords])
        return [r for r in self.reports if r.intersects(path)]

    def contains(self, coord: Coord) -> list[AirSigmet]:
        """Returns available reports that contain a coordinate"""
        if self.reports is None:
            return []
        return [r for r in self.reports if r.contains(coord)]


# N1429 W09053 - N1427 W09052 - N1411 W09139 - N1417 W09141
_COORD_PATTERN = re.compile(r"\b[NS]\d{4} [EW]\d{5}\b( -)?")

# FROM 60NW ISN-INL-TVC-GIJ-UIN-FSD-BIL-60NW ISN
# FROM 70SSW ISN TO 20NNW FAR TO 70E DLH TO 40SE EAU TO 80SE RAP TO 40NNW BFF TO 70SSW
_NAVAID_PATTERN = re.compile(r"\b(\d{1,3}[NESW]{1,3} [A-z]{3}-?\b)|((-|(TO )|(FROM ))[A-z]{3}\b)")

# N OF N2050 AND S OF N2900
_LATTERAL_PATTERN = re.compile(r"\b([NS] OF [NS]\d{2,4})|([EW] OF [EW]\d{3,5})( AND)?\b")

NAVAIDS = LazyLoad("navaids")

# Used to assist parsing after sanitized. Removed after parse
_FLAGS = {
    "...": " <elip> ",
    "..": " <elip> ",
    ". ": " <break> ",
    "/VIS ": " <vis> VIS ",
}


def _parse_prep(report: str) -> list[str]:
    """Prepares sanitized string by replacing elements with flags"""
    report = report.rstrip(".")
    for key, val in _FLAGS.items():
        report = report.replace(key, val)
    return report.split()


def _clean_flags(data: list[str]) -> list[str]:
    return [i for i in data if i[0] != "<"]


def _bulletin(value: str) -> Bulletin:
    # if len(value) != 6:
    #     return None
    type_key = value[:2]
    return Bulletin(
        repr=value,
        type=Code(repr=type_key, value=BULLETIN_TYPES[type_key]),
        country=value[2:4],
        number=int(value[4:]),
    )


def _header(data: list[str]) -> tuple[list[str], Bulletin, str, str, str | None]:
    bulletin = _bulletin(data[0])
    correction, end = (data[3], 4) if len(data[3]) == 3 else (None, 3)
    return data[end:], bulletin, data[1], data[2], correction


def _spacetime(
    data: list[str],
) -> tuple[list[str], str, str, str | None, str, str | None]:
    area = data.pop(0)
    # Skip airmet type + time repeat
    if data[0] == "WA" and data[1].isdigit():
        data = data[2:]
        area = area[:-1]  # Remove type label from 3-letter ident
    valid_index = data.index("VALID")
    report_type = " ".join(data[:valid_index])
    data = data[valid_index + 1 :]
    if data[0] == "UNTIL":
        start_time = None
        end_time = data[1]
        data = data[2:]
    else:
        target = "-" if "-" in data[0] else "/"
        start_time, end_time = data.pop(0).split(target)
    # KMCO- ORL FIR
    if data[0][-1] == "-":
        station = data.pop(0)[:-1]
    # KMCO - KMCO
    elif data[1] == "-" and len(data[0]) == 4:
        station = data.pop(0)
        data.pop(0)
    else:
        station = None
    return data, area, report_type, start_time, end_time, station


def _first_index(data: list[str], *targets: str) -> int:
    for target in targets:
        with suppress(ValueError):
            return data.index(target)
    return -1


def _region(data: list[str]) -> tuple[list[str], str]:
    # FIR/CTA region name
    # Or non-standard name using lookahead Ex: FL CSTL WTRS FROM 100SSW
    name_end = _first_index(data, "FIR", "CTA") + 1 or _first_index(data, "FROM")
    # State list
    if not name_end:
        for item in data:
            if len(item) == 2:
                name_end += 1
            else:
                break
    name = " ".join(data[:name_end])
    return data[name_end:], name


def _time(data: list[str], issued: date | None = None) -> tuple[list[str], Timestamp | None, Timestamp | None]:
    """Extracts the start and/or end time based on a couple starting elements"""
    index = _first_index(data, "AT", "FCST", "UNTIL", "VALID", "OUTLOOK", "OTLK")
    if index == -1:
        return data, None, None
    start_item = data.pop(index)
    start, end, observed = None, None, None
    if "-" in data[index]:
        start_item, end_item = data.pop(index).split("-")
        start = core.make_timestamp(start_item, time_only=len(start_item) < 6, target_date=issued)
        end = core.make_timestamp(end_item, time_only=len(end_item) < 6, target_date=issued)
    elif len(data[index]) >= 4 and data[index][:4].isdigit():
        observed = core.make_timestamp(data.pop(index), time_only=True, target_date=issued)
        if index > 0 and data[index - 1] == "OBS":
            data.pop(index - 1)
    for remv in ("FCST", "OUTLOOK", "OTLK", "VALID"):
        with suppress(ValueError):
            data.remove(remv)
    if observed:
        if start_item in ("UNTIL", "VALID"):
            end = observed
        else:
            start = observed
    return data, start, end


def _coord_value(value: str) -> float:
    if value[0] in ("N", "S"):
        index, strip, replace = 3, "N", "S"
    else:
        index, strip, replace = 4, "E", "W"
    num = f"{value[:index]}.{value[index:]}".lstrip(strip).replace(replace, "-")
    return float(num)


def _position(data: list[str]) -> tuple[list[str], Coord | None]:
    try:
        index = data.index("PSN")
    except ValueError:
        return data, None
    data.pop(index)
    raw = f"{data[index]} {data[index + 1]}"
    lat = _coord_value(data.pop(index))
    lon = _coord_value(data.pop(index))
    return data, Coord(lat=lat, lon=lon, repr=raw)


def _movement(data: list[str], units: Units) -> tuple[list[str], Units, Movement | None]:
    with suppress(ValueError):
        data.remove("STNR")
        speed = core.make_number("STNR")
        return data, units, Movement(repr="STNR", direction=None, speed=speed)
    try:
        index = data.index("MOV")
    except ValueError:
        return data, units, None
    raw = data.pop(index)
    direction_str = data.pop(index)
    # MOV CNL
    if direction_str == "CNL":
        return data, units, None
    raw += f" {direction_str} "
    # MOV FROM 23040KT
    if direction_str == "FROM":
        value = data[index][:3]
        raw += value
        direction = core.make_number(value)
        data[index] = data[index][3:]
    # MOV E 45KMH
    else:
        direction = core.make_number(direction_str.replace("/", ""), literal=True, special=CARDINAL_DEGREES)
    speed = None
    with suppress(IndexError):
        kt_unit, kmh_unit = data[index].endswith("KT"), data[index].endswith("KMH")
        if kt_unit or kmh_unit:
            units.wind_speed = "kmh" if kmh_unit else "kt"
            speed_str = data.pop(index)
            raw += speed_str
            # Remove bottom speed Ex: MOV W 05-10KT
            if "-" in speed_str:
                speed_str = speed_str[speed_str.find("-") + 1 :]
            speed = core.make_number(speed_str[: -3 if kmh_unit else -2])
    return data, units, Movement(repr=raw.strip(), direction=direction, speed=speed)


def _info_from_match(match: re.Match, start: int) -> tuple[str, int]:
    """Returns the matching text and starting location if none yet available"""
    if start == -1:
        start = match.start()
    return match.group(), start


def _pre_break(report: str) -> str:
    break_index = report.find(" <break> ")
    return report[:break_index] if break_index != -1 else report


def _bounds_from_latterals(report: str, start: int) -> tuple[str, list[str], int]:
    """Extract coordinate latterals from report Ex: N OF N2050"""
    bounds = []
    for match in _LATTERAL_PATTERN.finditer(_pre_break(report)):
        group, start = _info_from_match(match, start)
        bounds.append(group.removesuffix(" AND"))
        report = report.replace(group, " ")
    return report, bounds, start


def _coords_from_text(report: str, start: int) -> tuple[str, list[Coord], int]:
    """Extract raw coordinate values from report Ex: N4409 E01506"""
    coords = []
    for match in _COORD_PATTERN.finditer(_pre_break(report)):
        group, start = _info_from_match(match, start)
        text = group.strip(" -")
        lat, lon = text.split()
        coord = Coord(lat=_coord_value(lat), lon=_coord_value(lon), repr=text)
        coords.append(coord)
        report = report.replace(group, " ")
    return report, coords, start


def _coords_from_navaids(report: str, start: int) -> tuple[str, list[Coord], int]:
    """Extract navaid referenced coordinates from report Ex: 30SSW BNA"""
    coords, navs = [], []
    for match in _NAVAID_PATTERN.finditer(_pre_break(report)):
        group, start = _info_from_match(match, start)
        report = report.replace(group, " ")
        group = group.strip("-").removeprefix("FROM ").removeprefix("TO ")
        navs.append((group, *group.split()))
    locs = to_coordinates([n[2 if len(n) == 3 else 1] for n in navs])
    for i, nav in enumerate(navs):
        value = nav[0]
        if len(nav) == 3:
            vector, num_index = nav[1], 0
            while vector[num_index].isdigit():
                num_index += 1
            distance, bearing = (
                int(vector[:num_index]),
                CARDINAL_DEGREES[vector[num_index:]],
            )
            loc = geo_distance(nautical=distance).destination(locs[i].pair, bearing=bearing)
            coord = Coord(lat=loc.latitude, lon=loc.longitude, repr=value)
        else:
            coord = locs[i]
            coord.repr = value
        coords.append(coord)
    return report, coords, start


def _bounds(data: list[str]) -> tuple[list[str], list[Coord], list[str]]:
    """Extract coordinate bounds by coord, navaid, and latterals"""
    report, start = " ".join(data), -1
    report, bounds, start = _bounds_from_latterals(report, start)
    report, coords, start = _coords_from_text(report, start)
    report, navs, start = _coords_from_navaids(report, start)
    coords += navs
    for target in ("FROM", "WI", "BOUNDED", "OBS"):
        index = report.find(f"{target} ")
        if index != -1 and index < start:
            start = index
    report = report[:start] + report[report.rfind("  ") :]
    data = [s for s in report.split() if s]
    return data, coords, bounds


def _altitudes(data: list[str], units: Units) -> tuple[list[str], Units, Number | None, Number | None]:
    """Extract the floor and ceiling altitudes"""
    floor, ceiling = None, None
    for i, item in enumerate(data):
        # BTN FL180 AND FL330
        if item == "BTN" and len(data) > i + 2 and data[i + 2] == "AND":
            floor, units = core.make_altitude(data[i + 1], units)
            ceiling, units = core.make_altitude(data[i + 3], units)
            data = data[:i] + data[i + 4 :]
            break
        # TOPS ABV FL450
        if item in ("TOP", "TOPS", "BLW"):
            if data[i + 1] == "ABV":
                ceiling = core.make_number(f"ABV {data[i + 2]}")
                data = data[:i] + data[i + 3 :]
                break
            if data[i + 1] == "BLW":
                ceiling = core.make_number(f"BLW {data[i + 2]}")
                data = data[:i] + data[i + 3 :]
                break
            # TOPS TO FL310
            if data[i + 1] == "TO":
                data.pop(i)
            ceiling, units = core.make_altitude(data[i + 1], units)
            data = data[:i] + data[i + 2 :]
            # CIG BLW 010
            if data[i - 1] == "CIG":
                data.pop(i - 1)
            break
        # FL060/300 SFC/FL160
        if core.is_altitude(item):
            if "/" in item:
                floor_val, ceiling_val = item.split("/")
                floor, units = core.make_altitude(floor_val, units)
                if (floor_val == "SFC" or floor_val[:2] == "FL") and ceiling_val[:2] != "FL":
                    ceiling, units = core.make_altitude(ceiling_val, units, force_fl=True)
                else:
                    ceiling, units = core.make_altitude(ceiling_val, units)
            else:
                ceiling, units = core.make_altitude(item, units)
            data.pop(i)
            break
    return data, units, floor, ceiling


def _weather_type(data: list[str]) -> tuple[list[str], Code | None]:
    weather = None
    report = " ".join(data)
    for key, val in WEATHER_TYPES.items():
        if key in report:
            weather = Code(repr=key, value=val)
            data = [i for i in report.replace(key, "").split() if i]
            break
    return data, weather


def _intensity(data: list[str]) -> tuple[list[str], Code | None]:
    if not data:
        return data, None
    try:
        value = INTENSITY[data[-1]]
        code = data.pop()
        return data, Code(repr=code, value=value)
    except KeyError:
        return data, None


def _sigmet_observation(data: list[str], units: Units, issued: date | None = None) -> tuple[AirSigObservation, Units]:
    data, start_time, end_time = _time(data, issued)
    data, position = _position(data)
    data, coords, bounds = _bounds(data)
    data, units, movement = _movement(data, units)
    data, intensity = _intensity(data)
    data, units, floor, ceiling = _altitudes(data, units)
    data, weather = _weather_type(data)
    struct = AirSigObservation(
        type=weather,
        start_time=start_time,
        end_time=end_time,
        position=position,
        floor=floor,
        ceiling=ceiling,
        coords=coords,
        bounds=bounds,
        movement=movement,
        intensity=intensity,
        other=_clean_flags(data),
    )
    return struct, units


def _observations(
    data: list[str], units: Units, issued: date | None = None
) -> tuple[Units, AirSigObservation | None, AirSigObservation | None]:
    observation, forecast, forecast_index = None, None, -1
    forecast_index = _first_index(data, "FCST", "OUTLOOK", "OTLK")
    if forecast_index == -1:
        observation, units = _sigmet_observation(data, units, issued)
    # 6 is arbitrary. Will likely change or be more precise later
    elif forecast_index < 6:
        forecast, units = _sigmet_observation(data, units, issued)
    else:
        observation, units = _sigmet_observation(data[:forecast_index], units, issued)
        forecast, units = _sigmet_observation(data[forecast_index:], units, issued)
    return units, observation, forecast


_REPLACE = {
    " MO V ": " MOV ",
    " STNRY": " STNR",
    " STCNRY": " STNR",
    " N-NE ": " NNE ",
    " N-NW ": " NNW ",
    " E-NE ": " ENE ",
    " E-SE ": " ESE ",
    " S-SE ": " SSE ",
    " S-SW ": " SSW ",
    " W-SW ": " WSW ",
    " W-NW ": " WNW ",
}


def _find_first_digit(item: str) -> int:
    return next((i for i, char in enumerate(item) if char.isdigit()), -1)


def sanitize(report: str) -> str:
    """Sanitized AIRMET / SIGMET report string"""
    report = report.strip(" =")
    for key, val in _REPLACE.items():
        report = report.replace(key, val)
    data = report.split()
    for i, item in reversed(list(enumerate(data))):
        # Remove extra element on altitude Ex: FL450Z skip 1000FT
        if (
            len(item) > 4
            and not item[-1].isdigit()
            and item[-2:] != "FT"
            and item[-1] != "M"
            and core.is_altitude(item[:-1])
        ):
            data[i] = item[:-1]
        # Split attached movement direction Ex: NE05KT
        if len(item) >= 4 and item.endswith(("KT", "KMH")) and item[: _find_first_digit(item)] in CARDINALS:
            index = _find_first_digit(item)
            direction = item[:index]
            data.insert(i + 1, item[index:])
            data[i] = direction
    return " ".join(data)


def parse(report: str, issued: date | None = None) -> tuple[AirSigmetData, Units]:
    """Parse AIRMET / SIGMET report string"""
    units = Units.international()
    sanitized = sanitize(report)
    data, bulletin, issuer, time, correction = _header(_parse_prep(sanitized))
    data, area, report_type, start_time, end_time, station = _spacetime(data)
    body = sanitized[sanitized.find(" ".join(data[:2])) :]
    # Trim AIRMET type
    if data[0] == "AIRMET":
        with suppress(ValueError):
            data = data[data.index("<elip>") + 1 :]
    data, region = _region(data)
    units, observation, forecast = _observations(data, units, issued)
    struct = AirSigmetData(
        raw=report,
        sanitized=sanitized,
        station=station,
        time=core.make_timestamp(time, target_date=issued),
        remarks=None,
        bulletin=bulletin,
        issuer=issuer,
        correction=correction,
        area=area,
        type=report_type,
        start_time=core.make_timestamp(start_time, target_date=issued),
        end_time=core.make_timestamp(end_time, target_date=issued),
        body=body,
        region=region,
        observation=observation,
        forecast=forecast,
    )
    return struct, units
