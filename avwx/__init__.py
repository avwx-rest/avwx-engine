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
from avwx import metar, taf, translate, summary, speech
from avwx.core import valid_station
from avwx.exceptions import BadStation

INFO_KEYS = ['ICAO', 'Country', 'State', 'City', 'Name', 'IATA',
              'Elevation', 'Latitude', 'Longitude', 'Priority']
INFO_PATH = path.dirname(path.realpath(__file__)) + '/stations.json'
STATIONS = json.load(open(INFO_PATH))


class Report:
    """Base report to take care of station info"""

    def __init__(self, station: str, lang: str=None):
        valid_station(station)
        self.station = station
        self.lang = lang
        self.last_updated = None
        self.raw = None
        self.data = None
        self.translations = None
        self._station_info = None

    @property
    def station_info(self):
        """Provide basic station info with the keys below"""
        if self._station_info is None:
            if not self.station in STATIONS:
                raise BadStation('Could not find station in the info dict. Check avwx.STATIONS')
            info = [self.station] + STATIONS[self.station]
            self._station_info = dict(zip(INFO_KEYS, info))
        return self._station_info


class Metar(Report):
    """Class to handle METAR report data"""

    def update(self, report: str=None) -> bool:
        """Updates raw, data, and translations by fetching and parsing the METAR report"""
        if report is not None:
            self.raw = report
        else:
            raw = metar.fetch(self.station)
            if raw == self.raw:
                return False
            self.raw = raw
        self.data = metar.parse(self.station, self.raw)
        self.translations = translate.metar(self.data)
        self.last_updated = datetime.utcnow()
        return True

    @property
    def summary(self):
        """Condensed report summary created from translations"""
        if not self.translations:
            self.update()
        return summary.metar(self.translations)

    @property
    def speech(self):
        """Report summary designed to be read by a text-to-speech program"""
        if not self.data:
            self.update()
        return speech.metar(self.data)


class Taf(Report):
    """Class to handle TAF report data"""

    def update(self, report: str=None) -> bool:
        """Updates raw, data, and translations by fetching and parsing the TAF report"""
        if report is not None:
            self.raw = report
        else:
            raw = taf.fetch(self.station)
            if raw == self.raw:
                return False
            self.raw = raw
        self.data = taf.parse(self.station, self.raw)
        self.translations = translate.taf(self.data)
        self.last_updated = datetime.utcnow()

    @property
    def summary(self):
        """Condensed summary for each forecast created from translations"""
        if not self.translations:
            self.update()
        return [summary.taf(trans) for trans in self.translations['Forecast']]
