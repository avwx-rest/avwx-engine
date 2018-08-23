"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/__init__.py

Contains the primary report classes of avwx: Metar and Taf
"""

# stdlib
import json
from datetime import datetime
from os import path
# module
from avwx import metar, taf, translate, summary, speech, service, structs
from avwx.core import valid_station
from avwx.exceptions import BadStation
from avwx.static import INFO_KEYS

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
            info = [self.station] + STATIONS[self.station]
            self._station_info = structs.StationInfo(**dict(zip(INFO_KEYS, info)))
        return self._station_info

    def update(self, report: str = None) -> bool:
        """
        Updates report elements. Not implemented
        """
        raise NotImplementedError()


class Metar(Report):
    """
    Class to handle METAR report data
    """

    def update(self, report: str = None) -> bool:
        """Updates raw, data, and translations by fetching and parsing the METAR report

        Returns True is a new report is available, else False
        """
        if report is not None:
            self.raw = report
        else:
            raw = self.service.fetch(self.station)
            if raw == self.raw:
                return False
            self.raw = raw
        self.data, self.units = metar.parse(self.station, self.raw)
        self.translations = translate.metar(self.data, self.units)
        self.last_updated = datetime.utcnow()
        return True

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

    def update(self, report: str = None) -> bool:
        """
        Updates raw, data, and translations by fetching and parsing the TAF report

        Returns True is a new report is available, else False
        """
        if report is not None:
            self.raw = report
        else:
            raw = self.service.fetch(self.station)
            if raw == self.raw:
                return False
            self.raw = raw
        self.data, self.units = taf.parse(self.station, self.raw)
        self.translations = translate.taf(self.data, self.units)
        self.last_updated = datetime.utcnow()
        return True

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
