"""
Update ICAO list from Avio source
"""

# stdlib
import gzip
import json
import asyncio as aio
from os import environ

# library
import httpx
from dotenv import load_dotenv

# module
from find_bad_stations import PROJECT_ROOT

load_dotenv()

ICAO_PATH = PROJECT_ROOT / "data" / "icaos.json"
TIMEOUT = 60
DATA_URL = "https://api.aviowiki.com/export/airports"
HEADERS = {
    "Authorization": "Bearer " + environ["AVIOWIKI_API_KEY"],
    "Accept": "application/gzip",
}


async def fetch_data() -> dict:
    """Fetch avio data via gzip export"""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(
            DATA_URL,
            headers=HEADERS,
        )
    data_bytes = gzip.decompress(resp.content)
    data = json.loads(data_bytes.decode("utf8"))
    return data


async def main() -> None:
    """Update ICAO list from Avio source"""
    icaos = []
    for station in await fetch_data():
        if icao := station.get("icao"):
            icaos.append(icao)
    icaos.sort()
    json.dump(icaos, ICAO_PATH.open("w"), indent=2)


if __name__ == "__main__":
    try:
        aio.run(main())
    except KeyboardInterrupt:
        pass
