"""
AVWX Base class tests
"""

# stdlib
import unittest

# module
from avwx import base, Station


def test_find_station():
    for code in ("KMCO", "MCO"):
        station = base.find_station(f"1 2 {code} 4")
        assert isinstance(station, Station)
        assert station.icao == "KMCO"
    assert base.find_station("1 2 3 4") is None
