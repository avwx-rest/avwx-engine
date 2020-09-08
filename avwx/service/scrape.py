"""
Classes for retrieving raw report strings via web scraping
"""

# pylint: disable=arguments-differ,invalid-name

# stdlib
import asyncio as aio
from socket import gaierror
from typing import List, Tuple, Union

# library
import httpcore
import httpx
from xmltodict import parse as parsexml

# module
from avwx.parsing.core import dedupe
from avwx.exceptions import InvalidRequest, SourceError
from avwx.station import valid_station
from avwx.service.base import Service


class ScrapeService(Service):
    """
    Service class for fetching reports via direct web requests
    """

    method: str = "GET"

    _valid_types = ("metar", "taf")
    _strip_whitespace: bool = True

    def _make_err(self, body: str, key: str = "report path") -> InvalidRequest:
        """
        Returns an InvalidRequest exception with formatted error message
        """
        msg = f"Could not find {key} in {self.__class__.__name__} response\n"
        return InvalidRequest(msg + body)

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """
        Returns a formatted URL and parameters
        """
        raise NotImplementedError()

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts the report string from the service response
        """
        raise NotImplementedError()

    # pylint: disable=unused-argument
    @staticmethod
    def _post_data(station: str) -> dict:
        """
        Returns the POST form/data payload
        """
        return {}

    def _clean_report(self, report: str) -> str:
        """
        Replaces all *whitespace elements with a single space if enabled
        """
        if not self._strip_whitespace:
            return report
        if isinstance(report, list):
            return dedupe(" ".join(r.split()) for r in report)
        return " ".join(report.split())

    async def _fetch(self, station: str, url: str, params: dict, timeout: int) -> str:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if self.method.lower() == "post":
                    resp = await client.post(
                        url, params=params, data=self._post_data(station)
                    )
                else:
                    resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    raise SourceError(
                        f"{self.__class__.__name__} server returned {resp.status_code}"
                    )
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpcore.ReadTimeout):
            raise TimeoutError(f"Timeout from {self.__class__.__name__} server")
        except (gaierror, httpcore.ConnectError):
            raise ConnectionError(
                f"Unable to connect to {self.__class__.__name__} server"
            )
        except httpcore.NetworkError:
            raise ConnectionError(
                f"Unable to read data from {self.__class__.__name__} server"
            )
        report = self._extract(resp.text, station)
        return self._clean_report(report)

    def fetch(self, station: str, timeout: int = 10,) -> str:
        """
        Fetches a report string from the service
        """
        return aio.run(self.async_fetch(station, timeout))

    async def async_fetch(self, station: str, timeout: int = 10) -> str:
        """
        Asynchronously fetch a report string from the service
        """
        valid_station(station)
        url, params = self._make_url(station)
        return await self._fetch(station, url, params, timeout)


# Multiple sources for NOAA data


class NOAA_ADDS(ScrapeService):
    """
    Requests data from NOAA ADDS
    """

    url = "https://aviationweather.gov/adds/dataserver_current/httpparam"

    _valid_types = ("metar", "taf", "aircraftreport")
    _rtype_map = {"airep": "aircraftreport"}
    _targets = {"metar": "METAR", "taf": "TAF", "aircraftreport": "AircraftReport"}
    _coallate = ("aircraftreport",)

    def __init__(self, request_type: str):
        super().__init__(self._rtype_map.get(request_type, request_type))

    def _make_url(self, station: str, lat: float, lon: float) -> Tuple[str, dict]:
        """
        Returns a formatted URL and parameters
        """
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

    def _extract(self, raw: str, station: str = None) -> Union[str, List[str]]:
        """
        Extracts the raw_report element from XML response
        """
        resp = parsexml(raw)
        try:
            data = resp["response"]["data"]
            if data["@num_results"] == "0":
                return ""
            reports = data[self._targets[self.report_type]]
        except KeyError:
            raise self._make_err(raw)
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
    ) -> str:
        """
        Fetches a report string from the service
        """
        return aio.run(self.async_fetch(station, lat, lon, timeout))

    async def async_fetch(
        self,
        station: str = None,
        lat: float = None,
        lon: float = None,
        timeout: int = 10,
    ) -> str:
        """
        Asynchronously fetch a report string from the service
        """
        if station:
            valid_station(station)
        elif lat is None or lon is None:
            raise ValueError("No valid fetch parameters")
        url, params = self._make_url(station, lat, lon)
        return await self._fetch(station, url, params, timeout)


class NOAA_FTP(ScrapeService):
    """
    Requests data from NOAA via FTP
    """

    url = "https://tgftp.nws.noaa.gov/data/{}/{}/stations/{}.TXT"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """
        Returns a formatted URL and parameters
        """
        root = "forecasts" if self.report_type == "taf" else "observations"
        return self.url.format(root, self.report_type, station), None

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts the report using string finding
        """
        raw = raw[raw.find(station) :]
        return raw[: raw.find('"')]


