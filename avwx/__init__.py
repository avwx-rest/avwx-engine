"""
Aviation weather report parsing library
"""

# stdlib
import json
from abc import abstractmethod
from copy import copy
from datetime import datetime
from os import path
# module
from avwx import metar, taf, translate, summary, speech, service, structs
from avwx.core import valid_station
from avwx.exceptions import BadStation

INFO_PATH = path.dirname(path.realpath(__file__)) + '/stations.json'
STATIONS = json.load(open(INFO_PATH))


class Report(object):
    """
    Base report to take care of service assignment and station info
    """

    #: UTC Datetime object when the report was last updated
    last_updated: datetime = None

    #: The unparsed report string. Fetched on update()
    raw: str = None

    #: ReportData dataclass of parsed data values and units. Parsed on update()
    data: structs.ReportData = None

    #: ReportTrans dataclass of translation strings from data. Parsed on update()
    translations: structs.ReportTrans = None

    #: Units inferred from the station location and report contents
    units: structs.Units = None

    _station_info: structs.StationInfo = None

    def __init__(self, station: str):
        # Raises a BadStation error if needed
        valid_station(station)

        #: Service object used to fetch the report string
        self.service = service.get_service(station)(self.__class__.__name__.lower())
        
        #: 4-character ICAO station ident code the report was initialized with
        self.station = station

    @property
    def station_info(self) -> structs.StationInfo:
        """
        Provide basic station info

        Raises a BadStation exception if the station's info cannot be found
        """
        if self._station_info is None:
            if not self.station in STATIONS:
                raise BadStation('Could not find station in the info dict. Check avwx.STATIONS')
            info = copy(STATIONS[self.station])
            if info['runways']:
                info['runways'] = [structs.Runway(**r) for r in info['runways']]
            self._station_info = structs.StationInfo(**info)
        return self._station_info

    @abstractmethod
    def _post_update(self):
        pass

    @classmethod
    def from_report(cls, report: str) -> 'Report':
        """
        Returns an updated report object based on an existing report
        """
        obj = cls(report[:4])
        obj.update(report)
        return obj

    def update(self, report: str = None) -> bool:
        """Updates raw, data, and translations by fetching and parsing the report

        Can accept a report string to parse instead

        Returns True is a new report is available, else False
        """
        if not report:
            report = self.service.fetch(self.station)
        if report == self.raw:
            return False
        self.raw = report
        self._post_update()
        return True

    async def async_update(self) -> bool:
        """
        Async version of update
        """
        report = await self.service.async_fetch(self.station)
        if report == self.raw:
            return False
        self.raw = report
        self._post_update()
        return True

    def __repr__(self) -> str:
        return f'<avwx.{self.__class__.__name__} station={self.station}>'


class Metar(Report):
    """
    Class to handle METAR report data
    """

    def _post_update(self):
        self.data, self.units = metar.parse(self.station, self.raw)
        self.translations = translate.metar(self.data, self.units)
        self.last_updated = datetime.utcnow()

    @property
    def summary(self) -> str:
        """
        Condensed report summary created from translations
        """
        if not self.translations:
            self.update()
        return summary.metar(self.translations)

    @property
    def speech(self) -> str:
        """
        Report summary designed to be read by a text-to-speech program
        """
        if not self.data:
            self.update()
        return speech.metar(self.data, self.units)


class Taf(Report):
    """
    Class to handle TAF report data
    """

    def _post_update(self):
        self.data, self.units = taf.parse(self.station, self.raw)
        self.translations = translate.taf(self.data, self.units)
        self.last_updated = datetime.utcnow()

    @property
    def summary(self) -> [str]:
        """
        Condensed summary for each forecast created from translations
        """
        if not self.translations:
            self.update()
        return [summary.taf(trans) for trans in self.translations.forecast]

    @property
    def speech(self) -> str:
        """
        Report summary designed to be read by a text-to-speech program
        """
        if not self.data:
            self.update()
        return speech.taf(self.data, self.units)
