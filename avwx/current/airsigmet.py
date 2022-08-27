"""
AIRMET / SIGMET report parsing
"""

# stdlib
import asyncio as aio
import re
from contextlib import suppress
from datetime import date, datetime, timezone
from itertools import chain
from typing import List, Optional, Tuple

# library
from geopy.distance import distance as geo_distance  # type: ignore

# module
from avwx import exceptions
from avwx.base import AVWXBase
from avwx.flight_path import to_coordinates
from avwx.load_utils import LazyLoad
from avwx.parsing import core
from avwx.service.bulk import NOAA_Bulk, NOAA_Intl, Service
from avwx.static.core import CARDINAL_DEGREES, CARDINALS, IN_UNITS
from avwx.static.airsigmet import BULLETIN_TYPES, INTENSITY, WEATHER_TYPES
from avwx.structs import (
    AirSigmetData,
    Bulletin,
    Code,
    Coord,
    Movement,
    Number,
    AirSigObservation,
    Timestamp,
    Units,
)

try:
    from shapely.geometry import LineString  # type: ignore
except ModuleNotFoundError:
    LineString = None  # pylint: disable=invalid-name

# N1429 W09053 - N1427 W09052 - N1411 W09139 - N1417 W09141
_COORD_PATTERN = re.compile(r"\b[NS]\d{4} [EW]\d{5}\b( -)?")

# FROM 60NW ISN-INL-TVC-GIJ-UIN-FSD-BIL-60NW ISN
# FROM 70SSW ISN TO 20NNW FAR TO 70E DLH TO 40SE EAU TO 80SE RAP TO 40NNW BFF TO 70SSW
_NAVAID_PATTERN = re.compile(
    r"\b(\d{1,3}[NESW]{1,3} [A-z]{3}-?\b)|((-|(TO )|(FROM ))[A-z]{3}\b)"
)

# N OF N2050 AND S OF N2900
_LATTERAL_PATTERN = re.compile(
    r"\b([NS] OF [NS]\d{2,4})|([EW] OF [EW]\d{3,5})( AND)?\b"
)

NAVAIDS = LazyLoad("navaids")

# Used to assist parsing after sanitized. Removed after parse
_FLAGS = {
    "...": " <elip> ",
    "..": " <elip> ",
    ". ": " <break> ",
    "/VIS ": " <vis> VIS ",
}


def _parse_prep(report: str) -> List[str]:
    """Prepares sanitized string by replacing elements with flags"""
    report = report.rstrip(".")
    for key, val in _FLAGS.items():
        report = report.replace(key, val)
    return report.split()


def _clean_flags(data: List[str]) -> List[str]:
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


def _header(data: List[str]) -> Tuple[List[str], Bulletin, str, str, Optional[str]]:
    bulletin = _bulletin(data[0])
    correction, end = None, 3
    if len(data[3]) == 3:
        correction, end = data[3], 4
    return data[end:], bulletin, data[1], data[2], correction


def _spacetime(
    data: List[str],
) -> Tuple[List[str], str, str, Optional[str], str, Optional[str]]:
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


def _first_index(data: List[str], *targets: str) -> int:
    for target in targets:
        with suppress(ValueError):
            return data.index(target)
    return -1


def _region(data: List[str]) -> Tuple[List[str], str]:
    # FIR/CTA region name
    name_end = _first_index(data, "FIR", "CTA") + 1
    # Non-standard name using lookahead Ex: FL CSTL WTRS FROM 100SSW
    if not name_end:
        name_end = _first_index(data, "FROM")
    # State list
    if not name_end:
        for item in data:
            if len(item) == 2:
                name_end += 1
            else:
                break
    name = " ".join(data[:name_end])
    return data[name_end:], name


def _time(
    data: List[str], issued: Optional[date] = None
) -> Tuple[List[str], Optional[Timestamp], Optional[Timestamp]]:
    """Extracts the start and/or end time based on a couple starting elements"""
    index = _first_index(data, "AT", "FCST", "UNTIL", "VALID", "OUTLOOK", "OTLK")
    if index == -1:
        return data, None, None
    start_item = data.pop(index)
    start, end, observed = None, None, None
    if "-" in data[index]:
        start_item, end_item = data.pop(index).split("-")
        start = core.make_timestamp(
            start_item, time_only=len(start_item) < 6, target_date=issued
        )
        end = core.make_timestamp(
            end_item, time_only=len(end_item) < 6, target_date=issued
        )
    elif len(data[index]) >= 4 and data[index][:4].isdigit():
        observed = core.make_timestamp(
            data.pop(index), time_only=True, target_date=issued
        )
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


