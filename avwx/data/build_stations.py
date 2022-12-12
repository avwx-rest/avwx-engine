"""
Builds the main station list

Source file for airports.csv and runways.csv can be downloaded from
http://ourairports.com/data/

Source file for stations.txt can be downloaded from
https://www.aviationweather.gov/docs/metar/stations.txt
"""

# stdlib
import csv
import json
import logging
from contextlib import suppress
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

# library
import httpx

# module
from avwx.data.mappers import FILE_REPLACE, SURFACE_TYPES


LOG = logging.getLogger("avwx.data.build_stations")


def load_stations(path: Path) -> set[str]:
    """Load a station set from a path"""
    return set(path.read_text().strip().split("\n"))


_FILE_DIR = Path(__file__).parent
_DATA = _FILE_DIR / "files"
GOOD_PATH = _DATA / "good_stations.txt"
OUTPUT_PATH = _DATA / "stations.json"


DATA_ROOT = "https://davidmegginson.github.io/ourairports-data/"
_SOURCE: Dict[str, str] = {}
_SOURCES = {
    "airports": DATA_ROOT + "airports.csv",
    "runways": DATA_ROOT + "runways.csv",
    "stations": "https://www.aviationweather.gov/docs/metar/stations.txt",
    "icaos": "https://raw.githubusercontent.com/avwx-rest/avwx-engine/main/data/icaos.json",
    "awos": "https://raw.githubusercontent.com/avwx-rest/avwx-engine/main/data/awos.json",
}


# Managed list of official ICAO idents
ICAO: List[str] = []
# Allow-listed AWOS stations not covered by ICAO-GPS codes
AWOS: List[str] = []


ACCEPTED_STATION_TYPES = [
    "balloonport",
    # "closed",
    "heliport",
    "large_airport",
    "medium_airport",
    "seaplane_base",
    "small_airport",
]


def nullify(data: dict) -> dict:
    """Nullify empty strings in a dict"""
    for key, val in data.items():
        if isinstance(val, str) and not val.strip():
            data[key] = None
    return data


def format_coord(coord: str) -> float:
    """Convert coord string to float"""
    neg = -1 if coord[-1] in ("S", "W") else 1
    return neg * float(coord[:-1].strip().replace(" ", "."))


def load_codes() -> None:
    """Load ident lists"""
    # Global can't assign
    for key, out in (("icaos", ICAO), ("awos", AWOS)):
        for code in json.loads(_SOURCE[key]):
            out.append(code)


def validate_icao(code: str) -> Optional[str]:
    """Validates a given station ident"""
    if not (len(code) == 4 or code in AWOS):
        return None
    return code.upper()


def get_icao(station: List[str]) -> Optional[str]:
    """Finds the ICAO by checking ident and GPS code"""
    gps_code = validate_icao(station[12])
    if gps_code and gps_code in ICAO:
        return gps_code
    ident = validate_icao(station[1])
    if ident and (ident in ICAO or ident in AWOS):
        return ident
    return gps_code


def clean_source_files() -> None:
    """Cleans the source data files before parsing"""
    text = _SOURCE["airports"]
    for find, replace in FILE_REPLACE.items():
        text = text.replace(find, replace)
    _SOURCE["airports"] = text


def format_station(code: str, station: List[str]) -> dict:
    """Converts source station list into info dict"""
    try:
        elev_ft = float(station[6])
        elev_m = round(elev_ft * 0.3048)
        elev_ft = round(elev_ft)
    except ValueError:
        elev_ft, elev_m = None, None
    index = station[9].find("-")
    ret = {
        "type": station[2],
        "name": station[3],
        "reporting": None,
        "latitude": float(station[4]),
        "longitude": float(station[5]),
        "elevation_ft": elev_ft,
        "elevation_m": elev_m,
        "country": station[9][:index],
        "state": station[9][index + 1 :],
        "city": station[10],
        "icao": code if code in ICAO else None,
        "iata": station[13].upper() or None,
        "gps": station[12].upper() or None,
        "local": station[14].upper() or None,
        "website": station[15] or None,
        "wiki": station[16] or None,
        "note": station[17] or None,
    }
    return nullify(ret)


def build_stations() -> tuple[dict, dict]:
    """Builds the station dict from source file"""
    stations, code_map = {}, {}
    data = csv.reader(_SOURCE["airports"].splitlines())
    next(data)  # Skip header
    for station in data:
        code = get_icao(station)
        if code and station[2] in ACCEPTED_STATION_TYPES:
            stations[code] = format_station(code, station)
            code_map[station[0]] = code
    return stations, code_map


