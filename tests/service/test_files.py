"""
FileService API Tests
"""

# pylint: disable=protected-access,missing-class-docstring,unidiomatic-typecheck

# library
import pytest

# module
from avwx import exceptions, service

# tests
from .test_base import ServiceClassTest, ServiceFetchTest


class TestScrapeService(ServiceClassTest):
    service_class = service.files.FileService
    required_attrs = (
        "update_interval",
        "_updating",
        "last_updated",
        "is_outdated",
        "update",
    )

    def test_not_implemented(self, serv: service.Service):
        """Tests that the base FileService class throws NotImplemented errors"""
        if type(serv) != service.files.FileService:
            return
        # pylint: disable=no-member.pointless-statement
        with pytest.raises(NotImplementedError):
            serv._extract(None, None)
        with pytest.aises(NotImplementedError):
            serv._urls

    @pytest.mark.asyncio
    async def test_fetch_bad_station(self, serv: service.Service):
        """Tests fetch exception handling"""
        for station in ("12K", "MAYT"):
            with pytest.raises(exceptions.BadStation):
                await serv.async_fetch(station)  # pylint: disable=no-member

    @pytest.mark.asyncio
    async def test_not_implemented(self, serv: service.Service):
        """Should raise exception due to empty url"""
        if type(serv) == service.scrape.ScrapeService:
            with pytest.raises(NotImplementedError):
                await serv.async_fetch("KJFK")  # pylint: disable=no-member


@pytest.mark.parametrize("station", ("KJFK", "KMCO", "PHNL"))
class TestNBM(ServiceFetchTest):
    service_class = service.NOAA_NBM
    report_type = "nbs"


def test_nbm_all():
    """Tests extracting all reports from the requested file"""
    reports = service.NOAA_NBM("nbs").all
    assert isinstance(reports, list)
    assert len(reports) > 0


# @pytest.mark.parametrize("station", ("KJFK", "KLAX", "PHNL"))
# class TestGFS(ServiceFetchTest):
#     service_class = service.NOAA_GFS
#     report_type = "mav"
