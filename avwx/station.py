"""
Station handling and search
"""

# stdlib
from copy import copy
from dataclasses import dataclass

# module
from avwx.exceptions import BadStation
from avwx.static import NA_REGIONS, IN_REGIONS, M_NA_REGIONS, M_IN_REGIONS
from avwx.structs import _LazyLoad

# We catch this import error only if user attempts coord lookup
try:
    from scipy.spatial import KDTree
except ModuleNotFoundError:
    pass


# Lazy data loading to speed up import times for unused features
_STATIONS = _LazyLoad("stations")


# LazyCalc lets us avoid the global keyword
class _LazyCalc:

    func: "Callable"
    _value: object = None

    def __init__(self, func: "Callable"):
        self.func = func

    @property
    def value(self) -> object:
        if self._value is None:
            self._value = self.func()
        return self._value


def _make_coords():
    return [(s["icao"], s["latitude"], s["longitude"]) for s in _STATIONS.values()]


_COORDS = _LazyCalc(_make_coords)


def _make_coord_tree():
    try:
        return KDTree([c[1:] for c in _COORDS.value])
    except NameError:
        raise ModuleNotFoundError("Scipy must be installed to use coordinate lookup")


_COORD_TREE = _LazyCalc(_make_coord_tree)


def uses_na_format(station: str) -> bool:
    """
    Returns True if the station uses the North American format,
    False if the International format
    """
    if station[0] in NA_REGIONS:
        return True
    elif station[0] in IN_REGIONS:
        return False
    elif station[:2] in M_NA_REGIONS:
        return True
    elif station[:2] in M_IN_REGIONS:
        return False
    raise BadStation("Station doesn't start with a recognized character set")


def valid_station(station: str):
    """
    Checks the validity of a station ident

    This function doesn't return anything. It merely raises a BadStation error if needed
    """
    station = station.strip()
    if len(station) != 4:
        raise BadStation("ICAO station idents must be four characters long")
    uses_na_format(station)


@dataclass
class Runway(object):
    length_ft: int
    width_ft: int
    ident1: str
    ident2: str


@dataclass
class Station(object):
    """
    Stores basic station information
    """

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
    runways: [Runway]
    state: str
    type: str
    website: str
    wiki: str

    @classmethod
    def from_icao(cls, ident: str) -> "Station":
        """
        Load a Station from an ICAO station ident
        """
        try:
            info = copy(_STATIONS[ident.upper()])
            if info["runways"]:
                info["runways"] = [Runway(**r) for r in info["runways"]]
            return cls(**info)
        except (KeyError, AttributeError):
            raise BadStation(f"Could not find station with ident {ident}")

    @classmethod
    def nearest(
        cls,
        lat: float,
        lon: float,
        sends_reports: bool = True,
        max_distance: float = 50,
    ) -> ("Station", float):
        """
        Load the Station nearest to a lat,lon coordinate pair

        Returns the Station and coordinate distance from source
        """
        return nearest(lat, lon, 1, sends_reports, max_distance)

    @property
    def sends_reports(self) -> bool:
        """
        Returns whether or not a Station likely sends weather reports
        """
        return self.iata is not None


def _query_coords(lat: float, lon: float, n: int, d: float) -> [(str, float)]:
    """
    Returns <= n number of ident, dist tuples <= d distance from lat, lon
    """
    dist, index = _COORD_TREE.value.query([lat, lon], n, distance_upper_bound=d)
    if n == 1:
        dist, index = [dist], [index]
    # NOTE: index == len of list means Tree ran out of items
    return [
        (_COORDS.value[i][0], d) for i, d in zip(index, dist) if i < len(_COORDS.value)
    ]


def _n_reporting(lat: float, lon: float, n: int, d: float) -> (str, float):
    """
    Returns <= n number of reporting stations <= d distance from lat,lon
    """
    k = n * 20
    last = 0
    stations = []
    while True:
        nodes = _query_coords(lat, lon, k, d)[last:]
        # Ran out of new stations
        if not nodes:
            return stations
        for icao, d in nodes:
            stn = Station.from_icao(icao)
            if stn.sends_reports:
                stations.append((stn, d))
            # Reached the desired number of stations
            if len(stations) >= n:
                return stations
        last = k
        k += n * 100


def nearest(
    lat: float,
    lon: float,
    n: int = 1,
    sends_reports: bool = True,
    max_distance: float = 10,
) -> (str, float):
    """
    Returns the nearest n Stations to a lat,lon coordinate pair

    Returns the Station and coordinate distance from source
    """
    if not sends_reports:
        stations = _query_coords(lat, lon, n, max_distance)
        stations = [(Station.from_icao(icao), d) for icao, d in stations]
    else:
        stations = _n_reporting(lat, lon, n, max_distance)
    return stations[0] if n == 1 else stations
