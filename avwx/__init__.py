"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/__init__.py
"""

# stdlib
from datetime import datetime
# module
from avwx import metar
from avwx.core import valid_station

class Report:
    """"""

    def __init__(self, station: str):
        valid_station(station)
        self.station = station
        self.last_updated = None
        self.raw = None
        self.data = None
        self.translations = None

class Metar(Report):
    """Class to handle METAR report data"""

    def update(self) -> bool:
        """Updates the """
        raw = metar.fetch(self.station)
        if raw == self.raw:
            return False
        self.raw = raw
        self.data = metar.parse(self.station, raw)
        #self.translations = translate.metar(self.data)
        self.last_updated = datetime.utcnow()
        return True

    # @property
    # def summary(self):
    #     if not self.translations:
    #         self.update()
    #     return summary.metar(self.translations)

    # @property
    # def speech(self):
    #     if not self.translations:
    #         self.update()
    #     return speech.metar(self.translations)

class Taf(Report):
    """Class to handle METAR report data"""

    def update(self) -> bool:
        """"""
        raise NotImplementedError()
