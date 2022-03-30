"""
Testing utilities
"""

# pylint: disable=redefined-builtin,invalid-name

# stdlib
import json
import unittest
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

# module
from avwx import structs


class BaseTest(unittest.TestCase):
    """TestCase with added assert methods"""

    def assert_number(
        self, num: structs.Number, repr: str, value: object = None, spoken: str = None
    ):
        """Tests string conversion into a Number dataclass"""
        if not repr:
            self.assertIsNone(num)
        else:
            self.assertIsInstance(num, structs.Number)
            self.assertEqual(num.repr, repr)
            self.assertEqual(num.value, value)
            if spoken:
                self.assertEqual(num.spoken, spoken)

    def assert_timestamp(self, ts: structs.Timestamp, repr: str, value: datetime):
        """Tests string conversion into a Timestamp dataclass"""
        if not repr:
            self.assertIsNone(ts)
        else:
            self.assertIsInstance(ts, structs.Timestamp)
            self.assertEqual(ts.repr, repr)
            self.assertEqual(ts.dt, value)

    def assert_code(self, code: structs.Code, repr: object, value: object):
        """Tests string conversion into a conditional Code dataclass"""
        if not repr:
            self.assertIsNone(code)
        elif isinstance(code, str):
            self.assertEqual(code, repr)
        else:
            self.assertIsInstance(code, structs.Code)
            self.assertEqual(code.repr, repr)
            self.assertEqual(code.value, value)


def get_data(filepath: str, report_type: str) -> Iterator:
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
        if isinstance(val, str):
            if "+00:00" in val:
                with suppress(ValueError):
                    data[key] = datetime.fromisoformat(val)
            with suppress(ValueError):
                data[key] = datetime.strptime(val, r"%Y-%m-%d")
    return data


def round_coordinates(data: Any) -> Any:
    """Recursively round lat,lon floats to 2 digits"""
    if isinstance(data, dict):
        for key, val in data.items():
            if key in ("lat", "lon"):
                data[key] = round(val, 2)
            else:
                data[key] = round_coordinates(val)
    elif isinstance(data, list):
        data = [round_coordinates(i) for i in data]
    return data
