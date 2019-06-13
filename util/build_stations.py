"""
Builds the master station list

Source file for airports.csv and runways.csv can be downloaded from
http://ourairports.com/data/
"""

# stdlib
import csv
import json
from pathlib import Path

STATION_PATH = Path("data", "airports.csv")
RUNWAY_PATH = Path("data", "runways.csv")
OUTPUT_PATH = Path("..", "avwx", "stations.json")

ACCEPTED_STATION_TYPES = [
    # 'balloonport',
    # 'closed',
    # 'heliport',
    "large_airport",
    "medium_airport",
    "seaplane_base",
    "small_airport",
]


def format_station(station: [str]) -> dict:
    """
    Converts source station list into info dict
    """
    try:
        elev_ft = float(station[6])
        elev_m = round(elev_ft * 0.3048)
        elev_ft = round(elev_ft)
    except ValueError:
        elev_ft, elev_m = None, None
    iloc = station[9].find("-")
    ret = {
        "type": station[2],
        "name": station[3],
        "latitude": float(station[4]),
        "longitude": float(station[5]),
        "elevation_ft": elev_ft,
        "elevation_m": elev_m,
        "country": station[9][:iloc],
        "state": station[9][iloc + 1 :],
        "city": station[10],
        "icao": station[1],
        "iata": station[13],
        "website": station[15],
        "wiki": station[16],
        "note": station[17],
    }
    # Nullify empty strings
    for key, val in ret.items():
        if val == "":
            ret[key] = None
    return ret


def build_stations() -> dict:
    """
    Builds the station dict from source file
    """
    stations = {}
    data = csv.reader(STATION_PATH.open())
    next(data)  # Skip header
    for station in data:
        if len(station[1]) != 4:
            continue
        if station[2] in ACCEPTED_STATION_TYPES:
            stations[station[1]] = format_station(station)
    return stations


def add_runways(stations: dict) -> dict:
    """
    Add runway information to station if availabale
    """
    data = csv.reader(RUNWAY_PATH.open())
    next(data)  # Skip header
    for runway in data:
        data = {
            "length_ft": int(runway[3]) if runway[3] else 0,
            "width_ft": int(runway[4]) if runway[4] else 0,
            "ident1": runway[8],
            "ident2": runway[14],
        }
        station = runway[2]
        if station in stations:
            if "runways" in stations[station]:
                stations[station]["runways"].append(data)
            else:
                stations[station]["runways"] = [data]
    # Sort runways by longest length and add missing nulls
    for station in stations:
        if "runways" in stations[station]:
            stations[station]["runways"].sort(
                key=lambda x: x["length_ft"], reverse=True
            )
        else:
            stations[station]["runways"] = None
    return stations


def main() -> int:
    """
    Build/update the stations.json master file
    """
    stations = build_stations()
    stations = add_runways(stations)
    json.dump(stations, OUTPUT_PATH.open("w"), sort_keys=True)
    return 0


if __name__ == "__main__":
    main()
