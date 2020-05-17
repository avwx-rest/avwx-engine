"""
Current report shared resources
"""

# pylint: disable=abstract-method,arguments-differ

# stdlib
from datetime import date

# module
from avwx.base import AVWXBase
from avwx.service import get_service, NOAA_ADDS
from avwx.static.core import NA_UNITS, WX_TRANSLATIONS
from avwx.structs import Code, ReportData, ReportTrans, Units


def wx_code(code: str) -> "Code/str":
    """
    Translates weather codes into readable strings

    Returns translated string of variable length
    """
    if not code:
        return ""
    ret, code_copy = "", code
    if code[0] == "+":
        ret = "Heavy "
        code = code[1:]
    elif code[0] == "-":
        ret = "Light "
        code = code[1:]
    # Return code if code is not a code, ex R03/03002V03
    if len(code) not in [2, 4, 6]:
        return code
    while code:
        if code[:2] in WX_TRANSLATIONS:
            ret += WX_TRANSLATIONS[code[:2]] + " "
        else:
            ret += code[:2]
        code = code[2:]
    return Code(code_copy, ret.strip())


def get_wx_codes(codes: [str]) -> ([Code], [str]):
    """
    Separates parsed WX codes
    """
    ret, other = [], []
    for code in codes:
        code = wx_code(code)
        (ret if isinstance(code, Code) else other).append(code)
    return other, ret


class Report(AVWXBase):
    """
    Base report to take care of service assignment and station info
    """

    #: ReportTrans dataclass of translation strings from data. Parsed on update()
    translations: ReportTrans = None

    def __init__(self, icao: str):
        super().__init__(icao)
        self.service = get_service(icao, self.station.country)(
            self.__class__.__name__.lower()
        )


class Reports(AVWXBase):
    """
    Base class containing multiple reports
    """

    raw: [str] = None
    data: [ReportData] = None
    units: Units = Units(**NA_UNITS)

    def __init__(self, icao: str = None, lat: float = None, lon: float = None):
        if icao:
            super().__init__(icao)
            lat = self.station.latitude
            lon = self.station.longitude
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
        self,
        reports: [str] = None,
        issued: date = None,
        timeout: int = 10,
        disable_post: bool = False,
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
            issued = None
        if isinstance(reports, str):
            reports = [reports]
        if reports == self.raw:
            return False
        self.raw = self._report_filter(reports)
        self.issued = issued
        if not disable_post:
            self._post_update()
        self._set_meta()
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
        self.issued = None
        if not disable_post:
            self._post_update()
        self._set_meta()
        return True