def _position(data: List[str]) -> Tuple[List[str], Optional[Coord]]:
    try:
        index = data.index("PSN")
    except ValueError:
        return data, None
    data.pop(index)
    raw = f"{data[index]} {data[index + 1]}"
    lat = _coord_value(data.pop(index))
    lon = _coord_value(data.pop(index))
    return data, Coord(lat=lat, lon=lon, repr=raw)


def _movement(
    data: List[str], units: Units
) -> Tuple[List[str], Units, Optional[Movement]]:
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
    raw += " " + direction_str + " "
    # MOV FROM 23040KT
    if direction_str == "FROM":
        value = data[index][:3]
        raw += value
        direction = core.make_number(value)
        data[index] = data[index][3:]
    # MOV E 45KMH
    else:
        direction = core.make_number(
            direction_str.replace("/", ""), literal=True, special=CARDINAL_DEGREES
        )
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


def _info_from_match(match: re.Match, start: int) -> Tuple[str, int]:
    """Returns the matching text and starting location if none yet available"""
    if start == -1:
        start = match.start()
    return match.group(), start


def _pre_break(report: str) -> str:
    break_index = report.find(" <break> ")
    if break_index != -1:
        return report[:break_index]
    return report


def _bounds_from_latterals(report: str, start: int) -> Tuple[str, List[str], int]:
    """Extract coordinate latterals from report Ex: N OF N2050"""
    bounds = []
    for match in _LATTERAL_PATTERN.finditer(_pre_break(report)):
        group, start = _info_from_match(match, start)
        # post 3.8 bounds.append(group.removesuffix(" AND"))
        if group.endswith(" AND"):
            group = group[:-4]
        bounds.append(group)
        report = report.replace(group, " ")
    return report, bounds, start


def _coords_from_text(report: str, start: int) -> Tuple[str, List[Coord], int]:
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


def _coords_from_navaids(report: str, start: int) -> Tuple[str, List[Coord], int]:
    """Extract navaid referenced coordinates from report Ex: 30SSW BNA"""
    # pylint: disable=too-many-locals
    coords, navs = [], []
    for match in _NAVAID_PATTERN.finditer(_pre_break(report)):
        group, start = _info_from_match(match, start)
        report = report.replace(group, " ")
        group = group.strip("-")  # post 3.8 .removeprefix("FROM ").removeprefix("TO ")
        for end in ("FROM", "TO"):
            if group.startswith(end + " "):
                group = group[(len(end) + 1) :]
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
            loc = geo_distance(nautical=distance).destination(
                locs[i].pair, bearing=bearing
            )
            coord = Coord(lat=loc.latitude, lon=loc.longitude, repr=value)
        else:
            coord = locs[i]
            coord.repr = value
        coords.append(coord)
    return report, coords, start


def _bounds(data: List[str]) -> Tuple[List[str], List[Coord], List[str]]:
    """Extract coordinate bounds by coord, navaid, and latterals"""
    report, start = " ".join(data), -1
    report, bounds, start = _bounds_from_latterals(report, start)
    report, coords, start = _coords_from_text(report, start)
    report, navs, start = _coords_from_navaids(report, start)
    coords += navs
    for target in ("FROM", "WI", "BOUNDED", "OBS"):
        index = report.find(target + " ")
        if index != -1 and index < start:
            start = index
    report = report[:start] + report[report.rfind("  ") :]
    data = [s for s in report.split() if s]
    return data, coords, bounds


def _altitudes(
    data: List[str], units: Units
) -> Tuple[List[str], Units, Optional[Number], Optional[Number]]:
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
                ceiling = core.make_number("ABV " + data[i + 2])
                data = data[:i] + data[i + 3 :]
                break
            if data[i + 1] == "BLW":
                ceiling = core.make_number("BLW " + data[i + 2])
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
                if (floor_val == "SFC" or floor_val[:2] == "FL") and ceiling_val[
                    :2
                ] != "FL":
                    ceiling, units = core.make_altitude(
                        ceiling_val, units, force_fl=True
                    )
                else:
                    ceiling, units = core.make_altitude(ceiling_val, units)
            else:
                ceiling, units = core.make_altitude(item, units)
            data.pop(i)
            break
    return data, units, floor, ceiling


