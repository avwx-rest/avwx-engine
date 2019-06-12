"""
Classes for retrieving raw report strings
"""

# stdlib
from abc import abstractmethod
from urllib import request
from urllib.error import URLError
from urllib.parse import urlencode

# library
import aiohttp
from xmltodict import parse as parsexml

# module
from avwx._core import dedupe
from avwx.exceptions import InvalidRequest, SourceError
from avwx.station import valid_station

_atimeout = aiohttp.ClientTimeout(total=10)


class Service(object):
    """
    Base Service class for fetching reports
    """

    # Service URL must accept report type and station via .format()
    url: str = None
    method: str = "GET"

    _valid_types = ("metar", "taf")

    def __init__(self, request_type: str):
        if request_type not in self._valid_types:
            raise ValueError(
                f"{request_type} is not a valid report type for {self.__class__.__name__}"
            )
        self.rtype = request_type

    def make_err(self, body: str, key: str = "report path") -> InvalidRequest:
        """
        Returns an InvalidRequest exception with formatted error message
        """
        msg = f"Could not find {key} in {self.__class__.__name__} response\n"
        return InvalidRequest(msg + body)

    @abstractmethod
    def _make_url(self, station: str, lat: float, lon: float) -> (str, dict):
        raise NotImplementedError()

    @abstractmethod
    def _extract(self, raw: str, station: str = None) -> str:
        raise NotImplementedError()

    def fetch(self, station: str = None, lat: float = None, lon: float = None) -> str:
        """
        Fetches a report string from the service
        """
        if station:
            valid_station(station)
        elif lat is None or lon is None:
            raise ValueError("No valid fetch parameters")
        try:
            url, params = self._make_url(station, lat, lon)
            url += "?" + urlencode(params)
            # Non-null data signals a POST request
            data = {} if self.method == "POST" else None
            resp = request.urlopen(url, data=data, timeout=10)
            if resp.status != 200:
                raise SourceError(
                    f"{self.__class__.__name__} server returned {resp.status}"
                )
        except URLError:
            raise ConnectionError(
                f"Unable to connect to {self.__class__.__name__} server"
            )
        report = self._extract(resp.read().decode("utf-8"), station)
        # This split join replaces all *whitespace elements with a single space
        if isinstance(report, list):
            return dedupe(" ".join(r.split()) for r in report)
        return " ".join(report.split())

    async def async_fetch(
        self, station: str = None, lat: float = None, lon: float = None
    ) -> str:
        """
        Asynchronously fetch a report string from the service
        """
        if station:
            valid_station(station)
        elif lat is None or lon is None:
            raise ValueError("No valid fetch parameters")
        url, params = self._make_url(station, lat, lon)
        try:
            async with aiohttp.ClientSession(timeout=_atimeout) as sess:
                async with getattr(sess, self.method.lower())(
                    url, params=params
                ) as resp:
                    if resp.status != 200:
                        raise SourceError(
                            f"{self.__class__.__name__} server returned {resp.status}"
                        )
                    text = await resp.text()
        except aiohttp.ClientConnectionError:
            raise ConnectionError(
                f"Unable to connect to {self.__class__.__name__} server"
            )
        report = self._extract(text, station)
        # This split join replaces all *whitespace elements with a single space
        if isinstance(report, list):
            return dedupe(" ".join(r.split()) for r in report)
        return " ".join(report.split())


class NOAA(Service):
    """
    Requests data from NOAA ADDS
    """

    url = "https://aviationweather.gov/adds/dataserver_current/httpparam"

    _valid_types = ("metar", "taf", "aircraftreport")
    _rtype_map = {"airep": "aircraftreport"}
    _targets = {"metar": "METAR", "taf": "TAF", "aircraftreport": "AircraftReport"}
    _coallate = ("aircraftreport",)

    def __init__(self, request_type: str):
        if request_type in self._rtype_map:
            request_type = self._rtype_map[request_type]
        super().__init__(request_type)

    def _make_url(self, station: str, lat: float, lon: float) -> (str, dict):
        """
        Returns a formatted URL and parameters
        """
        # Base request params
        params = {
            "requestType": "retrieve",
            "format": "XML",
            "hoursBeforeNow": 2,
            "dataSource": self.rtype + "s",
        }
        if self.rtype == "aircraftreport":
            params["radialDistance"] = f"200;{lon},{lat}"
        else:
            params["stationString"] = station
        return self.url, params

    def _report_strip(self, report: str) -> str:
        """
        Remove excess leading and trailing data
        """
        for item in (self.rtype.upper(), "SPECI"):
            if report.startswith(item + " "):
                report = report[len(item) + 1 :]
        return report

    def _extract(self, raw: str, station: str = None) -> "str|[str]":
        """
        Extracts the raw_report element from XML response
        """
        resp = parsexml(raw)
        try:
            data = resp["response"]["data"]
            if data["@num_results"] == "0":
                return ""
            reports = data[self._targets[self.rtype]]
        except KeyError:
            raise self.make_err(raw)
        # Only one report exists
        if isinstance(reports, dict):
            ret = self._report_strip(reports["raw_text"])
            if self.rtype in self._coallate:
                ret = [ret]
        # Multiple reports exist
        elif isinstance(reports, list) and reports:
            if self.rtype in self._coallate:
                ret = [self._report_strip(r["raw_text"]) for r in reports]
            else:
                ret = self._report_strip(reports[0]["raw_text"])
        # Something went wrong
        else:
            raise self.make_err(raw, '"raw_text"')
        return ret


class AMO(Service):
    """
    Requests data from AMO KMA for Korean stations
    """

    url = "http://amoapi.kma.go.kr/amoApi/{}"

    def _make_url(self, station: str, lat: float, lon: float) -> (str, dict):
        """
        Returns a formatted URL and parameters
        """
        return self.url.format(self.rtype), {"icao": station}

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts the report message from XML response
        """
        resp = parsexml(raw)
        try:
            report = resp["response"]["body"]["items"]["item"][
                self.rtype.lower() + "Msg"
            ]
        except KeyError:
            raise self.make_err(raw)
        if not report:
            raise self.make_err("The station might not exist")
        # Replace line breaks
        report = report.replace("\n", "")
        # Remove excess leading and trailing data
        for item in (self.rtype.upper(), "SPECI"):
            if report.startswith(item + " "):
                report = report[len(item) + 1 :]
        report = report.rstrip("=")
        # Make every element single-spaced and stripped
        return " ".join(report.split())


class MAC(Service):
    """
    Requests data from Meteorologia Aeronautica Civil for Columbian stations
    """

    url = "http://meteorologia.aerocivil.gov.co/expert_text_query/parse"
    method = "POST"

    def _make_url(self, station: str, lat: float, lon: float) -> (str, dict):
        """
        Returns a formatted URL and parameters
        """
        return self.url, {"query": f"{self.rtype} {station}"}

    def _extract(self, raw: str, station: str) -> str:
        """
        Extracts the reports message using string finding
        """
        report = raw[raw.find(station.upper() + " ") :]
        report = report[: report.find(" =")]
        return report


PREFERRED = {"RK": AMO, "SK": MAC}


def get_service(station: str) -> Service:
    """
    Returns the preferred service for a given station
    """
    for prefix in PREFERRED:
        if station.startswith(prefix):
            return PREFERRED[prefix]
    return NOAA
