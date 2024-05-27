"""Station handling and coordinate search."""

# stdlib
from __future__ import annotations

from contextlib import suppress
from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

# library
import httpx
from geopy.distance import Distance, great_circle  # type: ignore

# module
from avwx.exceptions import BadStation, MissingExtraModule
from avwx.load_utils import LazyCalc
from avwx.station.meta import STATIONS
from avwx.structs import Coord

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


def _get_ip_location() -> Coord:
    """Return the current location according to ipinfo.io."""
    lat, lon = httpx.get("https://ipinfo.io/loc").text.strip().split(",")
    return Coord(float(lat), float(lon))


@dataclass
class Runway:
    """Represent a runway at an airport."""

    length_ft: int
    width_ft: int
    surface: str
    lights: bool
    ident1: str
    ident2: str
    bearing1: float
    bearing2: float


_ICAO = LazyCalc(lambda: {v["icao"]: k for k, v in STATIONS.items() if v["icao"]})
_IATA = LazyCalc(lambda: {v["iata"]: k for k, v in STATIONS.items() if v["iata"]})
_GPS = LazyCalc(lambda: {v["gps"]: k for k, v in STATIONS.items() if v["gps"]})
_LOCAL = LazyCalc(lambda: {v["local"]: k for k, v in STATIONS.items() if v["local"]})


@dataclass
class Station:
    """
    The Station dataclass stores basic info about the desired station and
    available Runways.

    The easiest way to get a station is to supply the ICAO, IATA, or GPS code.
    The example below uses `from_code` which checks against all three types,
    but you can also use `from_icao`, `from_iata`, or `from_gps` if you know
    what type of code you are using. This can be important if you may be using
    a code used by more than one station depending on the context. ICAO and
    IATA codes are guarenteed unique, but not all airports have them. That
    said, all stations available in AVWX have either an ICAO or GPS code.

    ```python
    >>> from avwx import Station
    >>> klex = Station.from_code("KLEX")
    >>> f"{klex.name} in {klex.city}, {klex.state}"
    'Blue Grass Airport in Lexington, KY'
    >>> coord = round(klex.latitude, 3), round(klex.longitude, 3)
    >>> f"Located at {coord} at {klex.elevation_ft} feet ({klex.elevation_m} meters)"
    'Located at (38.036, -84.606) at 979 feet (298 meters)'
    >>> rw = max(klex.runways, key=lambda r: r.length_ft)
    >>> f"Its longest runway is {rw.ident1}/{rw.ident2} at {rw.length_ft} feet"
    'Its longest runway is 04/22 at 7003 feet'
    ```

    This is also the same information you'd get from calling Report.station.

    ```python
    >>> from avwx import Metar
    >>> klex = Metar('KLEX')
    >>> klex.station.name
    'Blue Grass Airport'
    ```
    """

    city: str | None
    country: str
    elevation_ft: int | None
    elevation_m: int | None
    gps: str | None
    iata: str | None
    icao: str | None
    latitude: float
    local: str | None
    longitude: float
    name: str
    note: str | None
    reporting: bool
    runways: list[Runway]
    state: str | None
    type: str
    website: str | None
    wiki: str | None

    @classmethod
    def _from_code(cls, ident: str) -> Self:
        try:
            info: dict[str, Any] = copy(STATIONS[ident])
            if info["runways"]:
                info["runways"] = [Runway(**r) for r in info["runways"]]
            return cls(**info)
        except (KeyError, AttributeError) as not_found:
            msg = f"Could not find station with ident {ident}"
            raise BadStation(msg) from not_found

    @classmethod
    def from_code(cls, ident: str) -> Self:
        """Load a Station from ICAO, GPS, or IATA code in that order."""
        if ident and isinstance(ident, str):
            if len(ident) == 4:
                with suppress(BadStation):
                    return cls.from_icao(ident)
                with suppress(BadStation):
                    return cls.from_gps(ident)
            if len(ident) == 3:
                with suppress(BadStation):
                    return cls.from_iata(ident)
            with suppress(BadStation):
                return cls.from_local(ident)
        msg = f"Could not find station with ident {ident}"
        raise BadStation(msg)

    @classmethod
    def from_icao(cls, ident: str) -> Self:
        """Load a Station from an ICAO station ident."""
        try:
            return cls._from_code(_ICAO.value[ident.upper()])
        except (KeyError, AttributeError) as not_found:
            msg = f"Could not find station with ICAO ident {ident}"
            raise BadStation(msg) from not_found

    @classmethod
    def from_iata(cls, ident: str) -> Self:
        """Load a Station from an IATA code."""
        try:
            return cls._from_code(_IATA.value[ident.upper()])
        except (KeyError, AttributeError) as not_found:
            msg = f"Could not find station with IATA ident {ident}"
            raise BadStation(msg) from not_found

    @classmethod
    def from_gps(cls, ident: str) -> Self:
        """Load a Station from a GPS code."""
        try:
            return cls._from_code(_GPS.value[ident.upper()])
        except (KeyError, AttributeError) as not_found:
            msg = f"Could not find station with GPS ident {ident}"
            raise BadStation(msg) from not_found

    @classmethod
    def from_local(cls, ident: str) -> Self:
        """Load a Station from a local code."""
        try:
            return cls._from_code(_LOCAL.value[ident.upper()])
        except (KeyError, AttributeError) as not_found:
            msg = f"Could not find station with local ident {ident}"
            raise BadStation(msg) from not_found

    @classmethod
    def nearest(
        cls,
        lat: float | None = None,
        lon: float | None = None,
        *,
        is_airport: bool = False,
        sends_reports: bool = True,
        max_coord_distance: float = 10,
    ) -> tuple[Self, dict] | None:
        """Load the Station nearest to your location or a lat,lon coordinate pair.

        Returns the Station and distances from source.

        NOTE: Becomes less accurate toward poles and doesn't cross +/-180
        """
        if not (lat and lon):
            lat, lon = _get_ip_location().pair
        ret = nearest(
            lat, lon, 1, is_airport=is_airport, sends_reports=sends_reports, max_coord_distance=max_coord_distance
        )
        if not isinstance(ret, dict):
            return None
        station = ret.pop("station")
        return station, ret

    @property
    def lookup_code(self) -> str:
        """The ICAO or GPS code for report fetch."""
        if self.icao:
            return self.icao
        if self.gps:
            return self.gps
        msg = "Station does not have a valid lookup code"
        raise BadStation(msg)

    @property
    def storage_code(self) -> str:
        """The first unique-ish code from what's available."""
        if self.icao:
            return self.icao
        if self.iata:
            return self.iata
        if self.gps:
            return self.gps
        if self.local:
            return self.local
        msg = "Station does not have any useable codes"
        raise BadStation(msg)

    @property
    def sends_reports(self) -> bool:
        """Whether or not a Station likely sends weather reports."""
        return self.reporting is True

    @property
    def coord(self) -> Coord:
        """The station location as a Coord."""
        return Coord(lat=self.latitude, lon=self.longitude, repr=self.icao)

    def distance(self, lat: float, lon: float) -> Distance:
        """Geopy Distance using the great circle method."""
        return great_circle((lat, lon), (self.latitude, self.longitude))

    def nearby(
        self,
        *,
        is_airport: bool = False,
        sends_reports: bool = True,
        max_coord_distance: float = 10,
    ) -> list[tuple[Self, dict]]:
        """Return Stations nearest to current station and their distances.

        NOTE: Becomes less accurate toward poles and doesn't cross +/-180
        """
        stations = nearest(
            self.latitude,
            self.longitude,
            11,
            is_airport=is_airport,
            sends_reports=sends_reports,
            max_coord_distance=max_coord_distance,
        )
        if isinstance(stations, dict):
            return []
        return [(s.pop("station"), s) for s in stations[1:]]


