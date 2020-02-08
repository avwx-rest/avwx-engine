"""
"""

# stdlib
from abc import abstractmethod
from datetime import datetime, timezone

# module
from avwx.base import AVWXBase
from avwx.service import get_service, NOAA_ADDS
from avwx.static import NA_UNITS
from avwx.station import Station, valid_station
from avwx.structs import ReportData, ReportTrans, Units


class Report(AVWXBase):
    """
    Base report to take care of service assignment and station info
    """

    #: ReportTrans dataclass of translation strings from data. Parsed on update()
    translations: ReportTrans = None

    #: 4-character ICAO station ident code the report was initialized with
    station: str

    def __init__(self, icao: str):
        # Raises a BadStation error if needed
        valid_station(icao)
        self.station = icao
        self.station_info = Station.from_icao(icao)
        self.service = get_service(icao, self.station_info.country)(
            self.__class__.__name__.lower()
        )

    @abstractmethod
    def _post_update(self):
        pass

    @classmethod
    def from_report(cls, report: str) -> "Report":
        """
        Returns an updated report object based on an existing report
        """
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

    def __repr__(self) -> str:
        return f"<avwx.{self.__class__.__name__} station={self.station}>"


class Reports(AVWXBase):
    """
    Base class containing multiple reports
    """

    raw: [str] = None
    data: [ReportData] = None
    units: Units = Units(**NA_UNITS)

    def __init__(self, station_ident: str = None, lat: float = None, lon: float = None):
        if station_ident:
            station_obj = Station.from_icao(station_ident)
            self.station_info = station_obj
            lat = station_obj.latitude
            lon = station_obj.longitude
        elif lat is None or lon is None:
            raise ValueError("No station or valid coordinates given")
        self.lat = lat
        self.lon = lon
        self.service = NOAA_ADDS("aircraftreport")

    def _post_update(self):
        pass

    @staticmethod
    def _report_filter(reports: [str]) -> [str]:
        """
        Applies any report filtering before updating raw_reports
        """
        return reports

    def update(
        self, reports: [str] = None, timeout: int = 10, disable_post: bool = False
    ) -> bool:
        """
        Updates raw and data by fetch recent aircraft reports

        Can accept a list report strings to parse instead

        Returns True if new reports are available, else False
        """
        if not reports:
            reports = self.service.fetch(lat=self.lat, lon=self.lon, timeout=timeout)
            if not reports:
                return False
        if isinstance(reports, str):
            reports = [reports]
        if reports == self.raw:
            return False
        self.raw = self._report_filter(reports)
        if not disable_post:
            self._post_update()
        self.last_updated = datetime.now(tz=timezone.utc)
        return True

    async def async_update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """
        Async version of update
        """
        reports = await self.service.async_fetch(
            lat=self.lat, lon=self.lon, timeout=timeout
        )
        if not reports or reports == self.raw:
            return False
        self.raw = reports
        if not disable_post:
            self._post_update()
        return True
