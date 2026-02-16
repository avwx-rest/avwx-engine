"""Service API Tests."""

# stdlib

from typing import Any

# library
import pytest

# module
from avwx import service

BASE_ATTRS = ("_url", "report_type", "_valid_types")


class BaseServiceTest:
    service_class = service.Service
    report_type: str = "metar"
    required_attrs: tuple[str, ...] = ()

    @pytest.fixture
    def serv(self) -> service.Service:
        return self.service_class(self.report_type)


class ServiceClassTest(BaseServiceTest):
    def test_init(self, serv: service.Service) -> None:
        """Test that the Service class is initialized properly."""
        for attr in BASE_ATTRS + self.required_attrs:
            assert hasattr(serv, attr) is True
        assert serv.report_type == self.report_type


class ServiceFetchTest(BaseServiceTest):
    def validate_report(self, station: str, report: Any) -> None:
        assert isinstance(report, str)
        assert station in report

    def test_fetch(self, station: str, serv: service.Service) -> None:
        """Test that reports are fetched from service."""
        report = serv.fetch(station)  # type: ignore
        self.validate_report(station, report)

    async def test_async_fetch(self, station: str, serv: service.Service) -> None:
        """Test that reports are fetched from async service."""
        report = await serv.async_fetch(station)  # type: ignore
        self.validate_report(station, report)
