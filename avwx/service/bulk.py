"""
Classes for bulk fetching report strings
"""

# pylint: disable=invalid-name

# stdlib
import asyncio as aio
from contextlib import suppress
from typing import List

from avwx.service.base import CallsHTTP, Service


class NOAA_Bulk(Service, CallsHTTP):
    """Subclass for extracting current reports from NOAA CSV files"""

    url = "https://aviationweather.gov/adds/dataserver_current/current/{}s.cache.csv"
    _valid_types = ("metar", "taf", "aircraftreport")
    _rtype_map = {"airep": "aircraftreport", "pirep": "aircraftreport"}
    _targets = {"metar": 0, "taf": 0, "aircraftreport": -2}

    def __init__(self, request_type: str):
        super().__init__(self._rtype_map.get(request_type, request_type))

    def _extract(self, raw: str) -> List[str]:
        reports = []
        index = self._targets[self.report_type]
        for line in raw.split("\n")[6:]:
            with suppress(IndexError):
                if report := " ".join(line.split(",")[index].split()):
                    reports.append(report)
        return reports

    def fetch(self, timeout: int = 10) -> List[str]:
        """Bulk fetch report strings from the service"""
        return aio.run(self.async_fetch(timeout))

    async def async_fetch(self, timeout: int = 10) -> List[str]:
        """Asynchronously bulk fetch report strings from the service"""
        url = self.url.format(self.report_type)
        text = await self._call(url, timeout=timeout)
        return self._extract(text)
