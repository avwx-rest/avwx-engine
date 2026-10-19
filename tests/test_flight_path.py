"""Flight path tests."""

from __future__ import annotations

# library
import pytest

# module
from avwx import flight_path
from avwx.structs import Coord

FloatCoordT = tuple[float, float, str]
FloatPathT = FloatCoordT | str
CoordPathT = Coord | str
FlightCaseT = tuple[list[FloatPathT], list[FloatCoordT]]

FLIGHT_PATHS: list[FlightCaseT] = [
    (
        [(12.34, -12.34, "12.34,-12.34"), (-43.21, 43.21, "-43.21,43.21")],
        [(12.34, -12.34, "12.34,-12.34"), (-43.21, 43.21, "-43.21,43.21")],
    ),
    (
        [(12.34, -12.34, "12.34,-12.34"), "KMCO"],
        [(12.34, -12.34, "12.34,-12.34"), (28.43, -81.31, "KMCO")],
    ),
    (["KLEX", "KMCO"], [(38.04, -84.61, "KLEX"), (28.43, -81.31, "KMCO")]),
    (["FLL", "ATL"], [(26.07, -80.15, "FLL"), (33.63, -84.44, "ATL")]),
    (
        ["KMIA", "FLL", "ORL"],
        [(25.8, -80.29, "KMIA"), (26.07, -80.15, "FLL"), (28.54, -81.33, "ORL")],
    ),
    (
        ["FLL", "ORL", "KMCO"],
        [(26.07, -80.15, "FLL"), (28.54, -81.33, "ORL"), (28.43, -81.31, "KMCO")],
    ),
    (
        ["KMIA", "FLL", "ORL", "KMCO"],
        [
            (25.8, -80.29, "KMIA"),
            (26.07, -80.15, "FLL"),
            (28.54, -81.33, "ORL"),
            (28.43, -81.31, "KMCO"),
        ],
    ),
    (
        ["KLEX", "ATL", "ORL", "KMCO"],
        [
            (38.04, -84.61, "KLEX"),
            (33.63, -84.44, "ATL"),
            (28.54, -81.33, "ORL"),
            (28.43, -81.31, "KMCO"),
        ],
    ),
    (
        ["KLEX", "ATL", "KDAB", "ORL", "KMCO"],
        [
            (38.04, -84.61, "KLEX"),
            (33.63, -84.44, "ATL"),
            (29.18, -81.06, "KDAB"),
            (28.54, -81.33, "ORL"),
            (28.43, -81.31, "KMCO"),
        ],
    ),
]


def _to_coord(paths: list[FloatPathT]) -> list[CoordPathT]:
    coords: list[CoordPathT] = []
    for item in paths:
        if isinstance(item, tuple):
            coords.append(Coord(lat=item[0], lon=item[1], repr=item[2]))
        else:
            coords.append(item)
    return coords


@pytest.mark.parametrize(("source", "target"), FLIGHT_PATHS)
def test_to_coordinates(source: list[FloatPathT], target: list[FloatPathT]) -> None:
    """Test coord routing from coords, stations, and navaids."""
    coord_path = _to_coord(source)
    coords = flight_path.to_coordinates(coord_path)
    # Round to prevent minor coord changes from breaking tests
    float_path: list[FloatPathT] = [(round(c.lat, 2), round(c.lon, 2), c.repr or "") for c in coords]
    assert float_path == target


# LEV is both a navaid in Italy and one at Grand Isle, Louisiana; ORL is in Orlando and abroad.
GRAND_ISLE = (29.18, -90.1)


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (["LEV", "CEW", "LEV", "LEV", "LEV"], [GRAND_ISLE, (30.83, -86.68), GRAND_ISLE, GRAND_ISLE, GRAND_ISLE]),
        (["CEW", "LEV", "LEV"], [(30.83, -86.68), GRAND_ISLE, GRAND_ISLE]),
        (["ORL", "ORL", "KMCO"], [(28.54, -81.33), (28.54, -81.33), (28.43, -81.31)]),
    ],
)
def test_repeated_ambiguous_navaids(source: list[str], target: list[tuple[float, float]]) -> None:
    """A repeated ambiguous ident resolves near the unambiguous points, not near itself.

    Comparing an ambiguous ident only with its ambiguous neighbors ties at zero distance,
    and the tie went to the first candidate: these LEVs used to resolve to Italy.
    """
    path = flight_path.to_coordinates(source)  # type: ignore[arg-type]
    assert [(round(c.lat, 2), round(c.lon, 2)) for c in path] == target
    assert [c.repr for c in path] == source
