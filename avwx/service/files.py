"""
These services are directed at FTP servers to find the most recent file
associated with the search criteria. Files are stored in a temporary directory
which is deleted when the program ends. Fetch requests will extract reports
from the downloaded file until an update interval has been exceeded, at which
point the service will check for a newer file. You can also have direct access
to all downloaded reports.
"""

# stdlib
from __future__ import annotations

import asyncio as aio
import atexit
import datetime as dt
import tempfile
import warnings
from contextlib import suppress
from pathlib import Path
from socket import gaierror
from typing import TYPE_CHECKING, ClassVar, TextIO

# library
import httpx

# module
from avwx.service.base import Service
from avwx.station import valid_station

if TYPE_CHECKING:
    from collections.abc import Iterator

_TEMP_DIR = tempfile.TemporaryDirectory()
_TEMP = Path(_TEMP_DIR.name)


_HTTPX_EXCEPTIONS = (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError)


@atexit.register
def _cleanup() -> None:
    """Deletes temporary files and directory at Python exit."""
    _TEMP_DIR.cleanup()


class FileService(Service):
    """Service class for fetching reports via managed source files."""

    update_interval: dt.timedelta = dt.timedelta(minutes=10)
    _updating: bool = False

    @property
    def _file_stem(self) -> str:
        return f"{self.__class__.__name__}.{self.report_type}"

    @property
    def _file(self) -> Path | None:
        """Path object of the managed data file."""
        for path in _TEMP.glob(f"{self._file_stem}*"):
            return path
        return None

    @property
    def last_updated(self) -> dt.datetime | None:
        """When the file was last updated."""
        file = self._file
        if file is None:
            return None
        try:
            timestamp = int(file.name.split(".")[-2])
            return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
        except (AttributeError, ValueError):
            return None

    @property
    def is_outdated(self) -> bool:
        """If the file should be updated based on the update interval."""
        last = self.last_updated
        if last is None:
            return True
        now = dt.datetime.now(tz=dt.timezone.utc)
        return now > last + self.update_interval

    def _new_path(self) -> Path:
        now = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        timestamp = str(now).split(".", maxsplit=1)[0]
        return _TEMP / f"{self._file_stem}.{timestamp}.txt"

    async def _wait_until_updated(self) -> None:
        while not self._updating:
            await aio.sleep(0.01)

    @property
    def all(self) -> list[str]:
        """All report strings available after updating."""
        raise NotImplementedError

    @property
    def _urls(self) -> Iterator[str]:
        raise NotImplementedError

    def _extract(self, station: str, source: TextIO) -> str | None:
        raise NotImplementedError

    async def _update_file(self, timeout: int) -> bool:
        """Find and save the most recent file."""
        # Find the most recent file
        async with httpx.AsyncClient(timeout=timeout) as client:
            for url in self._urls:
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        break
                except _HTTPX_EXCEPTIONS:
                    return False
                except gaierror:
                    return False
            else:
                return False
        # Save successful file download
        new_path = self._new_path()
        with new_path.open("wb") as new_file:
            new_file.write(resp.content)
        return True

    async def update(self, *, wait: bool = False, timeout: int = 10) -> bool:
        """Update the stored file and returns success.

        If wait, this will block if the file is already being updated.
        """
        # Guard for other async calls
        if self._updating:
            if wait:
                await self._wait_until_updated()
                return True
            return False
        self._updating = True
        # Replace file
        old_path = self._file
        if not await self._update_file(timeout):
            self._updating = False
            return False
        if old_path:
            with suppress(FileNotFoundError):
                old_path.unlink()
        self._updating = False
        return True

    def fetch(self, station: str, *, wait: bool = True, timeout: int = 10, force: bool = False) -> str | None:
        """Fetch a report string from the source file.

        If wait, this will block if the file is already being updated.

        Can force the service to fetch a new file.
        """
        return aio.run(self.async_fetch(station, wait=wait, timeout=timeout, force=force))

    async def async_fetch(
        self, station: str, *, wait: bool = True, timeout: int = 10, force: bool = False
    ) -> str | None:
        """Asynchronously fetch a report string from the source file.

        If wait, this will block if the file is already being updated.

        Can force the service to fetch a new file.
        """
        valid_station(station)
        if wait and self._updating:
            await self._wait_until_updated()
        if (force or self.is_outdated) and not await self.update(wait=wait, timeout=timeout):
            return None
        file = self._file
        if file is None:
            return None
        with file.open() as fin:
            return self._extract(station, fin)


