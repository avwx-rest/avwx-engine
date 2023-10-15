"""
Bulk Service Tests
"""

# stdlib
from typing import Tuple

# library
import pytest

# module
from avwx.service import bulk

# tests
from .test_base import ServiceClassTest


class BulkServiceTest(ServiceClassTest):
    """Tests bulk downloads from NOAA file server"""

    service_class: bulk.Service
    report_types: Tuple[str, ...]

    @property
    def report_type(self) -> str:
        return self.report_types[0]

    def test_fetch(self):
        """Tests that reports are fetched from service"""
        reports = self.service_class(self.report_type).fetch()
        assert isinstance(reports, list)
        assert bool(reports)

    @pytest.mark.asyncio
    async def test_async_fetch(self):
        """Tests that reports are fetched from async service"""
        for report_type in self.report_types:
            service = self.service_class(report_type)
            reports = await service.async_fetch()
            assert isinstance(reports, list)
            assert bool(reports)


class TestNOAABulk(BulkServiceTest):
    """Tests bulk downloads from NOAA file server"""

    service_class = bulk.NOAA_Bulk
    report_types = (
        "metar",
        "taf",
        "aircraftreport",
        "airsigmet",
    )


class TestIntlBulk(BulkServiceTest):
    """Tests bulk downloads from NOAA file server"""

    service_class = bulk.NOAA_Intl
    report_types = ("airsigmet",)
