"""This module contains station/airport dataclasses and search functions.

For the purposes of AVWX, a station is any physical location that has an ICAO
or GPS identification code. These are usually airports, but smaller locations
might not generate certain report types or defer to larger stations nearby. For
example, small airports with an AWOS system might not send the report to NOAA
or other local authority. They also include remote weather observation stations
not associated with airports like weather buouys.

# Classes

- [avwx.Station](./station/station.html#Station)
"""

from avwx.station.meta import __LAST_UPDATED__, station_list, uses_na_format, valid_station
from avwx.station.search import search
from avwx.station.station import Station, nearest

__all__ = (
    "Station",
    "station_list",
    "nearest",
    "search",
    "uses_na_format",
    "valid_station",
    "__LAST_UPDATED__",
)
