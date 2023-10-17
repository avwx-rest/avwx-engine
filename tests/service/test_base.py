"""
Service API Tests
"""

# pylint: disable=missing-class-docstring

# stdlib
from typing import Any, Tuple

# library
import pytest

# module
from avwx import service

BASE_ATTRS = ("_url", "report_type", "_valid_types")


class BaseServiceTest:
    service_class = service.Service
    report_type: str = "metar"
    required_attrs: Tuple[str] = tuple()

    @pytest.fixture
    def serv(self) -> service.Service:
        return self.service_class(self.report_type)


class ServiceClassTest(BaseServiceTest):
    def test_init(self, serv: service.Service):
        """Tests that the Service class is initialized properly"""
        for attr in BASE_ATTRS + self.required_attrs:
            assert hasattr(serv, attr) is True
        assert serv.report_type == self.report_type


class ServiceFetchTest(BaseServiceTest):
    def validate_report(self, station: str, report: Any) -> None:
        assert isinstance(report, str)
        assert station in report

    def test_fetch(self, station: str, serv: service.Service):
        """Tests that reports are fetched from service"""
        report = serv.fetch(station)
        self.validate_report(station, report)

    @pytest.mark.asyncio
    async def test_async_fetch(self, station: str, serv: service.Service):
        """Tests that reports are fetched from async service"""
        report = await serv.async_fetch(station)
        self.validate_report(station, report)
