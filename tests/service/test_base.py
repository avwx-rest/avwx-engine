"""
Service API Tests
"""

# pylint: disable=missing-class-docstring

# stdlib
from typing import Tuple
import unittest

# library
import pytest

# module
from avwx import service

BASE_ATTRS = ("url", "report_type", "_valid_types", "fetch", "async_fetch")


class BaseTestService(unittest.TestCase):

    serv: service.Service
    service_class = service.Service
    report_type: str = ""
    stations: Tuple[str] = tuple()
    required_attrs: Tuple[str] = tuple()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serv = self.service_class(self.report_type)
        self.required_attrs = BASE_ATTRS + self.required_attrs

    def test_init(self):
        """
        Tests that the Service class is initialized properly
        """
        for attr in self.required_attrs:
            self.assertTrue(hasattr(self.serv, attr))
        self.assertEqual(self.serv.report_type, self.report_type)

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
            self.assertTrue(station in report)
