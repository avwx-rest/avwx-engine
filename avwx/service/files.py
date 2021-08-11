"""
Classes for retrieving raw report strings via managed files
"""

# pylint: disable=invalid-name,arguments-differ

# stdlib
import asyncio as aio
import atexit
import datetime as dt
import tempfile
from contextlib import suppress
from pathlib import Path
from socket import gaierror
from typing import Dict, Iterator, Optional, TextIO, Tuple

# library
import httpx

# module
from avwx.service.base import Service
from avwx.station import valid_station


_TEMP_DIR = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
_TEMP = Path(_TEMP_DIR.name)


@atexit.register
def _cleanup():
    """Deletes temporary files and directory at Python exit"""
    _TEMP_DIR.cleanup()


class FileService(Service):
    """Service class for fetching reports via managed source files"""

    update_interval: dt.timedelta = dt.timedelta(minutes=10)
    _updating: bool = False

    @property
    def _file_stem(self) -> str:
        return f"{self.__class__.__name__}.{self.report_type}"

    @property
    def _file(self) -> Optional[Path]:
        """Path object of the managed data file"""
        for path in _TEMP.glob(self._file_stem + "*"):
            return path
        return None

    @property
    def last_updated(self) -> Optional[dt.datetime]:
        """When the file was last updated"""
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
        """If the file should be updated based on the update interval"""
        last = self.last_updated
        if last is None:
            return True
        now = dt.datetime.now(tz=dt.timezone.utc)
        return now > last + self.update_interval

    def _new_path(self) -> Path:
        now = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        timestamp = str(now).split(".", maxsplit=1)[0]
        return _TEMP / f"{self._file_stem}.{timestamp}.txt"

    async def _wait_until_updated(self):
        while not self._updating:
            await aio.sleep(0.01)

    @property
    def _urls(self) -> Iterator[str]:
        raise NotImplementedError()

    def _extract(self, station: str, source: TextIO) -> Optional[str]:
        raise NotImplementedError()

    async def _update_file(self, timeout: int) -> bool:
        """Finds and saves the most recent file"""
        # Find the most recent file
        async with httpx.AsyncClient(timeout=timeout) as client:
            for url in self._urls:
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        break
                except (httpx.ConnectTimeout, httpx.ReadTimeout):
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

    async def update(self, wait: bool = False, timeout: int = 10) -> bool:
        """Update the stored file and returns success

        If wait, this will block if the file is already being updated
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

    def fetch(
        self, station: str, wait: bool = True, timeout: int = 10, force: bool = False
    ) -> Optional[str]:
        """Fetch a report string from the source file

        If wait, this will block if the file is already being updated

        Can force the service to fetch a new file
        """
        return aio.run(self.async_fetch(station, wait, timeout, force))

    async def async_fetch(
        self, station: str, wait: bool = True, timeout: int = 10, force: bool = False
    ) -> Optional[str]:
        """Asynchronously fetch a report string from the source file

        If wait, this will block if the file is already being updated

        Can force the service to fetch a new file
        """
        valid_station(station)
        if wait and self._updating:
            self._wait_until_updated()
        if force or self.is_outdated:
            if not await self.update(wait, timeout):
                return None
        file = self._file
        if file is None:
            return None
        with file.open() as fin:
            report = self._extract(station, fin)
        return report


class NOAA_Forecast(FileService):
    """Subclass for extracting reports from NOAA FTP files"""

    def _index_target(self, station: str) -> Tuple[str, str]:
        raise NotImplementedError()

    def _extract(self, station: str, source: TextIO) -> Optional[str]:
        """Returns report pulled from the saved file"""
        start, end = self._index_target(station)
        txt = source.read()
        txt = txt[txt.find(start) :]
        txt = txt[: txt.find(end, 30)]
        lines = []
        for line in txt.split("\n"):
            if "CLIMO" not in line:
                line = line.strip()
            if not line:
                break
            lines.append(line)
        return "\n".join(lines) or None


class NOAA_NBM(NOAA_Forecast):
    """Requests forecast data from NOAA NBM FTP servers"""

    url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/blend.{}/{}/text/blend_{}tx.t{}z"
    _valid_types = ("nbh", "nbs", "nbe")

    @property
    def _urls(self) -> Iterator[str]:
        """Iterates through hourly updates no older than two days"""
        date = dt.datetime.now(tz=dt.timezone.utc)
        cutoff = date - dt.timedelta(days=1)
        while date > cutoff:
            timestamp = date.strftime(r"%Y%m%d")
            hour = str(date.hour).zfill(2)
            yield self.url.format(timestamp, hour, self.report_type, hour)
            date -= dt.timedelta(hours=1)

    def _index_target(self, station: str) -> Tuple[str, str]:
        return station + "   ", self.report_type.upper() + " GUIDANCE"


class NOAA_GFS(NOAA_Forecast):
    """Requests forecast data from NOAA GFS FTP servers"""

    url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfsmos.{}/mdl_gfs{}.t{}z"
    _valid_types = ("mav", "mex")

    _cycles: Dict[str, Tuple[int, ...]] = {"mav": (0, 6, 12, 18), "mex": (0, 12)}

    @property
    def _urls(self) -> Iterator[str]:
        """Iterates through update cycles no older than two days"""
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
                yield self.url.format(timestamp, self.report_type, hour)
            date -= dt.timedelta(hours=1)

    def _index_target(self, station: str) -> Tuple[str, str]:
        return station + "   GFS", self.report_type.upper() + " GUIDANCE"
