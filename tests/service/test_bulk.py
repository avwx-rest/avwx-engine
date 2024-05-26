"""Bulk Service Tests."""

# library
import pytest

# module
from avwx.service import bulk

# tests
from .test_base import ServiceClassTest


class BulkServiceTest(ServiceClassTest):
    """Test bulk downloads from NOAA file server."""

    report_types: tuple[str, ...]

    @property
    def report_type(self) -> str:  # type: ignore
        return self.report_types[0]

    def test_fetch(self) -> None:
        """Test that reports are fetched from service."""
        reports = self.service_class(self.report_type).fetch()  # type: ignore
        assert isinstance(reports, list)
        assert bool(reports)

    @pytest.mark.asyncio
    async def test_async_fetch(self) -> None:
        """Test that reports are fetched from async service."""
        for report_type in self.report_types:
            service = self.service_class(report_type)
            reports = await service.async_fetch()  # type: ignore
            assert isinstance(reports, list)
            assert bool(reports)


class TestNOAABulk(BulkServiceTest):
    """Test bulk downloads from NOAA file server."""

    service_class = bulk.NoaaBulk
    report_types = (
        "metar",
        "taf",
        "aircraftreport",
        "airsigmet",
    )


class TestIntlBulk(BulkServiceTest):
    """Test bulk downloads from NOAA file server."""

    service_class = bulk.NoaaIntl
    report_types = ("airsigmet",)