class NoaaForecast(FileService):
    """Subclass for extracting reports from NOAA FTP files."""

    @property
    def all(self) -> list[str]:
        """All report strings available after updating."""
        if self._file is None:
            return []
        with self._file.open() as fin:
            lines = fin.readlines()
        reports = []
        report = ""
        for line in lines:
            if line := line.strip():
                report += "\n" + line
            else:
                if len(report) > 10:
                    reports.append(report.strip())
                report = ""
        return reports

    def _index_target(self, station: str) -> tuple[str, str]:
        raise NotImplementedError

    def _extract(self, station: str, source: TextIO) -> str | None:
        """Return report pulled from the saved file."""
        start, end = self._index_target(station)
        txt = source.read()
        txt = txt[txt.find(start) :]
        txt = txt[: txt.find(end, 30)]
        lines = []
        for line in txt.split("\n"):
            if "CLIMO" not in line:
                line = line.strip()  # noqa: PLW2901
            if not line:
                break
            lines.append(line)
        return "\n".join(lines) or None


class NoaaNbm(NoaaForecast):
    """Request forecast data from NOAA NBM FTP servers."""

    _url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/blend.{}/{}/text/blend_{}tx.t{}z"
    _valid_types = ("nbh", "nbs", "nbe", "nbx")

    @property
    def _urls(self) -> Iterator[str]:
        """Iterate through hourly updates no older than two days."""
        date = dt.datetime.now(tz=dt.timezone.utc)
        cutoff = date - dt.timedelta(days=1)
        while date > cutoff:
            timestamp = date.strftime(r"%Y%m%d")
            hour = str(date.hour).zfill(2)
            yield self._url.format(timestamp, hour, self.report_type, hour)
            date -= dt.timedelta(hours=1)

    def _index_target(self, station: str) -> tuple[str, str]:
        return f"{station}   ", f"{self.report_type.upper()} GUIDANCE"


class NoaaGfs(NoaaForecast):
    """Request forecast data from NOAA GFS FTP servers."""

    _url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfsmos.{}/mdl_gfs{}.t{}z"
    _valid_types = ("mav", "mex")

    _cycles: ClassVar[dict[str, tuple[int, ...]]] = {"mav": (0, 6, 12, 18), "mex": (0, 12)}

    @property
    def _urls(self) -> Iterator[str]:
        """Iterate through update cycles no older than two days."""
        warnings.warn(
            "GFS fetch has been deprecated due to NOAA retiring the format. Migrate to NBM for similar data",
            DeprecationWarning,
            stacklevel=2,
        )
        now = dt.datetime.now(tz=dt.timezone.utc)
        date = dt.datetime.now(tz=dt.timezone.utc)
        cutoff = date - dt.timedelta(days=1)
        while date > cutoff:
            for cycle in reversed(self._cycles[self.report_type]):
                date = date.replace(hour=cycle)
                if date > now:
                    continue
                timestamp = date.strftime(r"%Y%m%d")
                hour = str(date.hour).zfill(2)
                yield self._url.format(timestamp, self.report_type, hour)
            date -= dt.timedelta(hours=1)

    def _index_target(self, station: str) -> tuple[str, str]:
        return f"{station}   GFS", f"{self.report_type.upper()} GUIDANCE"


# https://www.ncei.noaa.gov/data/ncep-global-data-assimilation/access/202304/20230415/
