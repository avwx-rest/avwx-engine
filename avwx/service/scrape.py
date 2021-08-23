"""
Classes for retrieving raw report strings via web scraping
"""

# pylint: disable=arguments-differ,invalid-name

# stdlib
import asyncio as aio
import random
from typing import Any, List, Optional, Tuple, Union

# library
from xmltodict import parse as parsexml  # type: ignore

# module
from avwx.parsing.core import dedupe
from avwx.exceptions import InvalidRequest
from avwx.station import valid_station
from avwx.service.base import CallsHTTP, Service


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
]


class ScrapeService(Service, CallsHTTP):  # pylint: disable=too-few-public-methods
    """Service class for fetching reports via direct web requests"""

    _valid_types: Tuple[str, ...] = ("metar", "taf")
    _strip_whitespace: bool = True

    def _make_err(self, body: str, key: str = "report path") -> InvalidRequest:
        """Returns an InvalidRequest exception with formatted error message"""
        msg = f"Could not find {key} in {self.__class__.__name__} response\n"
        return InvalidRequest(msg + body)

    @staticmethod
    def _make_headers() -> dict:
        """Returns request headers"""
        return {}

    def _post_data(  # pylint: disable=no-self-use
        self, station: str  # pylint: disable=unused-argument
    ) -> dict:
        """Returns the POST form/data payload"""
        return {}

    def _clean_report(self, report: Any) -> Any:
        """Replaces all *whitespace elements with a single space if enabled"""
        if not self._strip_whitespace:
            return report
        if isinstance(report, list):
            return dedupe(" ".join(r.split()) for r in report)
        if isinstance(report, str):
            return " ".join(report.split())
        return report


class StationScrape(ScrapeService):
    """Service class fetching reports from a station ICAO"""

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        raise NotImplementedError()

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report string from the service response"""
        raise NotImplementedError()

    async def _fetch(self, station: str, url: str, params: dict, timeout: int) -> str:
        headers = self._make_headers()
        data = self._post_data(station) if self.method.lower() == "post" else None
        text = await self._call(
            url, params=params, headers=headers, data=data, timeout=timeout
        )
        report = self._extract(text, station)
        return self._clean_report(report)

    def fetch(
        self,
        station: str,
        timeout: int = 10,
    ) -> str:
        """Fetches a report string from the service"""
        return aio.run(self.async_fetch(station, timeout))

    async def async_fetch(self, station: str, timeout: int = 10) -> str:
        """Asynchronously fetch a report string from the service"""
        valid_station(station)
        url, params = self._make_url(station)
        return await self._fetch(station, url, params, timeout)


# Multiple sources for NOAA data


class NOAA_ADDS(ScrapeService):
    """Requests data from NOAA ADDS"""

    url = "https://aviationweather.gov/adds/dataserver_current/httpparam"

    _valid_types = ("metar", "taf", "aircraftreport")
    _rtype_map = {"airep": "aircraftreport"}
    _targets = {"metar": "METAR", "taf": "TAF", "aircraftreport": "AircraftReport"}
    _coallate = ("aircraftreport",)

    def __init__(self, request_type: str):
        super().__init__(self._rtype_map.get(request_type, request_type))

    def _make_url(
        self, station: Optional[str], lat: Optional[float], lon: Optional[float]
    ) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        # Base request params
        params = {
            "requestType": "retrieve",
            "format": "XML",
            "hoursBeforeNow": 2,
            "dataSource": self.report_type + "s",
        }
        if self.report_type == "aircraftreport":
            params["radialDistance"] = f"200;{lon},{lat}"
        else:
            params["stationString"] = station
        return self.url, params

    def _extract(self, raw: str) -> Union[str, List[str]]:
        """Extracts the raw_report element from XML response"""
        resp = parsexml(raw)
        try:
            data = resp["response"]["data"]
            if data["@num_results"] == "0":
                return ""
            reports = data[self._targets[self.report_type]]
        except KeyError as key_error:
            raise self._make_err(raw) from key_error
        # Only one report exists
        if isinstance(reports, dict):
            ret = reports["raw_text"]
            if self.report_type in self._coallate:
                ret = [ret]
        # Multiple reports exist
        elif isinstance(reports, list) and reports:
            if self.report_type in self._coallate:
                ret = [r["raw_text"] for r in reports]
            else:
                ret = reports[0]["raw_text"]
        # Something went wrong
        else:
            raise self._make_err(raw, '"raw_text"')
        return ret

    def fetch(
        self,
        station: str = None,
        lat: float = None,
        lon: float = None,
        timeout: int = 10,
    ) -> Union[str, List[str]]:
        """Fetches a report string from the service"""
        return aio.run(self.async_fetch(station, lat, lon, timeout))

    async def async_fetch(
        self,
        station: str = None,
        lat: float = None,
        lon: float = None,
        timeout: int = 10,
    ) -> Union[str, List[str]]:
        """Asynchronously fetch a report string from the service"""
        if station:
            valid_station(station)
        elif lat is None or lon is None:
            raise ValueError("No valid fetch parameters")
        url, params = self._make_url(station, lat, lon)
        text = await self._call(url, params=params, timeout=timeout)
        report = self._extract(text)
        return self._clean_report(report)


class NOAA_FTP(StationScrape):
    """Requests data from NOAA via FTP"""

    url = "https://tgftp.nws.noaa.gov/data/{}/{}/stations/{}.TXT"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        root = "forecasts" if self.report_type == "taf" else "observations"
        return self.url.format(root, self.report_type, station), {}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report using string finding"""
        raw = raw[raw.find(station) :]
        return raw[: raw.find('"')]


