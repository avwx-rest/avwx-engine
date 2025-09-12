"""Builds the aircraft code dict."""

# stdlib
import json
import re
from pathlib import Path

# library
import httpx

URL = "https://en.wikipedia.org/wiki/List_of_ICAO_aircraft_type_designators"
OUTPUT_PATH = Path(__file__).parent / "files" / "aircraft.json"
TAG_PATTERN = re.compile(r"<[^>]*>")


def main() -> int:
    """Build/update aircraft.json codes."""
    resp = httpx.get(URL)
    if resp.status_code != 200:
        return 1
    text = resp.text
    text = text[text.find("<caption>ICAO") :]
    rows = text[: text.find("</table>")].split("<tr>")[2:]
    craft = {}
    for row in rows:
        cols = row.split("\n")
        name = TAG_PATTERN.sub("", cols[3]).strip()
        if not name or "deprecated" in name:
            continue
        code = TAG_PATTERN.sub("", cols[1]).strip()
        if code not in craft:
            craft[code] = name
    old_craft = json.load(OUTPUT_PATH.open(encoding="utf8"))
    json.dump(old_craft | craft, OUTPUT_PATH.open("w", encoding="utf8"), sort_keys=True, indent=1)
    return 0


if __name__ == "__main__":
    main()
