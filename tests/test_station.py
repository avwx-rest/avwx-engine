"""
Station Data Tests
"""

# stdlib
from typing import Any, Optional

# library
import pytest

# module
from avwx import exceptions, station


NA_CODES = {"KJFK", "PHNL", "TNCM", "MYNN"}
IN_CODES = {"EGLL", "MNAH", "MUHA"}
BAD_CODES = {"12K", "MAYT"}


def test_station_list():
    """Test reporting filter for full station list"""
    reporting = station.station_list()
    full = station.station_list(False)
    assert len(full) > len(reporting)


# METAR and TAF reports come in two flavors: North American and International
# uses_na_format should determine the format based on the station ident using prefixes


@pytest.mark.parametrize("code", NA_CODES)
def test_is_na_format(code: str):
    assert station.uses_na_format(code) is True


def test_na_format_default():
    assert station.uses_na_format("KJFK", True) is True


@pytest.mark.parametrize("code", IN_CODES)
def test_is_in_format(code: str):
    assert station.uses_na_format(code) is False


@pytest.mark.parametrize("code", BAD_CODES)
def test_is_bad_format(code: str):
    with pytest.raises(exceptions.BadStation):
        station.uses_na_format(code)


# While not designed to catch all non-existant station idents,
# valid_station should catch non-ICAO strings and filter based on known prefixes


@pytest.mark.parametrize("code", NA_CODES | IN_CODES)
def test_is_valid_station(code: str):
    assert station.valid_station(code) is None


@pytest.mark.parametrize("code", BAD_CODES)
def test_is_invalid_station(code: str):
    with pytest.raises(exceptions.BadStation):
        station.valid_station(code)


def test_nearest():
    """Tests returning nearest Stations to lat, lon"""
    dist = station.nearest(28.43, -81.31)
    stn = dist.pop("station")
    assert isinstance(stn, station.Station)
    assert stn.icao == "KMCO"
    for val in dist.values():
        assert isinstance(val, float)


# These airport counts may change during data updates but should be valid otherwise
@pytest.mark.parametrize(
    "params,count",
    (
        ((30, -82, 10, True, True, 0.3), 1),
        ((30, -82, 10, True, False, 0.3), 5),
        ((30, -82, 10, False, False, 0.3), 7),
        ((30, -82, 1000, True, True, 0.5), 5),
        ((30, -82, 1000, False, False, 0.5), 37),
    ),
)
def test_nearest_params(params: tuple, count: int):
    stations = station.nearest(*params)
    assert len(stations) >= count
    for dist in stations:
        stn = dist.pop("station")
        assert isinstance(stn, station.Station)
        for val in dist.values():
            assert isinstance(val, float)


@pytest.mark.parametrize(
    "airport,reports,count",
    (
        (True, True, 6),
        (True, False, 16),
        (False, True, 6),
        (False, False, 30),
    ),
)
def test_nearest_filter(airport: bool, reports: bool, count: int):
    """Tests filtering nearest stations"""
    stations = station.nearest(30, -80, 30, airport, reports, 1.5)
    assert len(stations) == count


# Test Station class

BAD_STATION_CODES = {"1234", 1234, None, True, ""}


def test_storage_code():
    """Tests ID code selection"""
    stn = station.Station.from_icao("KJFK")
    stn.icao = "ICAO"
    stn.iata = "IATA"
    stn.gps = "GPS"
    stn.local = "LOCAL"
    assert stn.storage_code == "ICAO"
    stn.icao = None
    assert stn.storage_code == "IATA"
    stn.iata = None
    assert stn.storage_code == "GPS"
    stn.gps = None
    assert stn.storage_code == "LOCAL"
    stn.local = None
    with pytest.raises(exceptions.BadStation):
        stn.storage_code


@pytest.mark.parametrize(
    "icao,name,city",
    (
        ("KJFK", "John F Kennedy International Airport", "New York"),
        ("kjfk", "John F Kennedy International Airport", "New York"),
        ("KLAX", "Los Angeles / Tom Bradley International Airport", "Los Angeles"),
        ("PHNL", "Daniel K Inouye International Airport", "Honolulu"),
        ("EGLL", "London Heathrow Airport", "London"),
    ),
)
def test_from_icao(icao: str, name: str, city: str):
    """Tests loading a Station by ICAO ident"""
    stn = station.Station.from_icao(icao)
    assert isinstance(stn, station.Station)
    assert icao.upper() == stn.icao
    assert name == stn.name
    assert city == stn.city


@pytest.mark.parametrize("code", BAD_STATION_CODES | {"KX07", "TX35"})
def test_from_bad_icao(code: Any):
    with pytest.raises(exceptions.BadStation):
        station.Station.from_icao(code)


@pytest.mark.parametrize(
    "iata,icao",
    (
        ("JFK", "KJFK"),
        ("jfk", "KJFK"),
        ("LAX", "KLAX"),
        ("HNL", "PHNL"),
        ("LHR", "EGLL"),
    ),
)
def test_from_iata(iata: str, icao: str):
    """Tests loading a Station by IATA code"""
    stn = station.Station.from_iata(iata)
    assert isinstance(stn, station.Station)
    assert iata.upper() == stn.iata
    assert icao == stn.icao


