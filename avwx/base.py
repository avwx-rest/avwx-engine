"""
Report parent classes
"""

# stdlib
import asyncio as aio
from abc import ABCMeta, abstractmethod
from contextlib import suppress
from datetime import date, datetime, timezone
from typing import List, Optional, Type, TypeVar, Union

# module
from avwx.exceptions import BadStation
from avwx.service import Service
from avwx.station import Station
from avwx.structs import ReportData, Units


def find_station(report: str) -> Optional[Station]:
    """Returns the first ICAO ident found in a report string"""
    for item in report.split():
        if len(item) == 4:
            with suppress(BadStation):
                return Station.from_icao(item.upper())
        if len(item) == 3:
            with suppress(BadStation):
                return Station.from_iata(item.upper())
    return None


T = TypeVar("T", bound="AVWXBase")  # pylint: disable=invalid-name
MT = TypeVar("MT", bound="ManagedReport")  # pylint: disable=invalid-name


class AVWXBase(metaclass=ABCMeta):
    """Abstract base class for AVWX report types"""

    #: UTC datetime object when the report was last updated
    last_updated: Optional[datetime] = None

    #: UTC date object when the report was issued
    issued: Optional[date] = None

    #: Root URL used to retrieve the current report
    source: Optional[str] = None

    #: The original report string
    raw: Optional[str] = None

    #: ReportData dataclass of parsed data values and units
    data: Optional[ReportData] = None

    #: Units inferred from the station location and report contents
    units: Optional[Units] = None

    def __repr__(self) -> str:
        return f"<avwx.{self.__class__.__name__}>"

    def _set_meta(self) -> None:
        """Update timestamps after parsing"""
        self.last_updated = datetime.now(tz=timezone.utc)
        with suppress(AttributeError):
            self.issued = self.data.time.dt.date()  # type: ignore

    @abstractmethod
    def _post_parse(self) -> None:
        pass

    @classmethod
    def from_report(cls: Type[T], report: str, issued: date = None) -> Optional[T]:
        """Returns an updated report object based on an existing report"""
        report = report.strip()
        obj = cls()
        obj.parse(report, issued=issued)
        return obj

    def parse(self, report: str, issued: Optional[date] = None) -> bool:
        """Updates report data by parsing a given report

        Can accept a report issue date if not a recent report string
        """
        self.source = None
        if not report or report == self.raw:
            return False
        self.raw = report  # type: ignore
        self.issued = issued
        self._post_parse()
        self._set_meta()
        return True

    @staticmethod
    def sanitize(report: str) -> str:
        """Sanitizes the report string

        This has not been overridden and returns the raw report
        """
        return report


class ManagedReport(AVWXBase, metaclass=ABCMeta):
    """Abstract base class for reports types associated with a single station"""

    #: 4-character ICAO station ident code the report was initialized with
    icao: Optional[str] = None

    #: Provide basic station info if given at init
    station: Optional[Station] = None

    #: Service object used to fetch the report string
    service: Service

    def __init__(self, icao: str):
        icao = icao.upper()
        self.icao = icao
        self.station = Station.from_icao(icao)

    def __repr__(self) -> str:
        return f"<avwx.{self.__class__.__name__} icao={self.icao}>"

    @abstractmethod
    async def _post_update(self) -> None:
        pass

    @classmethod
    def from_report(cls: Type[MT], report: str, issued: date = None) -> Optional[MT]:
        """Returns an updated report object based on an existing report"""
        report = report.strip()
        station = find_station(report)
        if not station:
            return None
        obj = cls(station.icao)
        obj.parse(report, issued=issued)
        return obj

    async def _update(
        self, report: Union[str, List[str]], issued: Optional[date], disable_post: bool
    ) -> bool:
        if not report or report == self.raw:
            return False
        self.raw = report  # type: ignore
        self.issued = issued
        if not disable_post:
            await self._post_update()
        self._set_meta()
        return True

    def update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """Updates report data by fetching and parsing the report

        Returns True if a new report is available, else False
        """
        report = self.service.fetch(self.icao, timeout=timeout)  # type: ignore
        self.source = self.service.root
        return aio.run(self._update(report, None, disable_post))

    async def async_update(self, timeout: int = 10, disable_post: bool = False) -> bool:
        """Async updates report data by fetching and parsing the report

        Returns True if a new report is available, else False
        """
        report = await self.service.async_fetch(self.icao, timeout=timeout)  # type: ignore
        self.source = self.service.root
        return await self._update(report, None, disable_post)
