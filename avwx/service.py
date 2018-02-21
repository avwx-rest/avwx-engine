"""
Classes for retrieving raw report strings
"""

# library
import requests
from xmltodict import parse as parsexml
# module
from avwx.core import valid_station
from avwx.exceptions import InvalidRequest

class Service(object):
    """
    Base Service class for fetching reports
    """

    # Service URL must accept report type and station via .format()
    url: str = None

    def __init__(self, request_type: str):
        self.rtype = request_type

    def make_err(self, body: str, key: str = 'report path') -> InvalidRequest:
        """
        Returns an InvalidRequest exception with formatted error message
        """
        msg = f'Could not find {key} in {self.__class__.__name__} response\n'
        return InvalidRequest(msg + body)

    def _extract(self, raw: str) -> str:
        """
        Extracts report from response. Implemented by child classes
        """
        raise NotImplementedError()

    def fetch(self, station: str) -> str:
        """
        Fetches a report string from the service
        """
        valid_station(station)
        resp = requests.get(self.url.format(self.rtype, station)).text
        return self._extract(resp)


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

    def _extract(self, raw: str) -> str:
        """
        Extracts the raw_report element from XML response
        """
        resp = parsexml(raw)
        try:
            report = resp['response']['data'][self.rtype.upper()]
        except:
            raise self.make_err(raw)
        if isinstance(report, dict):
            return report['raw_text']
        elif isinstance(report, list) and report:
            return report[0]['raw_text']
        else:
            raise self.make_err(raw, '"raw_text"')


class AMO(Service):
    """
    Requests data from AMO KMA for Korean stations
    """

    url = 'https://amoapi.kma.go.kr/amoApi/{0}?icao={1}'

    def _extract(self, raw: str) -> str:
        """
        Extracts the report message from XML response
        """
        resp = parsexml(raw)
        try:
            report = resp['response']['body']['items']['item'][self.rtype.lower() + 'Msg']
        except:
            raise self.make_err(raw)
        # Replace line breaks
        report = report.replace('\n', '')
        # Remove excess leading and trailing data
        report = report.lstrip(self.rtype.upper()).rstrip('=')
        # Make every element single-spaced and stripped
        return ' '.join(report.split())


PREFERRED = {
    'RK': AMO
}


def get_service(station: str) -> Service:
    """
    Returns the preferred service for a given station
    """
    for prefix in PREFERRED:
        if station.startswith(prefix):
            return PREFERRED[prefix]
    return NOAA
