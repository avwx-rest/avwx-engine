"""Shared list and metadata."""

# stdlib
from __future__ import annotations

from functools import lru_cache

# module
from avwx.exceptions import BadStation
from avwx.load_utils import LazyLoad
from avwx.static.core import IN_REGIONS, M_IN_REGIONS, M_NA_REGIONS, NA_REGIONS

__LAST_UPDATED__ = "2024-10-29"

# Lazy data loading to speed up import times for unused features
STATIONS = LazyLoad("stations")


# maxsize = 2 ** number of boolean options
@lru_cache(maxsize=2)
def station_list(*, reporting: bool = True) -> list[str]:
    """Return a list of station idents matching the search criteria."""
    return [code for code, station in STATIONS.items() if not reporting or station["reporting"]]


def uses_na_format(station: str, default: bool | None = None) -> bool:
    """Return True if the station uses the North American format.

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
    if default is not None:
        return default
    msg = "Station doesn't start with a recognized character set"
    raise BadStation(msg)


def valid_station(station: str) -> None:
    """Check the validity of a station ident.

    This function doesn't return anything. It merely raises a BadStation error if needed.
    """
    station = station.strip()
    if len(station) != 4:
        msg = "Report station ident must be four characters long"
        raise BadStation(msg)
    uses_na_format(station)
