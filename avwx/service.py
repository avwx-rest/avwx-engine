"""
Classes for retrieving raw report strings
"""

# stdlib
from urllib import request
from urllib.error import URLError
# library
import aiohttp
from xmltodict import parse as parsexml
# module
from avwx.core import valid_station
from avwx.exceptions import InvalidRequest, SourceError

class Service(object):
    """
    Base Service class for fetching reports
    """

    # Service URL must accept report type and station via .format()
    url: str = None
    method: str = 'GET'

    def __init__(self, request_type: str):
        self.rtype = request_type

    def make_err(self, body: str, key: str = 'report path') -> InvalidRequest:
        """
        Returns an InvalidRequest exception with formatted error message
        """
        msg = f'Could not find {key} in {self.__class__.__name__} response\n'
        return InvalidRequest(msg + body)

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts report from response. Implemented by child classes
        """
        raise NotImplementedError()

    def fetch(self, station: str) -> str:
        """
        Fetches a report string from the service
        """
        valid_station(station)
        try:
            url = self.url.format(self.rtype, station)
            # Non-null data signals a POST request
            data = {} if self.method == 'POST' else None
            resp = request.urlopen(request.Request(url, data=data))
            if resp.status != 200:
                raise SourceError(f'{self.__class__.__name__} server returned {resp.status}')
        except URLError:
            raise ConnectionError(f'Unable to connect to {self.__class__.__name__} server')
        report = self._extract(resp.read().decode('utf-8'), station)
        # This split join replaces all *whitespace elements with a single space
        return ' '.join(report.split())

    async def async_fetch(self, station: str) -> str:
        """
        Asynchronously fetch a report string from the service
        """
        valid_station(station)
        url = self.url.format(self.rtype, station)
        try:
            async with aiohttp.ClientSession() as sess:
                async with getattr(sess, self.method.lower())(url) as resp:
                    if resp.status != 200:
                        raise SourceError(f'{self.__class__.__name__} server returned {resp.status}')
                    text = await resp.text()
        except aiohttp.ClientConnectionError:
            raise ConnectionError(f'Unable to connect to {self.__class__.__name__} server')
        report = self._extract(text, station)
        # This split join replaces all *whitespace elements with a single space
        return ' '.join(report.split())


class NOAA(Service):
    """
    Requests data from NOAA ADDS
    """

    url = (
        'https://aviationweather.gov/adds/dataserver_current/httpparam'
        '?dataSource={0}s'
        '&requestType=retrieve'
        '&format=XML'
        '&stationString={1}'
        '&hoursBeforeNow=2'
    )

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts the raw_report element from XML response
        """
        resp = parsexml(raw)
        try:
            report = resp['response']['data'][self.rtype.upper()]
        except KeyError:
            raise self.make_err(raw)
        # Find report string
        if isinstance(report, dict):
            report = report['raw_text']
        elif isinstance(report, list) and report:
            report = report[0]['raw_text']
        else:
            raise self.make_err(raw, '"raw_text"')
        # Remove excess leading and trailing data
        for item in (self.rtype.upper(), 'SPECI'):
            if report.startswith(item + ' '):
                report = report[len(item)+1:]
        return report


class AMO(Service):
    """
    Requests data from AMO KMA for Korean stations
    """

    url = 'http://amoapi.kma.go.kr/amoApi/{0}?icao={1}'

    def _extract(self, raw: str, station: str = None) -> str:
        """
        Extracts the report message from XML response
        """
        resp = parsexml(raw)
        try:
            report = resp['response']['body']['items']['item'][self.rtype.lower() + 'Msg']
        except KeyError:
            raise self.make_err(raw)
        # Replace line breaks
        report = report.replace('\n', '')
        # Remove excess leading and trailing data
        for item in (self.rtype.upper(), 'SPECI'):
            if report.startswith(item + ' '):
                report = report[len(item)+1:]
        report = report.rstrip('=')
        # Make every element single-spaced and stripped
        return ' '.join(report.split())


class MAC(Service):
    """
    Requests data from Meteorologia Aeronautica Civil for Columbian stations
    """

    url = 'http://meteorologia.aerocivil.gov.co/expert_text_query/parse?query={0}%20{1}'
    method = 'POST'

    def _extract(self, raw: str, station: str) -> str:
        """
        Extracts the reports message using string finding
        """
        report = raw[raw.find(station.upper() + ' '):]
        report = report[:report.find(' =')]
        return report


PREFERRED = {
    'RK': AMO,
    'SK': MAC,
}


def get_service(station: str) -> Service:
    """
    Returns the preferred service for a given station
    """
    for prefix in PREFERRED:
        if station.startswith(prefix):
            return PREFERRED[prefix]
    return NOAA
