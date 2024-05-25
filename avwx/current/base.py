"""Current report shared resources."""

# stdlib
from __future__ import annotations

import asyncio as aio
from typing import TYPE_CHECKING

# module
from avwx.base import ManagedReport
from avwx.service import get_service
from avwx.static.core import WX_TRANSLATIONS
from avwx.structs import Code, Coord, ReportData, ReportTrans, Sanitization, Units

if TYPE_CHECKING:
    from datetime import date


def wx_code(code: str) -> Code | str:
    """Translate weather codes into readable strings.

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
    is_code = False
    while code:
        try:
            ret += f"{WX_TRANSLATIONS[code[:2]]} "
            is_code = True
        except KeyError:
            ret += code[:2]
        code = code[2:]
    # Return Code if any part was able to be translated
    return Code(code_copy, ret.strip()) if is_code else code_copy


def get_wx_codes(codes: list[str]) -> tuple[list[str], list[Code]]:
    """Separate parsed WX codes."""
    other: list[str] = []
    ret: list[Code] = []
    for item in codes:
        code = wx_code(item)
        if isinstance(code, Code):
            ret.append(code)
        else:
            other.append(code)
    return other, ret


class Report(ManagedReport):
    """Base report to take care of service assignment and station info."""

    #: ReportTrans dataclass of translation strings from data. Parsed on update()
    translations: ReportTrans | None = None

    sanitization: Sanitization | None = None

    def __init__(self, code: str):
        """Add doc string to show constructor."""
        super().__init__(code)
        if self.station is not None:
            service = get_service(code, self.station.country)
            self.service = service(self.__class__.__name__.lower())  # type: ignore


class Reports(ManagedReport):
    """Base class containing multiple reports."""

    coord: Coord | None = None
    raw: list[str] | None = None  # type: ignore
    data: list[ReportData] | None = None  # type: ignore
    units: Units = Units.north_american()
    sanitization: list[Sanitization] | None = None

    def __init__(self, code: str | None = None, coord: Coord | None = None):
        if code:
            super().__init__(code)
            if self.station is not None:
                coord = self.station.coord
        elif coord is None:
            msg = "No station or coordinate given"
            raise ValueError(msg)
        self.coord = coord

    def __repr__(self) -> str:
        if self.code:
            return f"<avwx.{self.__class__.__name__} code={self.code}>"
        return f"<avwx.{self.__class__.__name__} coord={self.coord}>"

    @staticmethod
    def _report_filter(reports: list[str]) -> list[str]:
        """Apply any report filtering before updating raw_reports."""
        return reports

    async def _update(  # type: ignore
        self, reports: list[str], issued: date | None, *, disable_post: bool
    ) -> bool:
        if not reports:
            return False
        reports = self._report_filter(reports)
        return await super()._update(reports, issued, disable_post=disable_post)

    def parse(self, reports: str | list[str], issued: date | None = None) -> bool:
        """Update report data by parsing a given report.

        Can accept a report issue date if not a recent report string
        """
        return aio.run(self.async_parse(reports, issued))

    async def async_parse(self, reports: str | list[str], issued: date | None = None) -> bool:
        """Async update report data by parsing a given report.

        Can accept a report issue date if not a recent report string
        """
        self.source = None
        if isinstance(reports, str):
            reports = [reports]
        return await self._update(reports, issued, disable_post=False)

    def update(self, timeout: int = 10, *, disable_post: bool = False) -> bool:
        """Update report data by fetching and parsing the report.

        Returns True if new reports are available, else False
        """
        return aio.run(self.async_update(timeout, disable_post=disable_post))

    async def async_update(self, timeout: int = 10, *, disable_post: bool = False) -> bool:
        """Async update report data by fetching and parsing the report."""
        reports = await self.service.async_fetch(coord=self.coord, timeout=timeout)  # type: ignore
        self.source = self.service.root
        return await self._update(reports, None, disable_post=disable_post)
