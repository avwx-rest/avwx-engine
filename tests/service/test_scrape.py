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
        if not isinstance(serv, service.scrape.ScrapeService):
            with pytest.raises(NotImplementedError):
                serv.fetch("KJFK")

    async def test_async_fetch_bad_station(self, serv: service.scrape.ScrapeService) -> None:
        """Test fetch exception handling."""
        for station in ("12K", "MAYT"):
            with pytest.raises(exceptions.BadStation):
                await serv.async_fetch(station)  # type: ignore

    async def test_async_not_implemented(self, serv: service.scrape.ScrapeService) -> None:
        """Should raise exception due to empty url."""
        if not isinstance(serv, service.scrape.ScrapeService):
            with pytest.raises(NotImplementedError):
                await serv.async_fetch("KJFK")


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


class TestReportVariants:
    """Report headers that sources substitute for the requested type."""

    @pytest.mark.parametrize(
        ("report_type", "expected"),
        [
            ("metar", ["METAR", "SPECI"]),
            ("taf", ["TAF", "TAF AMD", "TAF COR"]),
        ],
    )
    def test_variants(self, report_type: str, expected: list[str]) -> None:
        serv = service.Nam(report_type)
        assert serv._report_variants() == expected


class TestNamVariantExtract:
    """Nam should extract reports issued under a variant header."""

    @staticmethod
    def _html(header: str, station: str, body: str) -> str:
        return f"<td>>{header} <b>{station}</b> top'>{station} {body}=</td>"

    @pytest.mark.parametrize("header", ["METAR", "SPECI"])
    def test_metar_headers(self, header: str) -> None:
        serv = service.Nam("metar")
        body = "301050Z 18008KT 9999 FEW035 12/06 Q1013"
        report = serv._extract(self._html(header, "ENGM", body), "ENGM")
        assert report.endswith(body)

    @pytest.mark.parametrize("header", ["TAF", "TAF AMD", "TAF COR"])
    def test_taf_headers(self, header: str) -> None:
        serv = service.Nam("taf")
        body = "301100Z 3011/3111 18010KT 9999"
        report = serv._extract(self._html(header, "ENGM", body), "ENGM")
        assert report.endswith(body)

    def test_missing_report_still_raises(self) -> None:
        serv = service.Nam("metar")
        with pytest.raises(exceptions.InvalidRequest):
            serv._extract("<html>nothing here</html>", "ENGM")


class TestOlbsVariantExtract:
    """Olbs should accept a SPECI in response to a METAR request."""

    @pytest.mark.parametrize("header", ["METAR", "SPECI"])
    def test_metar_headers(self, header: str) -> None:
        serv = service.Olbs("metar")
        body = "VIDP 301050Z 09006KT 3000 HZ SCT025 32/24 Q1002"
        report = serv._extract(f"<b>METAR:</b><br>{header} {body}=", "VIDP")
        assert report == f"{header} {body}"

    def test_unknown_header_still_raises(self) -> None:
        serv = service.Olbs("metar")
        with pytest.raises(exceptions.InvalidRequest):
            serv._extract("<b>METAR:</b><br>XXXXX VIDP 301050Z=", "VIDP")


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
