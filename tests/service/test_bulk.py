"""
Bulk Service Tests
"""

# stdlib
import unittest

# module
from avwx.service import bulk

BASE_ATTRS = ("url", "report_type", "_valid_types")


class TestBulkService(unittest.IsolatedAsyncioTestCase):
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
            self.assertTrue(hasattr(service, attr))
        self.assertEqual(service.report_type, self.report_types[0])

    def test_fetch(self):
        """Tests that reports are fetched from service"""
        service = bulk.NOAA_Bulk(self.report_types[0])
        reports = service.fetch()
        self.assertIsInstance(reports, list)
        self.assertTrue(reports)

    async def test_async_fetch(self):
        """Tests that reports are fetched from async service"""
        for report_type in self.report_types:
            service = bulk.NOAA_Bulk(report_type)
            reports = await service.async_fetch()
            self.assertIsInstance(reports, list)
            self.assertTrue(reports)
