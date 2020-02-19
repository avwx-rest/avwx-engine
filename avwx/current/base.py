"""
"""

# stdlib
from datetime import datetime, timezone

# module
from avwx.base import AVWXBase
from avwx.service import get_service, NOAA_ADDS
from avwx.static.core import NA_UNITS
from avwx.station import Station
from avwx.structs import ReportData, ReportTrans, Units


class Report(AVWXBase):
    """
    Base report to take care of service assignment and station info
    """

    #: ReportTrans dataclass of translation strings from data. Parsed on update()
    translations: ReportTrans = None

    def __init__(self, icao: str):
        super().__init__(icao)
        self.service = get_service(icao, self.station_info.country)(
            self.__class__.__name__.lower()
        )


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

    def __repr__(self) -> str:
        return f"<avwx.{self.__class__.__name__} lat={self.lat} lon={self.lon}>"

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
