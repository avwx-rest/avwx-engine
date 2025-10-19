"""
These services are specifically for returning multiple reports at a time.
For example, we'd want to know all SIGMETs currently in circulation.
The sources can be FTP, scraping, or any other method. There is no need
for specific stations or updating files behind the scenes.

The `fetch` and `async_fetch` methods are identical except they return
`list[str]` instead.
"""

import asyncio as aio
import gzip
from typing import ClassVar

from xmltodict import parse as parsexml

from avwx.service.base import CallsHTTP, Service


class NoaaBulk(Service, CallsHTTP):
    """Subclass for extracting current reports from NOAA CSV files.

    This class accepts `"metar"`, `"taf"`, `"aircraftreport"`, and
    `"airsigmet"` as valid report types.
    """

    _url = "https://aviationweather.gov/data/cache/{}s.cache.xml.gz"
    _valid_types = ("metar", "taf", "aircraftreport", "airsigmet")
    _rtype_map: ClassVar[dict[str, str]] = {"airep": "aircraftreport", "pirep": "aircraftreport"}
    _targets: ClassVar[dict[str, str]] = {"aircraftreport": "AircraftReport"}  # else .upper()

    def __init__(self, report_type: str):
        super().__init__(self._rtype_map.get(report_type, report_type))

    def _extract(self, raw: str) -> list[str]:
        target = self._targets.get(self.report_type, self.report_type.upper())
        return [t["raw_text"] for t in parsexml(raw)["response"]["data"][target]]

    def fetch(self, timeout: int = 10) -> list[str]:
        """Bulk fetch report strings from the service."""
        return aio.run(self.async_fetch(timeout))

    async def async_fetch(self, timeout: int = 10) -> list[str]:
        """Asynchronously bulk fetch report strings from the service."""
        url = self._url.format(self.report_type)
        text = await self._call(url, timeout=timeout, formatter=gzip.decompress)
        return self._extract(text)


class NoaaIntl(Service, CallsHTTP):
    """Scrapes international reports from NOAA. Designed to
    accompany `NoaaBulk` for AIRMET / SIGMET fetch.

    Currently, this class only accepts `"airsigmet"` as a valid report type.
    """

    _url = "https://www.aviationweather.gov/api/data/{}"
    _valid_types = ("airsigmet",)
    _url_map: ClassVar[dict[str, str]] = {"airsigmet": "isigmet"}

    @staticmethod
    def _clean_report(report: str) -> str:
        lines = report.splitlines()
        return " ".join([line for line in lines if not line.startswith("Hazard:")])

    def _extract(self, raw: str) -> list[str]:
        split = "----------------------"
        return [self._clean_report(line.strip().strip('"')) for line in raw.split(split)]

    def fetch(self, timeout: int = 10) -> list[str]:
        """Bulk fetch report strings from the service."""
        return aio.run(self.async_fetch(timeout))

    async def async_fetch(self, timeout: int = 10) -> list[str]:
        """Asynchronously bulk fetch report strings from the service."""
        url = self._url.format(self._url_map[self.report_type])
        text = await self._call(url, timeout=timeout)
        return self._extract(text)
