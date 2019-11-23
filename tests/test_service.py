"""
Service API Tests
"""

# stdlib
import unittest

# library
import pytest

# module
from avwx import exceptions, service


class TestService(unittest.TestCase):

    serv: service.Service
    name: str = "Service"
    stations: [str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serv = getattr(service, self.name)("metar")
        if not self.stations:
            self.stations = []

    def test_init(self):
        """
        Tests that the Service class is initialized properly
        """
        for attr in ("url", "rtype", "_make_err", "_extract", "fetch"):
            self.assertTrue(hasattr(self.serv, attr))
        self.assertEqual(self.serv.rtype, "metar")

    def test_service(self):
        """
        Tests that the base Service class has no URL and throws NotImplemented errors
        """
        if type(self.serv) == service.Service:
            self.assertIsNone(self.serv.url)
            with self.assertRaises(NotImplementedError):
                self.serv._extract(None)
        else:
            self.assertIsInstance(self.serv.url, str)
        self.assertIsInstance(self.serv.method, str)
        self.assertIn(self.serv.method, ("GET", "POST"))

    def test_make_err(self):
        """
        Tests that InvalidRequest exceptions are generated with the right message
        """
        key, msg = "test_key", "testing"
        err = self.serv._make_err(msg, key)
        err_str = (
            f"Could not find {key} in {self.serv.__class__.__name__} response\n{msg}"
        )
        self.assertIsInstance(err, exceptions.InvalidRequest)
        self.assertEqual(err.args, (err_str,))
        self.assertEqual(str(err), err_str)

    def test_fetch_exceptions(self):
        """
        Tests fetch exception handling
        """
        for station in ("12K", "MAYT"):
            with self.assertRaises(exceptions.BadStation):
                self.serv.fetch(station)
        # Should raise exception due to empty url
        if self.name == "Service":
            with self.assertRaises(NotImplementedError):
                self.serv.fetch("KJFK")

    @pytest.mark.asyncio
    async def test_async_fetch_exceptions(self):
        """
        Tests async fetch exception handling
        """
        for station in ("12K", "MAYT"):
            with self.assertRaises(exceptions.BadStation):
                await self.serv.async_fetch(station)
        # Should raise exception due to empty url
        if self.name == "Service":
            with self.assertRaises(AttributeError):
                await self.serv.async_fetch("KJFK")

    def test_fetch(self):
        """
        Tests that reports are fetched from service
        """
        for station in self.stations:
            report = self.serv.fetch(station)
            self.assertIsInstance(report, str)
            self.assertTrue(station in report)

    @pytest.mark.asyncio
    async def test_async_fetch(self):
        """
        Tests that reports are fetched from async service
        """
        for station in self.stations:
            report = await self.serv.async_fetch(station)
            self.assertIsInstance(report, str)
            self.assertTrue(report.startswith(station))


class TestNOAA(TestService):

    name = "NOAA"
    stations = ["KJFK", "EGLL", "PHNL"]


class TestAMO(TestService):

    name = "AMO"
    stations = ["RKSI", "RKSS", "RKNY"]


class TestMAC(TestService):

    name = "MAC"
    stations = ["SKBO"]


class TestAUBOM(TestService):

    name = "AUBOM"
    stations = ["YBBN", "YSSY"]


class TestModule(unittest.TestCase):
    def test_get_service(self):
        """
        Tests that the correct service class is returned
        """
        for stations, country, serv in (
            (("KJFK", "PHNL"), "US", service.NOAA),
            (("EGLL",), "GB", service.NOAA),
            (("RKSI",), "KR", service.AMO),
            (("SKBO", "SKPP"), "CO", service.MAC),
            (("YWOL", "YSSY"), "AU", service.AUBOM),
        ):
            for station in stations:
                self.assertIsInstance(
                    service.get_service(station, country)("metar"), serv
                )
