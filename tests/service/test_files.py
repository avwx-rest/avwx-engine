"""
FileService API Tests
"""

# pylint: disable=protected-access,missing-class-docstring,unidiomatic-typecheck

# library
import pytest

# module
from avwx import exceptions, service

# tests
from .test_base import BaseTestService


class TestScrapeService(BaseTestService):

    service_class = service.files.FileService
    required_attrs = (
        "update_interval",
        "_updating",
        "last_updated",
        "is_outdated",
        "update",
    )

    def test_not_implemented(self):
        """Tests that the base FileService class throws NotImplemented errors"""
        if type(self.serv) != service.files.FileService:
            return
        # pylint: disable=no-member.pointless-statement
        with self.assertRaises(NotImplementedError):
            self.serv._extract(None, None)
        with self.assertRaises(NotImplementedError):
            self.serv._urls

    @pytest.mark.asyncio
    async def test_async_fetch_exceptions(self):
        """Tests async fetch exception handling"""
        for station in ("12K", "MAYT"):
            with self.assertRaises(exceptions.BadStation):
                await self.serv.async_fetch(station)
        # Should raise exception due to empty url
        if type(self.serv) == service.scrape.ScrapeService:
            with self.assertRaises(NotImplementedError):
                await self.serv.async_fetch("KJFK")


class TestNBM(TestScrapeService):

    service_class = service.NOAA_NBM
    report_type = "nbs"
    stations = ["KJFK", "KMCO", "PHNL"]


class TestGFS(TestScrapeService):

    service_class = service.NOAA_GFS
    report_type = "mav"
    stations = ["KJFK", "KLAX", "PHNL"]