def _weather_type(data: List[str]) -> Tuple[List[str], Optional[Code]]:
    weather = None
    report = " ".join(data)
    for key, val in WEATHER_TYPES.items():
        if key in report:
            weather = Code(repr=key, value=val)
            data = [i for i in report.replace(key, "").split() if i]
            break
    return data, weather


def _intensity(data: List[str]) -> Tuple[List[str], Optional[Code]]:
    if not data:
        return data, None
    try:
        value = INTENSITY[data[-1]]
        code = data.pop()
        return data, Code(repr=code, value=value)
    except KeyError:
        return data, None


def _sigmet_observation(
    data: List[str], units: Units, issued: Optional[date] = None
) -> Tuple[AirSigObservation, Units]:
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
    data: List[str], units: Units, issued: Optional[date] = None
) -> Tuple[Units, Optional[AirSigObservation], Optional[AirSigObservation]]:
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
    for i, char in enumerate(item):
        if char.isdigit():
            return i
    return -1


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
        if (
            len(item) > 4
            and (item.endswith("KT") or item.endswith("KMH"))
            and item[: _find_first_digit(item)] in CARDINALS
        ):
            index = _find_first_digit(item)
            direction = item[:index]
            data.insert(i + 1, item[index:])
            data[i] = direction
    return " ".join(data)


def parse(report: str, issued: Optional[date] = None) -> Tuple[AirSigmetData, Units]:
    """Parse AIRMET / SIGMET report string"""
    # pylint: disable=too-many-locals
    units = Units(**IN_UNITS)
    sanitized = sanitize(report)
    data, bulletin, issuer, time, correction = _header(_parse_prep(sanitized))
    data, area, report_type, start_time, end_time, station = _spacetime(data)
    body = sanitized[sanitized.find(" ".join(data[:2])) :]
    # Trim AIRMET type
    if data[0] == "AIRMET":
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


class AirSigmet(AVWXBase):
    """Class representing an AIRMET or SIGMET report"""

    data: Optional[AirSigmetData] = None

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
            raise ModuleNotFoundError("Install avwx-engine[shape] to use this feature")
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
    """Class to fetch and manage AIRMET and SIGMET reports"""

    _services: List[Service]
    _raw: List[Tuple[str, str]]
    last_updated: Optional[datetime] = None
    raw: List[str]
    reports: Optional[List[AirSigmet]] = None

    def __init__(self):  # type: ignore
        self._services = [NOAA_Bulk("airsigmet"), NOAA_Intl("airsigmet")]
        self._raw, self.raw = [], []

    async def _update(
        self, index: int, timeout: int
    ) -> List[Tuple[str, Optional[str]]]:
        source = self._services[index].root
        reports = await self._services[index].async_fetch(timeout=timeout)  # type: ignore
        raw: List[Tuple[str, Optional[str]]] = []
        for report in reports:
            if not report:
                continue
            raw.append((report, source))
        return raw

    def update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """Updates fetched reports and returns whether they've changed"""
        return aio.run(self.async_update(timeout, disable_post))

    async def async_update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """Updates fetched reports and returns whether they've changed"""
        coros = [self._update(i, timeout) for i in range(len(self._services))]
        data = await aio.gather(*coros)
        raw = list(chain.from_iterable(data))
        reports = [i[0] for i in raw]
        changed = raw != self.raw
        if changed:
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
                except Exception as exc:  # pylint: disable=broad-except
                    exceptions.exception_intercept(exc, raw=report)
            self.reports = parsed
        return changed

    def along(self, coords: List[Coord]) -> List[AirSigmet]:
        """Returns available reports the intersect a flight path"""
        if LineString is None:
            raise ModuleNotFoundError("Install avwx-engine[shape] to use this feature")
        if self.reports is None:
            return []
        path = LineString([c.pair for c in coords])
        return [r for r in self.reports if r.intersects(path)]

    def contains(self, coord: Coord) -> List[AirSigmet]:
        """Returns available reports that contain a coordinate"""
        if self.reports is None:
            return []
        return [r for r in self.reports if r.contains(coord)]
