"""Build navaid coordinate map."""

import json
from pathlib import Path

import httpx

# redirect https://ourairports.com/data/navaids.csv
URL = "https://davidmegginson.github.io/ourairports-data/navaids.csv"
OUTPUT_PATH = Path(__file__).parent / "files" / "navaids.json"


def main() -> None:
    """Build the navaid coordinate map."""
    text = httpx.get(URL).text
    lines = text.strip().split("\n")
    lines.pop(0)
    data: dict[str, set[tuple[float, float]]] = {}
    for line_str in lines:
        line = line_str.split(",")
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
    with OUTPUT_PATH.open(encoding="utf8") as fin:
        output = json.load(fin)
    output |= {k: list(v) for k, v in data.items()}
    json.dump(output, OUTPUT_PATH.open("w", encoding="utf8"), sort_keys=True, indent=1)


if __name__ == "__main__":
    main()
