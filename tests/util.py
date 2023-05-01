"""
Testing utilities
"""

# pylint: disable=redefined-builtin,invalid-name

# stdlib
import json
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional, Tuple, Union

# module
from avwx import structs


def assert_number(
    num: structs.Number, repr: str, value: object = None, spoken: str = None
):
    """Tests string conversion into a Number dataclass"""
    if not repr:
        assert num is None
    else:
        assert isinstance(num, structs.Number)
        assert num.repr == repr
        assert num.value == value
        if spoken:
            assert num.spoken == spoken


def assert_timestamp(ts: structs.Timestamp, repr: str, value: datetime):
    """Tests string conversion into a Timestamp dataclass"""
    if not repr:
        assert ts is None
    else:
        assert isinstance(ts, structs.Timestamp)
        assert ts.repr == repr
        assert ts.dt == value


def assert_code(code: structs.Code, repr: Any, value: Any):
    """Tests string conversion into a conditional Code dataclass"""
    if not repr:
        assert code is None
    elif isinstance(code, str):
        assert code == repr
    else:
        assert isinstance(code, structs.Code)
        assert code.repr == repr
        assert code.value == value


def assert_value(src: Optional[structs.Number], value: Union[int, float, None]):
    """Tests a number's value matches the expected value while handling nulls"""
    if value is None:
        assert src is None
    else:
        assert src.value == value


def get_data(filepath: str, report_type: str) -> Iterator[Tuple[dict, str, datetime]]:
    """Returns a glob iterable of JSON files"""
    path = Path(filepath).parent.joinpath("data", report_type)
    for result in path.glob("*.json"):
        data = json.load(result.open(), object_hook=datetime_parser)
        icao = data.pop("icao")
        created = data.pop("created").date()
        yield data, icao, created


def datetime_parser(data: dict) -> dict:
    """Convert ISO strings into datetime objects"""
    for key, val in data.items():
        if isinstance(val, str) and len(val) > 6:
            if val[-3] == ":" and val[-6] in "+-":
                with suppress(ValueError):
                    data[key] = datetime.fromisoformat(val)
            with suppress(ValueError):
                data[key] = datetime.strptime(val, r"%Y-%m-%d")
    return data


def round_coordinates(data: Any) -> Any:
    """Recursively round lat,lon floats to 2 digits"""
    if isinstance(data, dict):
        for key, val in data.items():
            data[key] = (
                round(val, 2) if key in {"lat", "lon"} else round_coordinates(val)
            )
    elif isinstance(data, list):
        data = [round_coordinates(i) for i in data]
    return data
