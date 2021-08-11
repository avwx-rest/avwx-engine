"""
Builds the aircraft code dict

Copy and paste the table from
https://en.wikipedia.org/wiki/List_of_ICAO_aircraft_type_designators
and place in data/aircraft.txt
"""

import json
from pathlib import Path

_FILE_DIR = Path(__file__).parent
AIRCRAFT_PATH = _FILE_DIR / "data" / "aircraft.tsv"
OUTPUT_PATH = _FILE_DIR.parent / "avwx" / "data" / "aircraft.json"


def main() -> int:
    """Builds/updates aircraft.json codes"""
    craft = {}
    for line in AIRCRAFT_PATH.open(encoding="utf8").readlines():
        code, _, name = line.strip().split("\t")
        if code not in craft:
            craft[code] = name
    json.dump(craft, OUTPUT_PATH.open("w", encoding="utf8"))
    return 0


if __name__ == "__main__":
    main()
