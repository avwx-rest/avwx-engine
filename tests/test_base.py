"""AVWX Base class tests."""

# library
import pytest

# module
from avwx import Station, base


@pytest.mark.parametrize("code", ["KMCO", "MCO"])
def test_find_station(code: str) -> None:
    station = base.find_station(f"1 2 {code} 4")
    assert isinstance(station, Station)
    assert station.icao == "KMCO"


def test_no_station() -> None:
    assert base.find_station("1 2 3 4") is None
