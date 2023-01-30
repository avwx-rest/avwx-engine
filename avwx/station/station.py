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
import httpx
from geopy.distance import great_circle, Distance  # type: ignore

# module
from avwx.exceptions import BadStation
from avwx.load_utils import LazyCalc
from avwx.station.meta import STATIONS
from avwx.structs import Coord


def get_ip_location() -> Coord:
    """Returns the current location according to ipinfo.io"""
    lat, lon = httpx.get("https://ipinfo.io/loc").text.strip().split(",")
    return Coord(float(lat), float(lon))


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
_ICAO = LazyCalc(lambda: {v["icao"]: k for k, v in STATIONS.items() if v["icao"]})
_IATA = LazyCalc(lambda: {v["iata"]: k for k, v in STATIONS.items() if v["iata"]})
_GPS = LazyCalc(lambda: {v["gps"]: k for k, v in STATIONS.items() if v["gps"]})
_LOCAL = LazyCalc(lambda: {v["local"]: k for k, v in STATIONS.items() if v["local"]})


@dataclass
class Station:
    """Stores basic station information"""

    # pylint: disable=too-many-instance-attributes

    city: Optional[str]
    country: str
    elevation_ft: Optional[int]
    elevation_m: Optional[int]
    gps: Optional[str]
    iata: Optional[str]
    icao: Optional[str]
    latitude: float
    local: Optional[str]
    longitude: float
    name: str
    note: Optional[str]
    reporting: bool
    runways: List[Runway]
    state: Optional[str]
    type: str
    website: Optional[str]
    wiki: Optional[str]

    @classmethod
    def _from_code(cls: Type[T], ident: str) -> T:
        try:
            info: Dict[str, Any] = copy(STATIONS[ident])
            if info["runways"]:
                info["runways"] = [Runway(**r) for r in info["runways"]]
            return cls(**info)
        except (KeyError, AttributeError) as not_found:
            raise BadStation(
                f"Could not find station with ident {ident}"
            ) from not_found

    @classmethod
    def from_code(cls: Type[T], ident: str) -> T:
        """Load a Station from ICAO, GPS, or IATA code in that order"""
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
        raise BadStation(f"Could not find station with ident {ident}")

    @classmethod
    def from_icao(cls: Type[T], ident: str) -> T:
        """Load a Station from an ICAO station ident"""
        try:
            return cls._from_code(_ICAO.value[ident.upper()])
        except (KeyError, AttributeError) as not_found:
            raise BadStation(
                f"Could not find station with ICAO ident {ident}"
            ) from not_found

    @classmethod
    def from_iata(cls: Type[T], ident: str) -> T:
        """Load a Station from an IATA code"""
        try:
            return cls._from_code(_IATA.value[ident.upper()])
        except (KeyError, AttributeError) as not_found:
            raise BadStation(
                f"Could not find station with IATA ident {ident}"
            ) from not_found

    @classmethod
    def from_gps(cls: Type[T], ident: str) -> T:
        """Load a Station from a GPS code"""
        try:
            return cls._from_code(_GPS.value[ident.upper()])
        except (KeyError, AttributeError) as not_found:
            raise BadStation(
                f"Could not find station with GPS ident {ident}"
            ) from not_found

    @classmethod
    def from_local(cls: Type[T], ident: str) -> T:
        """Load a Station from a local code"""
        try:
            return cls._from_code(_LOCAL.value[ident.upper()])
        except (KeyError, AttributeError) as not_found:
            raise BadStation(
                f"Could not find station with local ident {ident}"
            ) from not_found

    @classmethod
    def nearest(
        cls: Type[T],
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        is_airport: bool = False,
        sends_reports: bool = True,
        max_coord_distance: float = 10,
    ) -> Optional[Tuple[T, dict]]:
        """Load the Station nearest to your location or a lat,lon coordinate pair

        Returns the Station and distances from source

        NOTE: Becomes less accurate toward poles and doesn't cross +/-180
        """
        if not (lat and lon):
            lat, lon = get_ip_location().pair
        ret = nearest(lat, lon, 1, is_airport, sends_reports, max_coord_distance)
        if not isinstance(ret, dict):
            return None
        station = ret.pop("station")
        return station, ret

    @property
    def lookup_code(self) -> str:
        """Returns the ICAO or GPS code for report fetch"""
        if self.icao:
            return self.icao
        if self.gps:
            return self.gps
        raise BadStation("Station does not have a valid lookup code")

    @property
    def storage_code(self) -> str:
        """Returns the first unique-ish code from what's available"""
        if self.icao:
            return self.icao
        if self.iata:
            return self.iata
        if self.gps:
            return self.gps
        if self.local:
            return self.local
        raise BadStation("Station does not have any useable codes")

    @property
    def sends_reports(self) -> bool:
        """Returns whether or not a Station likely sends weather reports"""
        return self.reporting is True

    @property
    def coord(self) -> Coord:
        """Returns the station location as a Coord"""
        return Coord(lat=self.latitude, lon=self.longitude, repr=self.icao)

    def distance(self, lat: float, lon: float) -> Distance:
        """Returns a geopy Distance using the great circle method"""
        return great_circle((lat, lon), (self.latitude, self.longitude))

    def nearby(
        self,
        is_airport: bool = False,
        sends_reports: bool = True,
        max_coord_distance: float = 10,
    ) -> List[Tuple[T, dict]]:
        """Returns Stations nearest to current station and their distances

        NOTE: Becomes less accurate toward poles and doesn't cross +/-180
        """
        stations = nearest(
            self.latitude,
            self.longitude,
            11,
            is_airport,
            sends_reports,
            max_coord_distance,
        )
        if isinstance(stations, dict):
            return []
        return [(s.pop("station"), s) for s in stations[1:]]


# Coordinate search and resources


def _make_coords() -> List[Tuple]:
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
    # pylint: disable=import-outside-toplevel
    try:
        from scipy.spatial import KDTree  # type: ignore

        return KDTree([c[1:] for c in _COORDS.value])
    except (NameError, ModuleNotFoundError) as name_error:
        raise ModuleNotFoundError(
            'scipy must be installed to use coordinate lookup. Run "pip install avwx-engine[scipy]" to enable this feature'
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
        for code, dist in nodes:
            if not code:
                continue
            stn = Station.from_code(code)
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
        stations = [(Station.from_code(code), d) for code, d in data]
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
    ret.sort(key=lambda x: x["miles"])  # type: ignore
    return ret
