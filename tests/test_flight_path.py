"""
Flight path tests
"""

# stdlib
from typing import List, Tuple, Union

# library
import pytest

# module
from avwx import flight_path
from avwx.structs import Coord

FLIGHT_PATHS = (
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
        [(25.79, -80.29, "KMIA"), (26.07, -80.15, "FLL"), (28.54, -81.33, "ORL")],
    ),
    (
        ["FLL", "ORL", "KMCO"],
        [(26.07, -80.15, "FLL"), (28.54, -81.33, "ORL"), (28.43, -81.31, "KMCO")],
    ),
    (
        ["KMIA", "FLL", "ORL", "KMCO"],
        [
            (25.79, -80.29, "KMIA"),
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
)


COORD = Tuple[float, float, str]
COORD_SRC = List[Union[COORD, str]]


def _to_coord(coords: COORD_SRC) -> List[Union[Coord, str]]:
    for i, item in enumerate(coords):
        if isinstance(item, tuple):
            coords[i] = Coord(lat=item[0], lon=item[1], repr=item[2])
    return coords


@pytest.mark.parametrize("source,target", FLIGHT_PATHS)
def test_to_coordinates(source: List[str], target: COORD_SRC):
    """Test coord routing from coords, stations, and navaids"""
    source = _to_coord(source)
    coords = flight_path.to_coordinates(source)
    # Round to prevent minor coord changes from breaking tests
    coords = [(round(c.lat, 2), round(c.lon, 2), c.repr) for c in coords]
    assert coords == target
