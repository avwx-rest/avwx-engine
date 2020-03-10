"""
Report parent classes
"""

# stdlib
from abc import ABCMeta, abstractmethod
from datetime import datetime, timezone

# module
from avwx.service import Service
from avwx.station import Station, valid_station
from avwx.structs import ReportData, Units


class AVWXBase(metaclass=ABCMeta):
    """
    Abstract base class for AVWX report types
    """

    #: UTC Datetime object when the report was last updated
    last_updated: datetime = None

    #: 4-character ICAO station ident code the report was initialized with
    station: str

    #: Provide basic station info if given at init
    station_info: Station = None

    #: The original report string. Fetched on update()
    raw: str = None

    #: ReportData dataclass of parsed data values and units. Parsed on update()
    data: ReportData = None

    #: Units inferred from the station location and report contents
    units: Units = None

    #: Service object used to fetch the report string
    service: Service

    def __init__(self, icao: str):
        # Raises a BadStation error if needed
        valid_station(icao)
        self.station = icao
        self.station_info = Station.from_icao(icao)

    def __repr__(self) -> str:
        return f"<avwx.{self.__class__.__name__} station={self.station}>"

    @abstractmethod
    def _post_update(self):
        pass

    @classmethod
    def from_report(cls, report: str) -> "AVWXBase":
        """
        Returns an updated report object based on an existing report
        """
        report = report.strip()
        obj = cls(report[:4])
        obj.update(report)
        return obj

    def update(
        self, report: str = None, timeout: int = 10, disable_post: bool = False
    ) -> bool:
        """
        Updates raw, data, and translations by fetching and parsing the report

        Can accept a report string to parse instead

        Returns True if a new report is available, else False
        """
        if not report:
            report = self.service.fetch(self.station, timeout=timeout)
        if not report or report == self.raw:
            return False
        self.raw = report
        if not disable_post:
            self._post_update()
        self.last_updated = datetime.now(tz=timezone.utc)
        return True

    async def async_update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """
        Async version of update
        """
        report = await self.service.async_fetch(self.station, timeout=timeout)
        if not report or report == self.raw:
            return False
        self.raw = report
        if not disable_post:
            self._post_update()
        return True