# Coordinate search and resources


def _make_coords() -> list[tuple[str, float, float]]:
    return [
        (
            s["icao"] or s["gps"] or s["iata"] or s["local"],
            s["latitude"],
            s["longitude"],
        )
        for s in STATIONS.values()
    ]


_COORDS = LazyCalc(_make_coords)


def _make_coord_tree():  # type: ignore
    try:
        from scipy.spatial import KDTree  # type: ignore

        return KDTree([c[1:] for c in _COORDS.value])
    except (NameError, ModuleNotFoundError) as name_error:
        extra = "scipy"
        raise MissingExtraModule(extra) from name_error


_COORD_TREE = LazyCalc(_make_coord_tree)


def _query_coords(lat: float, lon: float, n: int, d: float) -> list[tuple[str, float]]:
    """Returns <= n number of ident, dist tuples <= d coord distance from lat,lon"""
    dist, index = _COORD_TREE.value.query([lat, lon], n, distance_upper_bound=d)
    if n == 1:
        dist, index = [dist], [index]
    # NOTE: index == len of list means Tree ran out of items
    return [(_COORDS.value[i][0], d) for i, d in zip(index, dist, strict=True) if i < len(_COORDS.value)]


def station_filter(station: Station, *, is_airport: bool, reporting: bool) -> bool:
    """Return True if station matches given criteria."""
    if is_airport and "airport" not in station.type:
        return False
    return bool(not reporting or station.sends_reports)


@lru_cache(maxsize=128)
def _query_filter(
    lat: float, lon: float, n: int, d: float, *, is_airport: bool, reporting: bool
) -> list[tuple[Station, float]]:
    """Return <= n number of stations <= d distance from lat,lon matching the query params."""
    k = n * 20
    last = 0
    stations: list[tuple[Station, float]] = []
    while True:
        nodes = _query_coords(lat, lon, k, d)[last:]
        # Ran out of new stations
        if not nodes:
            return stations
        for code, dist in nodes:
            if not code:
                continue
            stn = Station.from_code(code)
            if station_filter(stn, is_airport=is_airport, reporting=reporting):
                stations.append((stn, dist))
            # Reached the desired number of stations
            if len(stations) >= n:
                return stations
        last = k
        k += n * 100


def nearest(
    lat: float,
    lon: float,
    n: int = 1,
    *,
    is_airport: bool = False,
    sends_reports: bool = True,
    max_coord_distance: float = 10,
) -> dict | list[dict]:
    """Find the nearest n Stations to a lat,lon coordinate pair.

    Returns the Station and coordinate distance from source.

    NOTE: Becomes less accurate toward poles and doesn't cross +/-180.
    """
    # Default state includes all, no filtering necessary
    if is_airport or sends_reports:
        stations = _query_filter(lat, lon, n, max_coord_distance, is_airport=is_airport, reporting=sends_reports)
    else:
        data = _query_coords(lat, lon, n, max_coord_distance)
        stations = [(Station.from_code(code), d) for code, d in data]
    if not stations:
        return []
    ret = []
    for station, coord_dist in stations:
        dist = station.distance(lat, lon)
        ret.append(
            {
                "station": station,
                "coordinate_distance": coord_dist,
                "nautical_miles": dist.nautical,
                "miles": dist.miles,
                "kilometers": dist.kilometers,
            }
        )
    if n == 1:
        return ret[0]
    ret.sort(key=lambda x: x["miles"])
    return ret
