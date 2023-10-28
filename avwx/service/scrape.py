"""
These services request reports via HTML scraping or direct API requests.
Requests are ephemeral and will call the selected service each time.
"""

# pylint: disable=arguments-differ,invalid-name,too-many-arguments

# stdlib
import asyncio as aio
import json
import random
import re
from contextlib import suppress
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

# library
from xmltodict import parse as parsexml  # type: ignore

# module
from avwx.parsing.core import dedupe
from avwx.exceptions import InvalidRequest
from avwx.service.base import CallsHTTP, Service
from avwx.station import valid_station, Station
from avwx.structs import Coord


_T = TypeVar("_T")


_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
]


class ScrapeService(Service, CallsHTTP):  # pylint: disable=too-few-public-methods
    """Service class for fetching reports via direct web requests

    Unless overwritten, this class accepts `"metar"` and `"taf"` as valid report types
    """

    default_timeout = 10
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

    def _clean_report(self, report: _T) -> _T:
        """Replaces all *whitespace elements with a single space if enabled"""
        if not self._strip_whitespace:
            return report
        if isinstance(report, list):
            return dedupe(" ".join(r.split()) for r in report)  # type: ignore
        return " ".join(report.split()) if isinstance(report, str) else report  # type: ignore


class StationScrape(ScrapeService):
    """Service class fetching reports from a station code"""

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        raise NotImplementedError()

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report string from the service response"""
        raise NotImplementedError()

    def _simple_extract(self, raw: str, starts: Union[str, List[str]], end: str) -> str:
        """Simple extract by cutting at sequential start and end points"""
        targets = [starts] if isinstance(starts, str) else starts
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


class NOAA_FTP(StationScrape):
    """Requests data from NOAA via FTP"""

    _url = "https://tgftp.nws.noaa.gov/data/{}/{}/stations/{}.TXT"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        root = "forecasts" if self.report_type == "taf" else "observations"
        return self._url.format(root, self.report_type, station), {}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report using string finding"""
        raw = raw[raw.find(station) :]
        return raw[: raw.find('"')]


class _NOAA_ScrapeURL:
    """Mixin implementing NOAA scrape service URL"""

    # pylint: disable=too-few-public-methods

    report_type: str
    _url = "https://aviationweather.gov/cgi-bin/data/{}.php"

    def _make_url(self, station: str, **kwargs: Union[int, str]) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        hours = 7 if self.report_type == "taf" else 2
        params = {"ids": station, "format": "raw", "hours": hours, **kwargs}
        return self._url.format(self.report_type), params


class NOAA_Scrape(_NOAA_ScrapeURL, StationScrape):
    """Requests data from NOAA via response scraping"""

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the first report"""
        report = ""
        for line in raw.strip().split("\n"):
            # Break when seeing the second non-indented line (next report)
            if line and line[0].isalnum() and report:
                break
            report += line
        return report


class NOAA_ScrapeList(_NOAA_ScrapeURL, ScrapeService):
    """Request listed data from NOAA via response scraping"""

    _valid_types = ("pirep",)

    def _extract(self, raw: str, station: str) -> List[str]:
        """Extracts the report strings"""
        return raw.strip().split("\n")

    async def _fetch(
        self, station: str, url: str, params: dict, timeout: int
    ) -> List[str]:
        headers = self._make_headers()
        data = self._post_data(station) if self.method.lower() == "post" else None
        text = await self._call(
            url, params=params, headers=headers, data=data, timeout=timeout
        )
        report = self._extract(text, station)
        return self._clean_report(report)

    def fetch(
        self,
        icao: Optional[str] = None,
        coord: Optional[Coord] = None,
        radius: int = 10,
        timeout: Optional[int] = None,
    ) -> List[str]:
        """Fetches a report string from the service"""
        return aio.run(self.async_fetch(icao, coord, radius, timeout))

    async def async_fetch(
        self,
        icao: Optional[str] = None,
        coord: Optional[Coord] = None,
        radius: int = 10,
        timeout: Optional[int] = None,
    ) -> List[str]:
        """Asynchronously fetch a report string from the service"""
        if timeout is None:
            timeout = self.default_timeout
        station: str
        if icao:
            valid_station(icao)
            station = icao
        elif coord:
            if ret := Station.nearest(coord.lat, coord.lon, max_coord_distance=radius):
                station = ret[0].icao or ""
            else:
                raise ValueError(
                    f"No reference station near enough to {coord} to call service"
                )
        url, params = self._make_url(station, distance=radius)
        return await self._fetch(station, url, params, timeout)


NOAA = NOAA_Scrape


# Regional data sources


class AMO(StationScrape):
    """Requests data from AMO KMA for Korean stations"""

    _url = "http://amoapi.kma.go.kr/amoApi/{}"
    default_timeout = 60

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        return self._url.format(self.report_type), {"icao": station}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report message from XML response"""
        resp = parsexml(raw)
        try:
            report = resp["response"]["body"]["items"]["item"][
                f"{self.report_type.lower()}Msg"
            ]
        except KeyError as key_error:
            raise self._make_err(raw) from key_error
        if not report:
            raise self._make_err("The station might not exist")
        # Replace line breaks
        report = report.replace("\n", "")
        # Remove excess leading and trailing data
        for item in (self.report_type.upper(), "SPECI"):
            if report.startswith(f"{item} "):
                report = report[len(item) + 1 :]
        report = report.rstrip("=")
        # Make every element single-spaced and stripped
        return " ".join(report.split())


