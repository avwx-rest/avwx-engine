"""
These services are specifically for returning multiple reports at a time.
For example, we'd want to know all SIGMETs currently in circulation.
The sources can be FTP, scraping, or any other method. There is no need
for specific stations or updating files behind the scenes.

The `fetch` and `async_fetch` methods are identical except they return
`List[str]` instead.
"""

# pylint: disable=invalid-name

# stdlib
import asyncio as aio
from contextlib import suppress
from typing import List

from avwx.service.base import CallsHTTP, Service


class NOAA_Bulk(Service, CallsHTTP):
    """Subclass for extracting current reports from NOAA CSV files

    This class accepts `"metar"`, `"taf"`, `"aircraftreport"`, and
    `"airsigmet"` as valid report types.
    """

    _url = "https://aviationweather.gov/data/cache/{}s.cache.csv"
    _valid_types = ("metar", "taf", "aircraftreport", "airsigmet")
    _rtype_map = {"airep": "aircraftreport", "pirep": "aircraftreport"}
    _targets = {"aircraftreport": -2}  # else 0

    def __init__(self, report_type: str):
        super().__init__(self._rtype_map.get(report_type, report_type))

    @staticmethod
    def _clean_report(report: str) -> str:
        report = report.strip(" '\"")
        for remove in (r"\x07", "\x07"):
            report = report.replace(remove, " ")
        return " ".join(report.split())

    def _extract(self, raw: str) -> List[str]:
        reports = []
        index = self._targets.get(self.report_type, 0)
        for line in raw.split("\n")[6:]:
            with suppress(IndexError):
                report = self._clean_report(line.split(",")[index])
                if report:
                    reports.append(report)
        return reports

    def fetch(self, timeout: int = 10) -> List[str]:
        """Bulk fetch report strings from the service"""
        return aio.run(self.async_fetch(timeout))

    async def async_fetch(self, timeout: int = 10) -> List[str]:
        """Asynchronously bulk fetch report strings from the service"""
        url = self._url.format(self.report_type)
        text = await self._call(url, timeout=timeout)
        return self._extract(text)


class NOAA_Intl(Service, CallsHTTP):
    """Scrapes international reports from NOAA. Designed to
    accompany `NOAA_Bulk` for AIRMET / SIGMET fetch.

    Currently, this class only accepts `"airsigmet"` as a valid report type.
    """

    _url = "https://www.aviationweather.gov/api/data/{}"
    _valid_types = ("airsigmet",)
    _url_map = {"airsigmet": "isigmet"}

    @staticmethod
    def _clean_report(report: str) -> str:
        lines = report.split()
        return " ".join([line for line in lines if not line.startswith("Hazard:")])

    def _extract(self, raw: str) -> List[str]:
        reports = []
        for line in raw.split("----------------------"):
            reports.append(self._clean_report(line.strip().strip('"')))
        return reports

    def fetch(self, timeout: int = 10) -> List[str]:
        """Bulk fetch report strings from the service"""
        return aio.run(self.async_fetch(timeout))

    async def async_fetch(self, timeout: int = 10) -> List[str]:
        """Asynchronously bulk fetch report strings from the service"""
        url = self._url.format(self._url_map[self.report_type])
        text = await self._call(url, timeout=timeout)
        return self._extract(text)
