"""
Current report shared resources
"""

# pylint: disable=abstract-method,arguments-renamed

# stdlib
import asyncio as aio
from datetime import date
from typing import List, Optional, Tuple, Union

# module
from avwx.base import ManagedReport
from avwx.service import get_service
from avwx.static.core import NA_UNITS, WX_TRANSLATIONS
from avwx.structs import Code, Coord, ReportData, ReportTrans, Sanitization, Units


def wx_code(code: str) -> Union[Code, str]:
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
    if len(code) not in [2, 4, 6] or code.isdigit():
        return code
    while code:
        try:
            ret += WX_TRANSLATIONS[code[:2]] + " "
        except KeyError:
            ret += code[:2]
        code = code[2:]
    return Code(code_copy, ret.strip())


def get_wx_codes(codes: List[str]) -> Tuple[List[str], List[Code]]:
    """
    Separates parsed WX codes
    """
    other: List[str] = []
    ret: List[Code] = []
    for item in codes:
        code = wx_code(item)
        if isinstance(code, Code):
            ret.append(code)
        else:
            other.append(code)
    return other, ret


class Report(ManagedReport):
    """
    Base report to take care of service assignment and station info
    """

    #: ReportTrans dataclass of translation strings from data. Parsed on update()
    translations: Optional[ReportTrans] = None

    sanitization: Optional[Sanitization] = None

    def __init__(self, code: str):
        super().__init__(code)
        if self.station is not None:
            service = get_service(code, self.station.country)
            self.service = service(self.__class__.__name__.lower())  # type: ignore


class Reports(ManagedReport):
    """
    Base class containing multiple reports
    """

    coord: Optional[Coord] = None
    raw: Optional[List[str]] = None  # type: ignore
    data: Optional[List[ReportData]] = None  # type: ignore
    units: Units = Units(**NA_UNITS)
    sanitization: Optional[List[Sanitization]] = None

    def __init__(self, code: Optional[str] = None, coord: Optional[Coord] = None):
        if code:
            super().__init__(code)
            if self.station is not None:
                coord = self.station.coord
        elif coord is None:
            raise ValueError("No station or coordinate given")
        self.coord = coord

    def __repr__(self) -> str:
        if self.code:
            return f"<avwx.{self.__class__.__name__} code={self.code}>"
        return f"<avwx.{self.__class__.__name__} coord={self.coord}>"

    @staticmethod
    def _report_filter(reports: List[str]) -> List[str]:
        """Applies any report filtering before updating raw_reports"""
        return reports

    async def _update(  # type: ignore
        self, reports: List[str], issued: Optional[date], disable_post: bool
    ) -> bool:
        if not reports:
            return False
        reports = self._report_filter(reports)
        return await super()._update(reports, issued, disable_post)

    def parse(
        self, reports: Union[str, List[str]], issued: Optional[date] = None
    ) -> bool:
        """Updates report data by parsing a given report

        Can accept a report issue date if not a recent report string
        """
        return aio.run(self.async_parse(reports, issued))

    async def async_parse(
        self, reports: Union[str, List[str]], issued: Optional[date] = None
    ) -> bool:
        """Async updates report data by parsing a given report

        Can accept a report issue date if not a recent report string
        """
        self.source = None
        if isinstance(reports, str):
            reports = [reports]
        return await self._update(reports, issued, False)

    def update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """Updates report data by fetching and parsing the report

        Returns True if new reports are available, else False
        """
        return aio.run(self.async_update(timeout, disable_post))

    async def async_update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """Async updates report data by fetching and parsing the report"""
        reports = await self.service.async_fetch(coord=self.coord, timeout=timeout)  # type: ignore
        self.source = self.service.root
        return await self._update(reports, None, disable_post)