class MAC(StationScrape):
    """Requests data from Meteorologia Aeronautica Civil for Columbian stations"""

    _url = "http://meteorologia.aerocivil.gov.co/expert_text_query/parse"
    method = "POST"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        return self._url, {"query": f"{self.report_type} {station}"}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report message using string finding"""
        return self._simple_extract(raw, f"{station.upper()} ", "=")


class AUBOM(StationScrape):
    """Requests data from the Australian Bureau of Meteorology"""

    _url = "http://www.bom.gov.au/aviation/php/process.php"
    method = "POST"

    def _make_url(self, _: Any) -> Tuple[str, dict]:
        """Returns a formatted URL and empty parameters"""
        return self._url, {}

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
            "User-Agent": random.choice(_USER_AGENTS),
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

    # _url = "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/showopmetquery.php"
    # method = "POST"

    # Temp redirect
    _url = "https://avbrief3.el.r.appspot.com/"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and empty parameters"""
        return self._url, {"icao": station}

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
            "User-Agent": random.choice(_USER_AGENTS),
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

    _url = "https://www.northavimet.com/NamConWS/rest/opmet/command/0/"

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and empty parameters"""
        return self._url + station, {}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the reports from HTML response"""
        starts = [f"<b>{self.report_type.upper()} <", f">{station.upper()}<", "<b> "]
        report = self._simple_extract(raw, starts, "=")
        return station + report[3:]


class AVT(StationScrape):
    """Requests data from AVT/XiamenAir for China
    NOTE: This should be replaced later with a gov+https source
    """

    _url = "http://www.avt7.com/Home/AirportMetarInfo?airport4Code="

    def _make_url(self, station: str) -> Tuple[str, dict]:
        """Returns a formatted URL and empty parameters"""
        return self._url + station, {}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the reports from HTML response"""
        try:
            data = json.loads(raw)
            key = f"{self.report_type.lower()}ContentList"
            text: str = data[key]["rows"][0]["content"]
            return text
        except (TypeError, json.decoder.JSONDecodeError, KeyError, IndexError):
            return ""


# Ancilary scrape services


_TAG_PATTERN = re.compile(r"<[^>]*>")

# Search fields https://notams.aim.faa.gov/NOTAM_Search_User_Guide_V33.pdf


class FAA_NOTAM(ScrapeService):
    """Sources NOTAMs from official FAA portal"""

    _url = "https://notams.aim.faa.gov/notamSearch/search"
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
            f"{prefix}Degrees": abs(degree),
            f"{prefix}Minutes": minute,
            f"{prefix}Seconds": second,
            f"{key}Direction": direction,
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
            text = await self._call(self._url, None, headers, data, timeout)
            resp: dict = json.loads(text)
            if resp.get("error"):
                raise self._make_err("Search criteria appears to be invalid")
            for item in resp["notamList"]:
                if report := item.get("icaoMessage", "").strip():
                    report = _TAG_PATTERN.sub("", report).strip()
                    if issued := item.get("issueDate"):
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
    """Returns the preferred scrape service for a given station

    ```python
    # Fetch Australian reports
    station = 'YWOL'
    country = 'AU' # can source from avwx.Station.country
    # Get the station's preferred service and initialize to fetch METARs
    service = avwx.service.get_service(station, country)('metar')
    # service is now avwx.service.AUBOM init'd to fetch METARs
    # Fetch the current METAR
    report = service.fetch(station)
    ```
    """
    with suppress(KeyError):
        return PREFERRED[station[:2]]  # type: ignore
    return BY_COUNTRY.get(country_code, NOAA)  # type: ignore
