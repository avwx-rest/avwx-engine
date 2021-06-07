"""
Station handling and coordinate search
"""

# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes

# stdlib
from contextlib import suppress
from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

# library
from geopy.distance import great_circle, Distance  # type: ignore

# module
from avwx.exceptions import BadStation
from avwx.load_utils import LazyCalc
from avwx.station.meta import STATIONS

# We catch this import error only if user attempts coord lookup
with suppress(ModuleNotFoundError):
    from scipy.spatial import KDTree  # type: ignore


@dataclass
class Runway:
    """Represents a runway at an airport"""

    length_ft: int
    width_ft: int
    surface: str
    lights: bool
    ident1: str
    ident2: str
    bearing1: float
    bearing2: float


T = TypeVar("T", bound="Station")
_IATAS = LazyCalc(lambda: {v["iata"]: k for k, v in STATIONS.items() if v["iata"]})


@dataclass
class Station:
    """Stores basic station information"""

    # pylint: disable=too-many-instance-attributes

    city: str
    country: str
    elevation_ft: int
    elevation_m: int
    iata: str
    icao: str
    latitude: float
    longitude: float
    name: str
    note: str
    reporting: bool
    runways: List[Runway]
    state: str
    type: str
    website: str
    wiki: str

    @classmethod
    def from_icao(cls: Type[T], ident: str) -> T:
        """Load a Station from an ICAO station ident"""
        try:
            info: Dict[str, Any] = copy(STATIONS[ident.upper()])
            if info["runways"]:
                info["runways"] = [Runway(**r) for r in info["runways"]]
            return cls(**info)
        except (KeyError, AttributeError) as not_found:
            raise BadStation(
                f"Could not find station with ICAO ident {ident}"
            ) from not_found

    @classmethod
    def from_iata(cls: Type[T], ident: str) -> T:
        """Load a Station from an IATA code"""
        try:
            return cls.from_icao(_IATAS.value[ident.upper()])
        except (KeyError, AttributeError) as not_found:
            raise BadStation(
                f"Could not find station with ICAO ident {ident}"
            ) from not_found

    @classmethod
    def nearest(
        cls: Type[T],
        lat: float,
        lon: float,
        is_airport: bool = False,
        sends_reports: bool = True,
        max_coord_distance: float = 10,
    ) -> Optional[Tuple[T, dict]]:
        """Load the Station nearest to a lat,lon coordinate pair

        Returns the Station and distances from source

        NOTE: Becomes less accurate toward poles and doesn't cross +/-180
        """
        ret = nearest(lat, lon, 1, is_airport, sends_reports, max_coord_distance)
        if not isinstance(ret, dict):
            return None
        station = ret.pop("station")
        return station, ret

    @property
    def sends_reports(self) -> bool:
        """Returns whether or not a Station likely sends weather reports"""
        return self.reporting is True

    def distance(self, lat: float, lon: float) -> Distance:
        """Returns a geopy Distance using the great circle method"""
        return great_circle((lat, lon), (self.latitude, self.longitude))


# Coordinate search and resources


def _make_coords():
    return [(s["icao"], s["latitude"], s["longitude"]) for s in STATIONS.values()]


_COORDS = LazyCalc(_make_coords)


def _make_coord_tree():
    try:
        return KDTree([c[1:] for c in _COORDS.value])
    except NameError as name_error:
        raise ModuleNotFoundError(
            "scipy must be installed to use coordinate lookup"
        ) from name_error


_COORD_TREE = LazyCalc(_make_coord_tree)


def _query_coords(lat: float, lon: float, n: int, d: float) -> List[Tuple[str, float]]:
    """Returns <= n number of ident, dist tuples <= d coord distance from lat,lon"""
    dist, index = _COORD_TREE.value.query([lat, lon], n, distance_upper_bound=d)
    if n == 1:
        dist, index = [dist], [index]
    # NOTE: index == len of list means Tree ran out of items
    return [
        (_COORDS.value[i][0], d) for i, d in zip(index, dist) if i < len(_COORDS.value)
    ]


def station_filter(station: Station, is_airport: bool, reporting: bool) -> bool:
    """Return True if station matches given criteria"""
    if is_airport and "airport" not in station.type:
        return False
    if reporting and not station.sends_reports:
        return False
    return True


@lru_cache(maxsize=128)
def _query_filter(
    lat: float, lon: float, n: int, d: float, is_airport: bool, reporting: bool
) -> List[Tuple[Station, float]]:
    """Returns <= n number of stations <= d distance from lat,lon matching the query params"""
    k = n * 20
    last = 0
    stations: List[Tuple[Station, float]] = []
    while True:
        nodes = _query_coords(lat, lon, k, d)[last:]
        # Ran out of new stations
        if not nodes:
            return stations
        for icao, dist in nodes:
            stn = Station.from_icao(icao)
            if station_filter(stn, is_airport, reporting):
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
    is_airport: bool = False,
    sends_reports: bool = True,
    max_coord_distance: float = 10,
) -> Union[dict, List[dict]]:
    """Finds the nearest n Stations to a lat,lon coordinate pair

    Returns the Station and coordinate distance from source

    NOTE: Becomes less accurate toward poles and doesn't cross +/-180
    """
    # Default state includes all, no filtering necessary
    if not (is_airport or sends_reports):
        data = _query_coords(lat, lon, n, max_coord_distance)
        stations = [(Station.from_icao(icao), d) for icao, d in data]
    else:
        stations = _query_filter(
            lat, lon, n, max_coord_distance, is_airport, sends_reports
        )
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
