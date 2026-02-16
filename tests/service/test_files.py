"""FileService API Tests."""

# ruff: noqa: SLF001

# library
import pytest

# module
from avwx import exceptions, service

# tests
from .test_base import ServiceClassTest, ServiceFetchTest


class TestFileService(ServiceClassTest):
    service_class = service.files.FileService
    required_attrs = (
        "update_interval",
        "_updating",
        "last_updated",
        "is_outdated",
        "update",
    )

    def test_file_service_not_implemented(self, serv: service.Service) -> None:
        """Test that the base FileService class throws NotImplemented errors."""
        if not isinstance(serv, service.files.FileService):
            return
        with pytest.raises(NotImplementedError):
            serv._extract(None, None)  # type: ignore
        with pytest.raises(NotImplementedError):
            assert serv._urls

    async def test_fetch_bad_station(self, serv: service.Service) -> None:
        """Test fetch exception handling."""
        for station in ("12K", "MAYT"):
            with pytest.raises(exceptions.BadStation):
                await serv.async_fetch(station)  # type: ignore

    async def test_scrape_service_not_implemented(self, serv: service.Service) -> None:
        """Should raise exception due to empty url."""
        if not isinstance(serv, service.scrape.ScrapeService):
            with pytest.raises(NotImplementedError):
                await serv.async_fetch("KJFK")  # type: ignore


@pytest.mark.parametrize("station", ["KJFK", "KMCO", "PHNL"])
class TestNBM(ServiceFetchTest):
    service_class = service.NoaaNbm
    report_type = "nbs"


async def test_nbm_all() -> None:
    """Test extracting all reports from the requested file."""
    srv = service.NoaaNbm("nbs")
    assert await srv.update() is True
    reports = srv.all
    assert isinstance(reports, list)
    assert len(reports) > 0


# @pytest.mark.parametrize("station", ["KJFK", "KLAX", "PHNL"])
# class TestGFS(ServiceFetchTest):
#     service_class = service.NOAA_GFS
#     report_type = "mav"