class NOAA_Scrape(ScrapeService):
    """
    Requests data from NOAA via site scraping
    """

    url = "https://aviationweather.gov/{}/data"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """
        Returns a formatted URL and parameters
        """
        hours = 7 if self.report_type == "taf" else 2
        return (
            self.url.format(self.report_type),
            {"ids": station, "format": "raw", "hours": hours},
        )

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts the report using string finding
        """
        raw = raw[raw.find("<code>") :]
        raw = raw[raw.find(station) :]
        raw = raw[: raw.find("</code>")]
        for char in ("<br/>", "&nbsp;"):
            raw = raw.replace(char, " ")
        return raw


NOAA = NOAA_Scrape


# Regional data sources


class AMO(ScrapeService):
    """
    Requests data from AMO KMA for Korean stations
    """

    url = "http://amoapi.kma.go.kr/amoApi/{}"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """
        Returns a formatted URL and parameters
        """
        return self.url.format(self.report_type), {"icao": station}

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts the report message from XML response
        """
        resp = parsexml(raw)
        try:
            report = resp["response"]["body"]["items"]["item"][
                self.report_type.lower() + "Msg"
            ]
        except KeyError:
            raise self._make_err(raw)
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


class MAC(ScrapeService):
    """
    Requests data from Meteorologia Aeronautica Civil for Columbian stations
    """

    url = "http://meteorologia.aerocivil.gov.co/expert_text_query/parse"
    method = "POST"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """
        Returns a formatted URL and parameters
        """
        return self.url, {"query": f"{self.report_type} {station}"}

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts the report message using string finding
        """
        report = raw[raw.find(station.upper() + " ") :]
        report = report[: report.find(" =")]
        return report


class AUBOM(ScrapeService):
    """
    Requests data from the Australian Bureau of Meteorology
    """

    url = "http://www.bom.gov.au/aviation/php/process.php"
    method = "POST"

    def _make_url(self, _) -> Tuple[str, dict]:
        """
        Returns a formatted URL and empty parameters
        """
        return self.url, None

    @staticmethod
    def _post_data(station: str) -> dict:
        """
        Returns the POST form
        """
        return {"keyword": station, "type": "search", "page": "TAF"}

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts the reports from HTML response
        """
        index = 1 if self.report_type == "taf" else 2
        try:
            report = raw.split("<p")[index]
            report = report[report.find(">") + 1 :]
        except IndexError:
            raise self._make_err("The station might not exist")
        if report.startswith("<"):
            return ""
        report = report[: report.find("</p>")]
        return report.replace("<br />", " ")


PREFERRED = {"RK": AMO, "SK": MAC}
BY_COUNTRY = {"AU": AUBOM}


def get_service(station: str, country_code: str) -> Service:
    """
    Returns the preferred service for a given station
    """
    for prefix in PREFERRED:
        if station.startswith(prefix):
            return PREFERRED[prefix]
    return BY_COUNTRY.get(country_code, NOAA)