class NOAA_Scrape(StationScrape):
    """Requests data from NOAA via site scraping"""

    url = "https://aviationweather.gov/{}/data"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        hours = 7 if self.report_type == "taf" else 2
        return (
            self.url.format(self.report_type),
            {"ids": station, "format": "raw", "hours": hours},
        )

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report using string finding"""
        raw = raw[raw.find("<code>") :]
        raw = raw[raw.find(station) :]
        raw = raw[: raw.find("</code>")]
        for char in ("<br/>", "&nbsp;"):
            raw = raw.replace(char, " ")
        return raw


NOAA = NOAA_Scrape


# Regional data sources


class AMO(StationScrape):
    """Requests data from AMO KMA for Korean stations"""

    url = "http://amoapi.kma.go.kr/amoApi/{}"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        return self.url.format(self.report_type), {"icao": station}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report message from XML response"""
        resp = parsexml(raw)
        try:
            report = resp["response"]["body"]["items"]["item"][
                self.report_type.lower() + "Msg"
            ]
        except KeyError as key_error:
            raise self._make_err(raw) from key_error
        if not report:
            raise self._make_err("The station might not exist")
        # Replace line breaks
        report = report.replace("\n", "")
        # Remove excess leading and trailing data
        for item in (self.report_type.upper(), "SPECI"):
            if report.startswith(item + " "):
                report = report[len(item) + 1 :]
        report = report.rstrip("=")
        # Make every element single-spaced and stripped
        return " ".join(report.split())


class MAC(StationScrape):
    """Requests data from Meteorologia Aeronautica Civil for Columbian stations"""

    url = "http://meteorologia.aerocivil.gov.co/expert_text_query/parse"
    method = "POST"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        return self.url, {"query": f"{self.report_type} {station}"}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report message using string finding"""
        report = raw[raw.find(station.upper() + " ") :]
        report = report[: report.find(" =")]
        return report


class AUBOM(StationScrape):
    """Requests data from the Australian Bureau of Meteorology"""

    url = "http://www.bom.gov.au/aviation/php/process.php"
    method = "POST"

    def _make_url(self, _) -> Tuple[str, dict]:
        """Returns a formatted URL and empty parameters"""
        return self.url, {}

    @staticmethod
    def _make_headers() -> dict:
        """Returns request headers"""
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Language": "en-us",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.bom.gov.au",
            "Origin": "http://www.bom.gov.au",
            "User-Agent": random.choice(USER_AGENTS),
            "Connection": "keep-alive",
        }

    def _post_data(self, station: str) -> dict:
        """Returns the POST form"""
        return {"keyword": station, "type": "search", "page": "TAF"}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the reports from HTML response"""
        index = 1 if self.report_type == "taf" else 2
        try:
            report = raw.split("<p")[index]
            report = report[report.find(">") + 1 :]
        except IndexError as index_error:
            raise self._make_err("The station might not exist") from index_error
        if report.startswith("<"):
            return ""
        report = report[: report.find("</p>")]
        return report.replace("<br />", " ")


class OLBS(StationScrape):
    """Requests data from India OLBS flight briefing"""

    # url = "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/showopmetquery.php"
    # method = "POST"

    # Temp redirect
    url = "https://avbrief3.el.r.appspot.com/"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and empty parameters"""
        return self.url, {"icao": station}

    def _post_data(self, station: str) -> dict:
        """Returns the POST form"""
        # Can set icaos to "V*" to return all results
        return {"icaos": station, "type": self.report_type}

    @staticmethod
    def _make_headers() -> dict:
        """Returns request headers"""
        return {
            # "Content-Type": "application/x-www-form-urlencoded",
            # "Accept": "text/html, */*; q=0.01",
            # "Accept-Language": "en-us",
            "Accept-Encoding": "gzip, deflate, br",
            # "Host": "olbs.amsschennai.gov.in",
            "User-Agent": random.choice(USER_AGENTS),
            "Connection": "keep-alive",
            # "Referer": "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/",
            # "X-Requested-With": "XMLHttpRequest",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://avbrief3.el.r.appspot.com/",
            "Host": "avbrief3.el.r.appspot.com",
        }

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the reports from HTML response"""
        # start = raw.find(f"{self.report_type.upper()} {station} ")
        start = raw.find(f">{self.report_type.upper()}</div>")
        if start < 0:
            return ""
        raw = raw[start:]
        start = raw.find(station)
        if start < 0:
            return ""
        report = raw[start:]
        report = report[: report.find("=")].strip()
        return " ".join(dedupe(report.split()))


PREFERRED = {"RK": AMO, "SK": MAC}
BY_COUNTRY = {"AU": AUBOM, "IN": OLBS}


def get_service(station: str, country_code: str) -> ScrapeService:
    """Returns the preferred service for a given station"""
    for prefix, service in PREFERRED.items():
        if station.startswith(prefix):
            return service  # type: ignore
    return BY_COUNTRY.get(country_code, NOAA)  # type: ignore
