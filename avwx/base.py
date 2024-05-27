"""Report parent classes."""

# stdlib
from __future__ import annotations

import asyncio as aio
from abc import ABCMeta, abstractmethod
from contextlib import suppress
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

# module
from avwx.exceptions import BadStation
from avwx.station import Station

if TYPE_CHECKING:
    from avwx.service import Service
    from avwx.structs import ReportData, Units

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


def find_station(report: str) -> Station | None:
    """Returns the first Station found in a report string"""
    for item in report.split():
        with suppress(BadStation):
            return Station.from_code(item.upper())
    return None


class AVWXBase(metaclass=ABCMeta):
    """Abstract base class for AVWX report types."""

    #: UTC datetime object when the report was last updated
    last_updated: datetime | None = None

    #: UTC date object when the report was issued
    issued: date | None = None

    #: Root URL used to retrieve the current report
    source: str | None = None

    #: The original report string
    raw: str | None = None

    #: ReportData dataclass of parsed data values and units
    data: ReportData | None = None

    #: Units inferred from the station location and report contents
    units: Units | None = None

    def __repr__(self) -> str:
        return f"<avwx.{self.__class__.__name__}>"

    def _set_meta(self) -> None:
        """Update timestamps after parsing."""
        self.last_updated = datetime.now(tz=timezone.utc)
        with suppress(AttributeError):
            self.issued = self.data.time.dt.date()  # type: ignore

    @abstractmethod
    def _post_parse(self) -> None:
        pass

    @classmethod
    def from_report(cls, report: str, issued: date | None = None) -> Self | None:
        """Return an updated report object based on an existing report."""
        report = report.strip()
        obj = cls()
        obj.parse(report, issued=issued)
        return obj

    def parse(self, report: str, issued: date | None = None) -> bool:
        """Update report data by parsing a given report.

        Can accept a report issue date if not a recent report string.
        """
        self.source = None
        if not report or report == self.raw:
            return False
        self.raw = report
        self.issued = issued
        self._post_parse()
        self._set_meta()
        return True

    @staticmethod
    def sanitize(report: str) -> str:
        """Sanitize the report string.

        This has not been overridden and returns the raw report.
        """
        return report


class ManagedReport(AVWXBase, metaclass=ABCMeta):
    """Abstract base class for reports types associated with a single station."""

    #: 4-character station code the report was initialized with
    code: str | None = None

    #: Provide basic station info if given at init
    station: Station | None = None

    #: Service object used to fetch the report string
    service: Service

    def __init__(self, code: str):
        code = code.upper()
        self.code = code
        self.station = Station.from_code(code)

    def __repr__(self) -> str:
        return f"<avwx.{self.__class__.__name__} code={self.code}>"

    @abstractmethod
    async def _post_update(self) -> None:
        pass

    @classmethod
    def from_report(cls, report: str, issued: date | None = None) -> Self | None:
        """Return an updated report object based on an existing report."""
        report = report.strip()
        station = find_station(report)
        if not station:
            return None
        obj = cls(station.lookup_code)
        obj.parse(report, issued=issued)
        return obj

    async def _update(self, report: str | list[str], issued: date | None, *, disable_post: bool) -> bool:
        if not report or report == self.raw:
            return False
        self.raw = report  # type: ignore
        self.issued = issued
        if not disable_post:
            await self._post_update()
        self._set_meta()
        return True

    def update(self, timeout: int = 10, *, disable_post: bool = False) -> bool:
        """Update. report data by fetching and parsing the report.

        Returns True if a new report is available, else False.
        """
        report = self.service.fetch(self.code, timeout=timeout)  # type: ignore
        self.source = self.service.root
        return aio.run(self._update(report, None, disable_post=disable_post))

    async def async_update(self, timeout: int = 10, *, disable_post: bool = False) -> bool:
        """Async update report data by fetching and parsing the report.

        Returns True if a new report is available, else False.
        """
        report = await self.service.async_fetch(self.code, timeout=timeout)  # type: ignore
        self.source = self.service.root
        return await self._update(report, None, disable_post=disable_post)
