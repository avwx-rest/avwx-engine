"""
Report parent classes
"""

# stdlib
from abc import ABCMeta, abstractmethod
from datetime import date, datetime, timezone

# module
from avwx.exceptions import BadStation
from avwx.service import Service
from avwx.station import Station
from avwx.structs import ReportData, Units


def find_station(report: str) -> Station:
    """
    Returns the first ICAO ident found in a report string
    """
    for item in report.split():
        if len(item) == 4:
            try:
                return Station.from_icao(item.upper())
            except BadStation:
                pass
    return None


class AVWXBase(metaclass=ABCMeta):
    """
    Abstract base class for AVWX report types
    """

    #: UTC datetime object when the report was last updated
    last_updated: datetime = None

    #: UTC date object when the report was issued
    issued: date = None

    #: 4-character ICAO station ident code the report was initialized with
    icao: str = None

    #: Provide basic station info if given at init
    station: Station = None

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
        self.icao = icao
        self.station = Station.from_icao(icao)

    def __repr__(self) -> str:
        return f"<avwx.{self.__class__.__name__} icao={self.icao}>"

    @abstractmethod
    def _post_update(self):
        pass

    @classmethod
    def from_report(cls, report: str, issued: date = None) -> "AVWXBase":
        """
        Returns an updated report object based on an existing report
        """
        report = report.strip()
        station = find_station(report)
        if not station:
            return None
        obj = cls(station.icao)
        obj.update(report, issued=issued)
        return obj

    def _set_meta(self):
        """
        Update timestamps after parsing
        """
        self.last_updated = datetime.now(tz=timezone.utc)
        try:
            self.issued = self.data.time.dt.date()
        except AttributeError:
            pass

    def update(
        self,
        report: str = None,
        issued: date = None,
        timeout: int = 10,
        disable_post: bool = False,
    ) -> bool:
        """
        Updates raw, data, and translations by fetching and parsing the report

        Can accept a report string to parse instead

        Returns True if a new report is available, else False
        """
        if not report:
            report = self.service.fetch(self.icao, timeout=timeout)
            issued = None
        if not report or report == self.raw:
            return False
        self.raw = report
        self.issued = issued
        if not disable_post:
            self._post_update()
        self._set_meta()
        return True

    async def async_update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """
        Async version of update
        """
        report = await self.service.async_fetch(self.icao, timeout=timeout)
        if not report or report == self.raw:
            return False
        self.raw = report
        self.issued = None
        if not disable_post:
            self._post_update()
        self._set_meta()
        return True

    @staticmethod
    def sanitize(report: str) -> str:
        """
        Sanitizes the report string.
        This has not been overridden and returns the raw report
        """
        return report
