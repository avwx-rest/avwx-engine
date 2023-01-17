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
        url = self.url.format(self.report_type)
        text = await self._call(url, timeout=timeout)
        return self._extract(text)


class NOAA_Intl(Service, CallsHTTP):
    """Bulk scrape international NOAA data"""

    url = "https://www.aviationweather.gov/{}/intl"
    _valid_types = ("airsigmet",)
    _url_map = {"airsigmet": "sigmet"}

    @staticmethod
    def _clean_report(report: str) -> str:
        # for remove in (r"\x07",):
        #     report = report.replace(remove, " ")
        return " ".join(report.split())

    def _extract(self, raw: str) -> List[str]:
        reports = []
        raw = raw[raw.find("<pre>") + 5 :]
        raw = raw[: raw.find("</pre>")]
        for line in raw.split("<br/>"):
            reports.append(self._clean_report(line.strip().strip('"')))
        return reports

    def fetch(self, timeout: int = 10) -> List[str]:
        """Bulk fetch report strings from the service"""
        return aio.run(self.async_fetch(timeout))

    async def async_fetch(self, timeout: int = 10) -> List[str]:
        """Asynchronously bulk fetch report strings from the service"""
        url = self.url.format(self._url_map[self.report_type])
        text = await self._call(url, timeout=timeout)
        return self._extract(text)
