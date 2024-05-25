"""Methods to resolve flight paths in coordinates."""

from __future__ import annotations

# library
from geopy.distance import great_circle  # type: ignore

# module
from avwx.exceptions import BadStation
from avwx.load_utils import LazyLoad
from avwx.station import Station
from avwx.structs import Coord

NAVAIDS = LazyLoad("navaids")
QCoord = Coord | list[Coord]


def _distance(near: Coord, far: Coord) -> float:
    circle = great_circle(near.pair, far.pair).nm
    if not isinstance(circle, float):
        msg = "Could not evaluate great circle distance"
        raise TypeError(msg)
    return circle


def _closest(coord: QCoord, coords: list[Coord]) -> Coord:
    if isinstance(coord, Coord):
        distances = [(_distance(coord, c), c) for c in coords]
    else:
        distances = [(_distance(c, _closest(c, coords)), c) for c in coord]
    distances.sort(key=lambda x: x[0])
    return distances[0][1]


def _best_coord(
    previous: QCoord | None,
    current: QCoord,
    up_next: QCoord | None,
) -> Coord:
    """Determine the best coordinate based on surroundings.
    At least one of these should be a list.
    """
    if previous is None and up_next is None:
        if isinstance(current, list):
            msg = "Unable to determine best coordinate"
            raise TypeError(msg)
        return current
    # NOTE: add handling to determine best midpoint
    if up_next is None:
        up_next = previous
    if isinstance(up_next, list):
        return _closest(current, up_next)
    return _closest(up_next, current)  # type: ignore


def _to_coordinates(values: list[Coord | str], last_value: QCoord | None = None) -> list[Coord]:
    if not values:
        return []
    coord = values[0]
    if isinstance(coord, str):
        coord = coord.strip()
        try:
            value = coord
            coord = Station.from_icao(coord).coord
            coord.repr = value
        except BadStation:
            try:
                coords = [Coord(lat=c[0], lon=c[1], repr=coord) for c in NAVAIDS[coord]]  # type: ignore
            except KeyError:
                value = coord  # type: ignore
                coord = Station.from_code(coord).coord  # type: ignore
                coord.repr = value
            else:
                if len(coords) == 1:
                    coord = coords[0]
                else:
                    new_coords = _to_coordinates(values[1:], coords)
                    new_coord = new_coords[0] if new_coords else None
                    coord = _best_coord(last_value, coords, new_coord)
                    return [coord, *new_coords]
    return [coord, *_to_coordinates(values[1:], coord)]


def to_coordinates(values: list[Coord | str]) -> list[Coord]:
    """Convert any known idents found in a flight path into coordinates.

    Prefers Coord > ICAO > Navaid > IATA / GPS
    """
    if not values:
        return []
    cleaned = []
    for value in values:
        if not value:
            continue
        if isinstance(value, str):
            value = value.strip()  # noqa: PLW2901
            if not value:
                continue
        cleaned.append(value)
    return _to_coordinates(values)
