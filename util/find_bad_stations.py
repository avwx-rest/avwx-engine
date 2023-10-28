"""
Manages good/bad station lists by calling METARs
"""

# pylint: disable=broad-except

# stdlib
import random
import asyncio as aio
from contextlib import suppress
from datetime import datetime
from pathlib import Path

# library
from kewkew import Kew

# module
import avwx
from avwx.service.bulk import NOAA_Bulk
from avwx.service.scrape import NOAA


PROJECT_ROOT = Path(__file__).parent.parent
GOOD_PATH = PROJECT_ROOT / "avwx" / "data" / "files" / "good_stations.txt"


def load_stations(path: Path) -> set[str]:
    """Load a station set from a path"""
    return set(path.read_text().strip().split("\n"))


def save_stations(data: set[str], path: Path):
    """Save a sation set to a path"""
    path.write_text("\n".join(sorted(data)))


async def get_noaa_codes() -> {str}:
    """Create a set of current NOAA codes from bulk access"""
    codes = set()
    for report in await NOAA_Bulk("metar").async_fetch():
        items = report.strip(" '\"").split()
        if items[0] == "METAR":
            items.pop(0)
        codes.add(items[0])
    return codes


class StationTester(Kew):
    """Station reporting queue manager"""

    good_stations: set[str]
    sleep_chance: float

    def __init__(self, stations: set[str], workers: int = 3) -> None:
        super().__init__(workers=workers)
        self.good_stations = stations
        self.sleep_chance = 0.0

    def should_test(self, code: str) -> bool:
        """Returns False if an ident is known good or never good"""
        if code in self.good_stations:
            return False
        return not any(char.isdigit() for char in code)

    async def worker(self, data: object) -> bool:
        """Worker to check queued idents and update lists"""
        code = data
        try:
            metar = avwx.Metar(code)
            if isinstance(metar.service, NOAA):  # Skip NOAA if not in bulk pull
                return True
            if await metar.async_update():
                self.good_stations.add(code)
        except avwx.exceptions.SourceError as exc:
            print("\n", code, exc, "\n")
        except (avwx.exceptions.BadStation, avwx.exceptions.InvalidRequest):
            pass
        except Exception as exc:
            print("\n", code, exc, "\n")
        return True

    async def wait(self):
        """Waits until the queue is empty"""
        while not self._queue.empty():
            await aio.sleep(0.01)

    async def add_stations(self):
        """Populate and run ICAO check queue"""
        stations = []
        for station in avwx.station.meta.STATIONS.values():
            code = station["icao"] or station["gps"]
            if code and not station["reporting"] and self.should_test(code):
                stations.append(code)
        random.shuffle(stations)
        for code in stations:
            await self.add(code)


async def main() -> int:
    """Update ICAO lists with 1 hour sleep cycle"""
    tester = StationTester(load_stations(GOOD_PATH).union(await get_noaa_codes()))
    try:
        while True:
            print("\nStarting", datetime.now())
            await tester.add_stations()
            await tester.wait()
            save_stations(tester.good_stations, GOOD_PATH)
            print(f"Good stations: {len(tester.good_stations)}")
            print("Sleeping", datetime.now())
            await aio.sleep(60 * 60)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print("\nMAIN ERROR:", exc)
    finally:
        await tester.finish(wait=False)
    return 0


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        aio.run(main())
