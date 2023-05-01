"""
Bulk Service Tests
"""

# library
import pytest

# module
from avwx.service import bulk

BASE_ATTRS = ("url", "report_type", "_valid_types")


class TestBulkService:
    """Tests bulk downloads from NOAA file server"""

    report_types = (
        "metar",
        "taf",
        "aircraftreport",
    )
    required_attrs = BASE_ATTRS

    def test_init(self):
        """Tests that the Bulk class is initialized properly"""
        service = bulk.NOAA_Bulk(self.report_types[0])
        for attr in self.required_attrs:
            assert hasattr(service, attr) is True
        assert service.report_type == self.report_types[0]

    def test_fetch(self):
        """Tests that reports are fetched from service"""
        service = bulk.NOAA_Bulk(self.report_types[0])
        reports = service.fetch()
        assert isinstance(reports, list)
        assert bool(reports)

    @pytest.mark.asyncio
    async def test_async_fetch(self):
        """Tests that reports are fetched from async service"""
        for report_type in self.report_types:
            service = bulk.NOAA_Bulk(report_type)
            reports = await service.async_fetch()
            assert isinstance(reports, list)
            assert bool(reports)
