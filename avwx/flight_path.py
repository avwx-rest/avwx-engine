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


def _resolve(value: Coord | str) -> QCoord:
    """A value's coordinate, or every candidate when it names an ambiguous navaid."""
    if isinstance(value, Coord):
        return value
    try:
        coord = Station.from_icao(value).coord
    except BadStation:
        try:
            candidates = [Coord(lat=c[0], lon=c[1], repr=value) for c in NAVAIDS[value]]
        except KeyError:
            coord = Station.from_code(value).coord
        else:
            if len(candidates) > 1:
                return candidates
            coord = candidates[0]
    coord.repr = value
    return coord


def _neighboring_anchors(resolved: list[QCoord], index: int) -> list[Coord]:
    """The nearest unambiguous coordinate on each side of a position in the path."""
    anchors = []
    for step in (-1, 1):
        i = index + step
        while 0 <= i < len(resolved):
            if isinstance(resolved[i], Coord):
                anchors.append(resolved[i])
                break
            i += step
    return anchors  # type: ignore[return-value]


def _nearest(options: list[Coord], anchors: list[Coord]) -> Coord:
    """The option closest to any of the anchors."""
    return min(options, key=lambda option: min(_distance(option, anchor) for anchor in anchors))


def _resolve_by_anchors(resolved: list[QCoord]) -> list[Coord]:
    """Pick each ambiguous navaid by the unambiguous points around it.

    Every appearance of an ident resolves to the same navaid, chosen as the candidate
    nearest the unambiguous points surrounding any of its appearances. Comparing ambiguous
    neighbors to each other instead lets a repeated ident match itself at zero distance on
    the wrong continent: "LEV CEW LEV LEV" put the last LEVs in Italy, not Louisiana.
    """
    candidates: dict[str, list[Coord]] = {}
    anchors: dict[str, list[Coord]] = {}
    for index, item in enumerate(resolved):
        if isinstance(item, list):
            ident = item[0].repr or ""
            candidates[ident] = item
            anchors.setdefault(ident, []).extend(_neighboring_anchors(resolved, index))
    chosen = {ident: _nearest(options, anchors[ident]) for ident, options in candidates.items()}
    path = []
    for item in resolved:
        if isinstance(item, Coord):
            path.append(item)
        else:
            best = chosen[item[0].repr or ""]
            path.append(Coord(lat=best.lat, lon=best.lon, repr=best.repr))
    return path


def to_coordinates(values: list[Coord | str]) -> list[Coord]:
    """Convert any known idents found in a flight path into coordinates.

    Prefers Coord > ICAO > Navaid > IATA / GPS. An ident naming several navaids resolves to
    the one nearest the unambiguous points around it.
    """
    if not values:
        return []
    cleaned: list[Coord | str] = []
    for value in values:
        if not value:
            continue
        if isinstance(value, str):
            value = value.strip()  # noqa: PLW2901
            if not value:
                continue
        cleaned.append(value)
    resolved = [_resolve(value) for value in cleaned]
    if not any(isinstance(item, list) for item in resolved):
        return resolved  # type: ignore[return-value]
    if any(isinstance(item, Coord) for item in resolved):
        return _resolve_by_anchors(resolved)
    # Nothing unambiguous to anchor on: fall back to comparing neighbors with each other.
    return _to_coordinates(cleaned)
