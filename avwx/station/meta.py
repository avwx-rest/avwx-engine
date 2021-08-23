"""
Shared list and metadata
"""

# stdlib
from functools import lru_cache
from typing import List

# module
from avwx.exceptions import BadStation
from avwx.load_utils import LazyLoad
from avwx.static.core import IN_REGIONS, M_IN_REGIONS, M_NA_REGIONS, NA_REGIONS

__LAST_UPDATED__ = "2021-08-22"

# Lazy data loading to speed up import times for unused features
STATIONS = LazyLoad("stations")

# maxsize = 2 ** number of boolean options
@lru_cache(maxsize=2)
def station_list(reporting: bool = True) -> List[str]:
    """Returns a list of station idents matching the search criteria"""
    stations = []
    for icao, station in STATIONS.items():
        if not reporting or station["reporting"]:
            stations.append(icao)
    return stations


def uses_na_format(station: str) -> bool:
    """Returns True if the station uses the North American format,

    False if the International format
    """
    if station[0] in NA_REGIONS:
        return True
    if station[0] in IN_REGIONS:
        return False
    if station[:2] in M_NA_REGIONS:
        return True
    if station[:2] in M_IN_REGIONS:
        return False
    raise BadStation("Station doesn't start with a recognized character set")


def valid_station(station: str):
    """Checks the validity of a station ident

    This function doesn't return anything. It merely raises a BadStation error if needed
    """
    station = station.strip()
    if len(station) != 4:
        raise BadStation("ICAO station ident must be four characters long")
    uses_na_format(station)
