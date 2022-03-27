"""
Build navaid coordinate map
"""

import json
from pathlib import Path
import httpx

# redirect https://ourairports.com/data/navaids.csv
URL = "https://davidmegginson.github.io/ourairports-data/navaids.csv"
OUTPUT_PATH = Path(__file__).parent / "files" / "navaids.json"


def main():
    """Builds the navaid coordinate map"""
    text = httpx.get(URL).text
    lines = text.strip().split("\n")
    lines.pop(0)
    data = {}
    for line in lines:
        line = line.split(",")
        try:
            ident, lat, lon = line[2].strip('"'), float(line[6]), float(line[7])
        except ValueError:
            continue
        if not ident:
            continue
        try:
            data[ident].add((lat, lon))
        except KeyError:
            data[ident] = {(lat, lon)}
    data = {k: list(v) for k, v in data.items()}
    json.dump(data, OUTPUT_PATH.open("w"), sort_keys=True)


if __name__ == "__main__":
    main()