@pytest.mark.parametrize("code", BAD_STATION_CODES | {"KMCO", "X35"})
def test_from_bad_iata(code: Any):
    with pytest.raises(exceptions.BadStation):
        station.Station.from_iata(code)


@pytest.mark.parametrize(
    "gps,icao,name",
    (
        ("KJFK", "KJFK", "John F Kennedy International Airport"),
        ("kjfk", "KJFK", "John F Kennedy International Airport"),
        ("EGLL", "EGLL", "London Heathrow Airport"),
        ("KX07", None, "Lake Wales Municipal Airport"),
    ),
)
def test_from_gps(gps: str, icao: Optional[str], name: str):
    """Tests loading a Station by GPS code"""
    stn = station.Station.from_gps(gps)
    assert isinstance(stn, station.Station)
    assert gps.upper() == stn.gps
    assert icao == stn.icao
    assert name == stn.name


@pytest.mark.parametrize("code", BAD_STATION_CODES | {"KX35"})
def test_from_bad_gps(code: Any):
    with pytest.raises(exceptions.BadStation):
        station.Station.from_gps(code)


@pytest.mark.parametrize(
    "code,icao,name",
    (
        ("KJFK", "KJFK", "John F Kennedy International Airport"),
        ("kjfk", "KJFK", "John F Kennedy International Airport"),
        ("EGLL", "EGLL", "London Heathrow Airport"),
        ("LHR", "EGLL", "London Heathrow Airport"),
        ("LAX", "KLAX", "Los Angeles / Tom Bradley International Airport"),
        ("HNL", "PHNL", "Daniel K Inouye International Airport"),
        ("KX07", None, "Lake Wales Municipal Airport"),
    ),
)
def test_from_code(code: str, icao: Optional[str], name: str):
    """Tests loading a Station by any code"""
    stn = station.Station.from_code(code)
    assert isinstance(stn, station.Station)
    assert icao == stn.icao
    assert name == stn.name


@pytest.mark.parametrize("code", BAD_STATION_CODES)
def test_from_bad_code(code: Any):
    with pytest.raises(exceptions.BadStation):
        station.Station.from_code(code)


@pytest.mark.parametrize(
    "lat,lon,icao", ((28.43, -81.31, "KMCO"), (28.43, -81, "KTIX"))
)
def test_station_nearest(lat: float, lon: float, icao: str):
    """Tests loading a Station nearest to a lat,lon coordinate pair"""
    stn, dist = station.Station.nearest(lat, lon, is_airport=True)
    assert isinstance(stn, station.Station)
    assert stn.icao == icao
    for val in dist.values():
        assert isinstance(val, float)


def test_station_nearest_without_iata():
    """Test nearest station with IATA req disabled"""
    stn, dist = station.Station.nearest(28.43, -81, False, False)
    assert isinstance(stn, station.Station)
    assert stn.lookup_code == "FA18"
    for val in dist.values():
        assert isinstance(val, float)


@pytest.mark.parametrize(
    "code,near",
    (
        ("KMCO", "KORL"),
        ("KJFK", "KLGA"),
        ("PHKO", "PHSF"),
    ),
)
def test_nearby(code: str, near: str):
    """Tests finding nearby airports to the current one"""
    target = station.Station.from_code(code)
    nearby = target.nearby()
    assert isinstance(nearby, list)
    assert len(nearby) == 10
    nearest = nearby[0]
    assert isinstance(nearest[0], station.Station)
    assert isinstance(nearest[1], dict)
    assert nearest[0].lookup_code == near


@pytest.mark.parametrize("code", ("KJFK", "EGLL"))
def test_sends_reports(code: str):
    """Tests bool indicating likely reporting station"""
    stn = station.Station.from_code(code)
    assert stn.sends_reports is True
    assert stn.iata is not None


@pytest.mark.parametrize("code", ("FA18",))
def test_not_sends_reports(code: str):
    stn = station.Station.from_code(code)
    assert stn.sends_reports is False
    assert stn.iata is None


# Test station search


@pytest.mark.parametrize("icao", ("KMCO", "KJFK", "PHNL", "EGLC"))
def test_exact_icao(icao: str):
    """Tests searching for a Station by exact ICAO ident"""
    results = station.search(icao)
    assert len(results) == 10
    assert results[0].icao == icao


@pytest.mark.parametrize(
    "text,icao",
    (
        ("kona hi", "PHKO"),
        ("danville powell field", "KDVK"),
        ("lexington ky", "KLEX"),
        ("orlando", "KMCO"),
        ("london city", "EGLC"),
    ),
)
def test_combined_terms(text: str, icao: str):
    """Tests search using multiple search terms"""
    results = station.search(text)
    assert len(results) == 10
    assert results[0].lookup_code == icao


def test_search_filter():
    """Tests search result filtering"""
    for airport in station.search("orlando", is_airport=True):
        assert "airport" in airport.type
    for airport in station.search("orlando", sends_reports=True):
        assert airport.reporting is True
