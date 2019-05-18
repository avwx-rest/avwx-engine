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
    with open(AIRCRAFT_PATH) as fin:
        lines = fin.readlines()
    craft = {}
    for line in lines:
        code, _, name = line.strip().split("\t")
        if code not in craft:
            craft[code] = name
    json.dump(craft, open(OUTPUT_PATH, "w"))
    return 0


if __name__ == "__main__":
    main()