def add_missing_stations(stations: dict) -> dict:
    """Add non-airport stations from NOAA"""
    for line in _SOURCE["stations"].splitlines():
        # Must be data line with METAR reporting
        if len(line) != 83 or line[0] == "!" or line[62] != "X":
            continue
        icao = line[20:24].strip().upper()
        if not icao or icao in stations:  # or icao in BAD_STATIONS:
            continue
        elev_m = int(line[55:59].strip())
        ret = {
            "type": "weather_station",
            "name": line[3:19].strip(),
            "reporting": None,
            "latitude": format_coord(line[39:45]),
            "longitude": format_coord(line[47:54]),
            "elevation_ft": round(elev_m * 3.28084),
            "elevation_m": elev_m,
            "country": line[81:83].strip(),
            "state": line[:2],
            "city": None,
            "icao": icao,
            "iata": line[26:29].strip().upper(),
            "gps": "",
            "local": "",
            "website": None,
            "wiki": None,
            "note": None,
        }
        stations[icao] = nullify(ret)
    return stations


def get_surface_type(surface: str) -> Optional[str]:
    """Returns the normalize surface type value"""
    for key, items in SURFACE_TYPES.items():
        if surface in items:
            return key
    return None


def add_runways(stations: dict, code_map: dict) -> dict:
    """Add runway information to station if availabale"""
    data = csv.reader(_SOURCE["runways"].splitlines())
    next(data)  # Skip header
    for runway in data:
        # if runway is closed
        if runway[7] != "0":
            continue
        out = {
            "length_ft": int(runway[3]) if runway[3] else 0,
            "width_ft": int(runway[4]) if runway[4] else 0,
            "surface": get_surface_type(runway[5].lower()),
            "lights": runway[6] == "1",
            "ident1": runway[8],
            "ident2": runway[14],
            "bearing1": float(runway[12]) if runway[12] else None,
            "bearing2": float(runway[18]) if runway[18] else None,
        }
        code = code_map.get(runway[1], runway[2])
        with suppress(KeyError):
            if "runways" in stations[code]:
                stations[code]["runways"].append(out)
            else:
                stations[code]["runways"] = [out]
    # Sort runways by longest length and add missing nulls
    for code in stations:
        if "runways" in stations[code]:
            stations[code]["runways"].sort(key=lambda x: x["length_ft"], reverse=True)
        else:
            stations[code]["runways"] = None
    return stations


def add_reporting(stations: dict) -> dict:
    """Add reporting boolean to station if available"""
    good = load_stations(GOOD_PATH)
    for code in stations:
        stations[code]["reporting"] = code in good
    return stations


def check_local_icaos() -> None:
    """Load local ICAO file if available. Not included in distro"""
    icao_path = _FILE_DIR.parent.parent / "data" / "icaos.json"
    if not icao_path.exists():
        return
    _SOURCE["icaos"] = icao_path.open().read().strip()


def check_local_awos() -> None:
    """Load local AWOS file if available. Not included in distro"""
    awos_path = _FILE_DIR.parent.parent / "data" / "awos.json"
    if not awos_path.exists():
        return
    _SOURCE["awos"] = awos_path.open().read().strip()


def download_source_files() -> bool:
    """Returns True if source files updated successfully"""
    for key, route in _SOURCES.items():
        resp = httpx.get(route)
        if resp.status_code != 200:
            return False
        _SOURCE[key] = resp.text
    return True


def update_station_info_date() -> None:
    """Update the package's station meta date"""
    meta_path = _FILE_DIR.parent / "station" / "meta.py"
    meta = meta_path.open().read()
    target = '__LAST_UPDATED__ = "'
    start = meta.find(target) + len(target)
    prefix = meta[:start]
    end = start + 10
    output = prefix + date.today().strftime(r"%Y-%m-%d") + meta[end:]
    with meta_path.open("w") as out:
        out.write(output)


def main() -> int:
    """Build/update the stations.json main file"""
    LOG.info("Fetching")
    if not download_source_files():
        LOG.error("Unable to update source files")
        return 1
    check_local_icaos()
    check_local_awos()
    LOG.info("Cleaning")
    clean_source_files()
    LOG.info("Building")
    load_codes()
    stations, code_map = build_stations()
    stations = add_missing_stations(stations)
    stations = add_reporting(stations)
    stations = add_runways(stations, code_map)
    LOG.info("Saving")
    json.dump(
        stations,
        OUTPUT_PATH.open("w", encoding="utf8"),
        sort_keys=True,
        indent=1,
        ensure_ascii=False,
    )
    LOG.info("Updating station date")
    update_station_info_date()
    return 0


if __name__ == "__main__":
    LOG.setLevel("INFO")
    main()
