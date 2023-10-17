"""
ScrapeService API Tests
"""

# pylint: disable=protected-access,missing-class-docstring,unidiomatic-typecheck

# stdlib
from typing import Any, Tuple

# library
import pytest

# module
from avwx import exceptions, service

# tests
from .test_base import ServiceClassTest, ServiceFetchTest


class TestStationScrape(ServiceClassTest):
    service_class = service.scrape.StationScrape
    required_attrs = ("method", "_strip_whitespace", "_extract")

    def test_service(self, serv: service.scrape.ScrapeService):
        """Tests for expected values and method implementation"""
        # pylint: disable=no-member
        assert isinstance(serv._url, str)
        assert isinstance(serv.method, str)
        assert serv.method in {"GET", "POST"}

    def test_make_err(self, serv: service.scrape.ScrapeService):
        """Tests that InvalidRequest exceptions are generated with the right message"""
        # pylint: disable=no-member
        key, msg = "test_key", "testing"
        name = serv.__class__.__name__
        err = serv._make_err(msg, key)
        err_str = f"Could not find {key} in {name} response\n{msg}"
        assert isinstance(err, exceptions.InvalidRequest)
        assert err.args == (err_str,)
        assert str(err) == err_str

    def test_fetch_bad_station(self, serv: service.scrape.ScrapeService):
        """Tests fetch exception handling"""
        for station in ("12K", "MAYT"):
            with pytest.raises(exceptions.BadStation):
                serv.fetch(station)  # pylint: disable=no-member

    def test_not_implemented(self, serv: service.scrape.ScrapeService):
        """Should raise exception due to empty url"""
        if type(serv) == service.scrape.ScrapeService:
            with pytest.raises(NotImplementedError):
                serv.fetch("KJFK")  # pylint: disable=no-member

    @pytest.mark.asyncio
    async def test_fetch_bad_station(self, serv: service.scrape.ScrapeService):
        """Tests fetch exception handling"""
        for station in ("12K", "MAYT"):
            with pytest.raises(exceptions.BadStation):
                await serv.async_fetch(station)  # pylint: disable=no-member

    @pytest.mark.asyncio
    async def test_not_implemented(self, serv: service.scrape.ScrapeService):
        """Should raise exception due to empty url"""
        if type(serv) == service.scrape.ScrapeService:
            with pytest.raises(NotImplementedError):
                await serv.async_fetch("KJFK")  # pylint: disable=no-member


NOAA_PARAMS = ("station", ("KJFK", "EGLL", "PHNL"))


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNOAA(ServiceFetchTest):
    service_class = service.NOAA


class TestNOAAClass(TestStationScrape):
    service_class = service.NOAA


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNOAATaf(ServiceFetchTest):
    service_class = service.NOAA
    report_type = "taf"


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNOAA_FTP(ServiceFetchTest):
    service_class = service.scrape.NOAA_FTP


class TestNOAA_FTPClass(TestStationScrape):
    service_class = service.scrape.NOAA_FTP


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNOAA_Scrape(ServiceFetchTest):
    service_class = service.scrape.NOAA_Scrape


class TestNOAA_ScrapeClass(TestStationScrape):
    service_class = service.scrape.NOAA_Scrape


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNOAA_ScrapeList(ServiceFetchTest):
    service_class = service.scrape.NOAA_ScrapeList
    report_type = "pirep"

    def validate_report(self, station: str, report: Any) -> None:
        assert isinstance(report, list)
        assert isinstance(report[0], str)


class TestNOAA_ScrapeListClass(TestStationScrape):
    service_class = service.scrape.NOAA_ScrapeList
    report_type = "pirep"


# @pytest.mark.parametrize("station", ("RKSI", "RKSS", "RKNY"))
# class TestAMO(TestStationScrape):
#     service_class = service.AMO
#     report_type = "metar"

# class TestAMOClass(TestStationScrape):
#     service_class = service.AMO


@pytest.mark.parametrize("station", ("SKBO",))
class TestMAC(ServiceFetchTest):
    service_class = service.MAC


class TestMACClass(TestStationScrape):
    service_class = service.MAC


@pytest.mark.parametrize("station", ("YBBN", "YSSY", "YCNK"))
class TestAUBOM(ServiceFetchTest):
    service_class = service.AUBOM


class TestAUBOMClass(TestStationScrape):
    service_class = service.AUBOM


@pytest.mark.parametrize("station", ("VAPO", "VEGT"))
class TestOLBS(ServiceFetchTest):
    service_class = service.OLBS


class TestOLBSClass(TestStationScrape):
    service_class = service.OLBS


@pytest.mark.parametrize("station", ("EHAM", "ENGM", "BIRK"))
class TestNAM(ServiceFetchTest):
    service_class = service.NAM


class TestNAMClass(TestStationScrape):
    service_class = service.NAM


# @pytest.mark.parametrize("station", ("ZJQH", "ZYCC", "ZSWZ"))
# class TestAVT(ServiceFetchTest):
#     service_class = service.AVT

# class TestAVTClass(TestStationScrape):
#     service_class = service.AVT


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNotam(ServiceFetchTest):
    service_class = service.FAA_NOTAM
    report_type = "notam"

    def validate_report(self, station: str, report: Any) -> None:
        assert isinstance(report, list)
        assert isinstance(report[0], str)
        assert station in report[0]


@pytest.mark.parametrize(
    "stations,country,serv",
    (
        (("KJFK", "PHNL"), "US", service.NOAA),
        (("EGLL",), "GB", service.NOAA),
        (("RKSI",), "KR", service.AMO),
        (("SKBO", "SKPP"), "CO", service.MAC),
        (("YWOL", "YSSY"), "AU", service.AUBOM),
        (("VAPO", "VEGT"), "IN", service.OLBS),
        # (("ZJQH", "ZYCC", "ZSWZ"), "CN", service.AVT),
    ),
)
def test_get_service(stations: Tuple[str], country: str, serv: service.Service):
    """Tests that the correct service class is returned"""
    for station in stations:
        fetched = service.get_service(station, country)("metar")
        assert isinstance(fetched, serv)
