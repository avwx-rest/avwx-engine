"""
Classes for retrieving raw report strings via web scraping
"""

# pylint: disable=arguments-differ,invalid-name,too-many-arguments

# stdlib
import asyncio as aio
import json
import random
import re
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

# library
from xmltodict import parse as parsexml  # type: ignore

# module
from avwx.parsing.core import dedupe
from avwx.exceptions import InvalidRequest
from avwx.service.base import CallsHTTP, Service
from avwx.station import valid_station
from avwx.structs import Coord


T = TypeVar("T")


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

    def _post_data(self, station: str) -> dict:  # pylint: disable=unused-argument
        """Returns the POST form/data payload"""
        return {}

    def _clean_report(self, report: T) -> T:
        """Replaces all *whitespace elements with a single space if enabled"""
        if not self._strip_whitespace:
            return report
        if isinstance(report, list):
            return dedupe(" ".join(r.split()) for r in report)  # type: ignore
        if isinstance(report, str):
            return " ".join(report.split())  # type: ignore
        return report


class StationScrape(ScrapeService):
    """Service class fetching reports from a station code"""

    default_timeout = 10

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        raise NotImplementedError()

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report string from the service response"""
        raise NotImplementedError()

    def _simple_extract(self, raw: str, starts: Union[str, List[str]], end: str) -> str:
        """Simple extract by cutting at sequential start and end points"""
        if isinstance(starts, str):
            targets = [starts]
        else:
            targets = starts
        for target in targets:
            index = raw.find(target)
            if index == -1:
                raise self._make_err("The station might not exist")
            raw = raw[index:]
        report = raw[: raw.find(end)].strip()
        return " ".join(dedupe(report.split()))

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
        timeout: Optional[int] = None,
    ) -> str:
        """Fetches a report string from the service"""
        return aio.run(self.async_fetch(station, timeout))

    async def async_fetch(self, station: str, timeout: Optional[int] = None) -> str:
        """Asynchronously fetch a report string from the service"""
        if timeout is None:
            timeout = self.default_timeout
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
        self, station: Optional[str], coord: Optional[Coord]
    ) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        # Base request params
        params = {
            "requestType": "retrieve",
            "format": "XML",
            "hoursBeforeNow": 2,
            "dataSource": self.report_type + "s",
        }
        if self.report_type == "aircraftreport" and coord is not None:
            params["radialDistance"] = f"200;{coord.lon},{coord.lat}"
        else:
            params["stationString"] = station
        return self.url, params

    def _extract(self, raw: str) -> Union[str, List[str]]:
        """Extracts the raw_report element from XML response"""
        ret: Union[str, List[str]]
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
            if self.report_type in self._coallate and isinstance(ret, str):
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
        station: Optional[str] = None,
        coord: Optional[Coord] = None,
        timeout: int = 10,
    ) -> Union[str, List[str]]:
        """Fetches a report string from the service"""
        return aio.run(self.async_fetch(station, coord, timeout))

    async def async_fetch(
        self,
        station: Optional[str] = None,
        coord: Optional[Coord] = None,
        timeout: int = 10,
    ) -> Union[str, List[str]]:
        """Asynchronously fetch a report string from the service"""
        if station:
            valid_station(station)
        elif coord is None:
            raise ValueError("No valid fetch parameters")
        url, params = self._make_url(station, coord)
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
    default_timeout = 60

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
        return self._simple_extract(raw, station.upper() + " ", "=")


class AUBOM(StationScrape):
    """Requests data from the Australian Bureau of Meteorology"""

    url = "http://www.bom.gov.au/aviation/php/process.php"
    method = "POST"

    def _make_url(self, _: Any) -> Tuple[str, dict]:
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
        return self._simple_extract(
            raw, [f">{self.report_type.upper()}</div>", station], "="
        )


class NAM(StationScrape):
    """Requests data from NorthAviMet for North Atlantic and Nordic countries"""

    url = "https://www.northavimet.com/NamConWS/rest/opmet/command/0/"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and empty parameters"""
        return self.url + station, {}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the reports from HTML response"""
        starts = [f"<b>{self.report_type.upper()} <", f">{station.upper()}<", "<b> "]
        report = self._simple_extract(raw, starts, "=")
        return station + report[3:]


class AVT(StationScrape):
    """Requests data from AVT/XiamenAir for China
    NOTE: This should be replaced later with a gov+https source
    """

    url = "http://www.avt7.com/Home/AirportMetarInfo?airport4Code="

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and empty parameters"""
        return self.url + station, {}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the reports from HTML response"""
        try:
            data = json.loads(raw)
            key = self.report_type.lower() + "ContentList"
            text: str = data[key]["rows"][0]["content"]
            return text
        except (TypeError, json.decoder.JSONDecodeError, KeyError, IndexError):
            return ""


# Ancilary scrape services


TAG_PATTERN = re.compile(r"<[^>]*>")

# Search fields https://notams.aim.faa.gov/NOTAM_Search_User_Guide_V33.pdf


class FAA_NOTAM(ScrapeService):
    """Sources NOTAMs from official FAA portal"""

    url = "https://notams.aim.faa.gov/notamSearch/search"
    method = "POST"
    _valid_types = ("notam",)

    @staticmethod
    def _make_headers() -> dict:
        return {"Content-Type": "application/x-www-form-urlencoded"}

    @staticmethod
    def _split_coord(prefix: str, value: float) -> dict:
        """Adds coordinate deg/min/sec fields per float value"""
        degree, minute, second = Coord.to_dms(value)
        if prefix == "lat":
            key = "latitude"
            direction = "N" if degree >= 0 else "S"
        else:
            key = "longitude"
            direction = "E" if degree >= 0 else "W"
        return {
            prefix + "Degrees": abs(degree),
            prefix + "Minutes": minute,
            prefix + "Seconds": second,
            key + "Direction": direction,
        }

    def _post_for(
        self,
        icao: Optional[str] = None,
        coord: Optional[Coord] = None,
        path: Optional[List[str]] = None,
        radius: int = 10,
    ) -> dict:
        """Generate POST payload for search params in location order"""
        data: Dict[str, Any] = {"notamsOnly": False, "radius": radius}
        if icao:
            data["searchType"] = 0
            data["designatorsForLocation"] = icao
        elif coord:
            data["searchType"] = 3
            data["radiusSearchOnDesignator"] = False
            data.update(self._split_coord("lat", coord.lat))
            data.update(self._split_coord("long", coord.lon))
        elif path:
            data["searchType"] = 6
            data["flightPathText"] = " ".join(path)
            data["flightPathBuffer"] = radius
            data["flightPathIncludeNavaids"] = True
            data["flightPathIncludeArtcc"] = False
            data["flightPathIncludeTfr"] = True
            data["flightPathIncludeRegulatory"] = False
            data["flightPathResultsType"] = "All NOTAMs"
        else:
            raise InvalidRequest("Not enough info to request NOTAM data")
        return data

    def fetch(
        self,
        icao: Optional[str] = None,
        coord: Optional[Coord] = None,
        path: Optional[List[str]] = None,
        radius: int = 10,
        timeout: int = 10,
    ) -> List[str]:
        """Fetch NOTAM list from the service via ICAO, coordinate, or ident path"""
        return aio.run(self.async_fetch(icao, coord, path, radius, timeout))

    async def async_fetch(
        self,
        icao: Optional[str] = None,
        coord: Optional[Coord] = None,
        path: Optional[List[str]] = None,
        radius: int = 10,
        timeout: int = 10,
    ) -> List[str]:
        """Async fetch NOTAM list from the service via ICAO, coordinate, or ident path"""
        headers = self._make_headers()
        data = self._post_for(icao, coord, path, radius)
        notams = []
        while True:
            text = await self._call(self.url, None, headers, data, timeout)
            resp: dict = json.loads(text)
            if resp.get("error"):
                raise self._make_err("Search criteria appears to be invalid")
            for item in resp["notamList"]:
                report = item.get("icaoMessage", "").strip()
                if report:
                    report = TAG_PATTERN.sub("", report).strip()
                    issued = item.get("issueDate")
                    if issued:
                        report = f"{issued}||{report}"
                    notams.append(report)
            offset = resp["endRecordCount"]
            if not notams or offset >= resp["totalNotamCount"]:
                break
            data["offset"] = offset
        return notams


PREFERRED = {
    "RK": AMO,
    "SK": MAC,
}
BY_COUNTRY = {
    "AU": AUBOM,
    # "CN": AVT,
    "DK": NAM,
    "EE": NAM,
    "FI": NAM,
    "FO": NAM,
    "GL": NAM,
    "IN": OLBS,
    "IS": NAM,
    "LV": NAM,
    "NO": NAM,
    "SE": NAM,
}


def get_service(station: str, country_code: str) -> ScrapeService:
    """Returns the preferred service for a given station"""
    for prefix, service in PREFERRED.items():
        if station.startswith(prefix):
            return service  # type: ignore
    return BY_COUNTRY.get(country_code, NOAA)  # type: ignore
