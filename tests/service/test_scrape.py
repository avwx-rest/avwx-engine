"""ScrapeService API Tests."""

# ruff: noqa: SLF001

# stdlib
from typing import Any

# library
import pytest

# module
from avwx import exceptions, service

# tests
from .test_base import ServiceClassTest, ServiceFetchTest


class TestStationScrape(ServiceClassTest):
    service_class = service.scrape.StationScrape
    required_attrs = ("method", "_strip_whitespace", "_extract")

    def test_service(self, serv: service.scrape.ScrapeService) -> None:
        """Test for expected values and method implementation."""
        assert isinstance(serv._url, str)
        assert isinstance(serv.method, str)
        assert serv.method in {"GET", "POST"}

    def test_make_err(self, serv: service.scrape.ScrapeService) -> None:
        """Test that InvalidRequest exceptions are generated with the right message."""
        key, msg = "test_key", "testing"
        name = serv.__class__.__name__
        err = serv._make_err(msg, key)
        err_str = f"Could not find {key} in {name} response. {msg}"
        assert isinstance(err, exceptions.InvalidRequest)
        assert err.args == (err_str,)
        assert str(err) == err_str

    def test_fetch_bad_station(self, serv: service.scrape.ScrapeService) -> None:
        """Test fetch exception handling."""
        for station in ("12K", "MAYT"):
            with pytest.raises(exceptions.BadStation):
                serv.fetch(station)  # type: ignore

    def test_not_implemented(self, serv: service.scrape.ScrapeService) -> None:
        """Should raise exception due to empty url."""
        if type(serv) == service.scrape.ScrapeService:
            with pytest.raises(NotImplementedError):
                serv.fetch("KJFK")  # type: ignore

    @pytest.mark.asyncio
    async def test_async_fetch_bad_station(self, serv: service.scrape.ScrapeService) -> None:
        """Test fetch exception handling."""
        for station in ("12K", "MAYT"):
            with pytest.raises(exceptions.BadStation):
                await serv.async_fetch(station)  # type: ignore

    @pytest.mark.asyncio
    async def test_async_not_implemented(self, serv: service.scrape.ScrapeService) -> None:
        """Should raise exception due to empty url."""
        if type(serv) == service.scrape.ScrapeService:
            with pytest.raises(NotImplementedError):
                await serv.async_fetch("KJFK")  # type: ignore


NOAA_PARAMS = ("station", ["KJFK", "EGLL", "PHNL"])


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNoaa(ServiceFetchTest):
    service_class = service.Noaa


class TestNoaaClass(TestStationScrape):
    service_class = service.Noaa


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNoaaTaf(ServiceFetchTest):
    service_class = service.Noaa
    report_type = "taf"


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNoaaApi(ServiceFetchTest):
    service_class = service.scrape.NoaaApi


class TestNoaaApiClass(TestStationScrape):
    service_class = service.scrape.NoaaApi


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNoaaFtp(ServiceFetchTest):
    service_class = service.scrape.NoaaFtp


class TestNoaaFtpClass(TestStationScrape):
    service_class = service.scrape.NoaaFtp


@pytest.mark.parametrize(*NOAA_PARAMS)
class TestNoaaApiList(ServiceFetchTest):
    service_class = service.scrape.NoaaApiList
    report_type = "pirep"

    def validate_report(self, station: str, report: Any) -> None:  # noqa: ARG002
        assert isinstance(report, list)
        if report:
            assert isinstance(report[0], str)


class TestNoaaApiListClass(TestStationScrape):
    service_class = service.scrape.NoaaApiList  # type: ignore
    report_type = "pirep"


# @pytest.mark.parametrize("station", ["RKSI", "RKSS", "RKNY"])
# class TestAmo(TestStationScrape):
#     service_class = service.Amo
#     report_type = "metar"

# class TestAmoClass(TestStationScrape):
#     service_class = service.Amo


# @pytest.mark.parametrize("station", ["SKBO"])
# class TestMac(ServiceFetchTest):
#     service_class = service.Mac


class TestMacClass(TestStationScrape):
    service_class = service.Mac


# @pytest.mark.parametrize("station", ["YBBN", "YSSY", "YCNK"])
# class TestAubom(ServiceFetchTest):
#     service_class = service.Aubom


# class TestAubomClass(TestStationScrape):
#     service_class = service.Aubom


@pytest.mark.parametrize("station", ["VAPO", "VEGT"])
class TestOlbs(ServiceFetchTest):
    service_class = service.Olbs


class TestOlbsClass(TestStationScrape):
    service_class = service.Olbs


@pytest.mark.parametrize("station", ["EHAM", "ENGM", "BIRK"])
class TestNam(ServiceFetchTest):
    service_class = service.Nam


class TestNamClass(TestStationScrape):
    service_class = service.Nam


# @pytest.mark.parametrize("station", ["ZJQH", "ZYCC", "ZSWZ"])
# class TestAvt(ServiceFetchTest):
#     service_class = service.Avt

# class TestAvtClass(TestStationScrape):
#     service_class = service.Avt


# @pytest.mark.parametrize(*NOAA_PARAMS)
# class TestNotam(ServiceFetchTest):
#     service_class = service.FaaNotam
#     report_type = "notam"

#     def validate_report(self, station: str, report: Any) -> None:
#         assert isinstance(report, list)
#         assert isinstance(report[0], str)
#         assert station in report[0]


@pytest.mark.parametrize(
    ("stations", "country", "serv"),
    [
        (("KJFK", "PHNL"), "US", service.Noaa),
        (("EGLL",), "GB", service.Noaa),
        (("RKSI",), "KR", service.Amo),
        # (("SKBO", "SKPP"), "CO", service.Mac),
        # (("YWOL", "YSSY"), "AU", service.Aubom),
        (("VAPO", "VEGT"), "IN", service.Olbs),
        # (("ZJQH", "ZYCC", "ZSWZ"), "CN", service.Avt),
    ],
)
def test_get_service(stations: tuple[str], country: str, serv: service.Service) -> None:
    """Test that the correct service class is returned."""
    for station in stations:
        fetched = service.get_service(station, country)("metar")  # type: ignore
        assert isinstance(fetched, serv)  # type: ignore
