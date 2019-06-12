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
        cls, lat: float, lon: float, sends_reports: bool = True
    ) -> ("Station", float):
        """
        Load the Station nearest to a lat,lon coordinate pair

        Returns the Station and coordinate distance from source
        """
        k = 100 if sends_reports else 1
        dist, index = _COORD_TREE.value.query([lat, lon], k)
        if not sends_reports:
            return cls.from_icao(_COORDS.value[index][0]), dist
        for d, i in zip(dist, index):
            stn = cls.from_icao(_COORDS.value[i][0])
            if stn.sends_reports:
                return stn, d

    @property
    def sends_reports(self) -> bool:
        """
        Returns whether or not a Station likely sends weather reports
        """
        return self.iata is not None
