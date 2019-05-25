"""
Builds the aircraft code dict

Copy and paste the table from
https://en.wikipedia.org/wiki/List_of_ICAO_aircraft_type_designators
and place in data/aircraft.txt
"""

import json
from pathlib import Path

AIRCRAFT_PATH = Path("data", "aircraft.txt")
OUTPUT_PATH = Path("..", "avwx", "aircraft.json")


def main() -> int:
    """
    Builds/updates aircraft.json codes
    """
    craft = {}
    for line in AIRCRAFT_PATH.open().readlines():
        code, _, name = line.strip().split("\t")
        if code not in craft:
            craft[code] = name
    json.dump(craft, OUTPUT_PATH.open("w"))
    return 0


if __name__ == "__main__":
    main()
