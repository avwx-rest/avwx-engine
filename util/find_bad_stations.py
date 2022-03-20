"""
Manages good/bad station lists by calling METARs
"""

# pylint: disable=broad-except

# stdlib
import random
import asyncio as aio
from datetime import datetime
from pathlib import Path

# library
from kewkew import Kew

# module
import avwx


GOOD_PATH = Path(__file__).parent.parent / "avwx" / "data" / "files" / "good_stations.txt"


def load_stations(path: Path) -> set[str]:
    """Load a station set from a path"""
    return set(path.read_text().strip().split("\n"))


def save_stations(data: set[str], path: Path):
    """Save a sation set to a path"""
    path.write_text("\n".join(sorted(data)))


class StationTester(Kew):
    """Station reporting queue manager"""

    good_stations: set[str]
    sleep_chance: float

    def __init__(self, stations: set[str], workers: int = 3) -> None:
        super().__init__(workers=workers)
        self.good_stations = stations
        self.sleep_chance = 0.0

    def should_test(self, icao: str) -> bool:
        """Returns False if an ident is known good or never good"""
        if icao in self.good_stations:
            return False
        for char in icao:
            if char.isdigit():
                return False
        return True

    async def worker(self, data: object) -> bool:
        """Worker to check queued idents and update lists"""
        icao = data
        try:
            metar = avwx.Metar(icao)
            if await metar.async_update():
                self.good_stations.add(icao)
        except avwx.exceptions.SourceError as exc:
            print("\n", icao, exc, "\n")
        except (avwx.exceptions.BadStation, avwx.exceptions.InvalidRequest):
            pass
        except Exception as exc:
            print("\n", icao, exc, "\n")
        return True

    async def wait(self):
        """Waits until the queue is empty"""
        while not self._queue.empty():
            await aio.sleep(0.01)

    async def add_stations(self):
        """Populate and run ICAO check queue"""
        stations = []
        for station in avwx.station.meta.STATIONS.values():
            icao = station["icao"]
            if not station["reporting"] and self.should_test(icao):
                stations.append(icao)
        random.shuffle(stations)
        for icao in stations:
            await self.add(icao)


async def main() -> int:
    """Update ICAO lists with 1 hour sleep cycle"""
    tester = StationTester(load_stations(GOOD_PATH))
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
    try:
        aio.run(main())
    except KeyboardInterrupt:
        pass
