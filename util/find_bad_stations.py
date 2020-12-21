"""
Manages good/bad station lists by calling METARs
"""

# stdlib
import sys
import asyncio as aio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import List

# module
import avwx

GOOD_PATH = Path("data", "good_stations.txt")
BAD_PATH = Path("data", "bad_stations.txt")


def load_stations(path: Path) -> List[str]:
    return path.read_text().strip().split(",")


def save_stations(data: List[str], path: Path):
    path.write_text(",".join(sorted(set(data))))


GOOD = load_stations(GOOD_PATH)
BAD = load_stations(BAD_PATH)


def should_test(icao: str) -> bool:
    """Returns False if an ident is known good or never good"""
    if icao in GOOD:
        return False
    for char in icao:
        if char.isdigit():
            return False
    return True


async def worker(queue: aio.Queue):
    """Worker to check queued idents and update lists"""
    i = 0
    maxi = 100
    while True:
        icao = await queue.get()
        try:
            m = avwx.Metar(icao)
            if await m.async_update():
                GOOD.append(icao)
                BAD.remove(icao)
            elif icao not in BAD:
                BAD.append(icao)
            i += 1
            # Sleep to prevent 403 from services
            if i >= maxi:
                i = 0
                await aio.sleep(10)
        except avwx.exceptions.SourceError as exc:
            print(exc)
            sys.exit(3)
        except (avwx.exceptions.BadStation, avwx.exceptions.InvalidRequest):
            pass
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as exc:
            print()
            print(exc)
            print(icao)
            print()
        finally:
            queue.task_done()


@asynccontextmanager
async def task_manager(queue: aio.Queue, n: int = 10):
    """Handles async task managers"""
    tasks = []
    # Create three worker tasks to process the queue concurrently
    for _ in range(n):
        task = aio.create_task(worker(queue))
        tasks.append(task)
    yield
    # Cancel our worker tasks
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled
    await aio.gather(*tasks, return_exceptions=True)


async def loop():
    """Populate and run ICAO check queue"""
    queue = aio.Queue()
    for station in avwx.station._STATIONS.values():
        icao = station["icao"]
        if not station["reporting"] and should_test(icao):
            queue.put_nowait(icao)
    try:
        async with task_manager(queue, 2):
            await queue.join()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as exc:
        print()
        print(exc)
        sys.exit(2)


def main() -> int:
    """Update ICAO lists with 1 hour sleep cycle"""
    while True:
        aio.run(loop())
        print()
        save_stations(BAD, BAD_PATH)
        save_stations(GOOD, GOOD_PATH)
        print("Looped", datetime.now())
        sleep(60 * 60)
    return 0


if __name__ == "__main__":
    main()
