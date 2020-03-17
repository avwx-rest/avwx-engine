"""
Testing utilities
"""

# stdlib
import unittest
from datetime import datetime
from pathlib import Path

# module
from avwx import structs


class BaseTest(unittest.TestCase):
    """
    TestCase with added assert methods
    """

    def assert_number(
        self, num: structs.Number, repr: str, value: object = None, spoken: str = None
    ):
        """
        Tests string conversion into a Number dataclass
        """
        if not repr:
            self.assertIsNone(num)
        else:
            self.assertIsInstance(num, structs.Number)
            self.assertEqual(num.repr, repr)
            self.assertEqual(num.value, value)
            if spoken:
                self.assertEqual(num.spoken, spoken)

    def assert_timestamp(self, ts: structs.Timestamp, repr: str, value: datetime):
        """
        Tests string conversion into a Timestamp dataclass
        """
        if not repr:
            self.assertIsNone(ts)
        else:
            self.assertIsInstance(ts, structs.Timestamp)
            self.assertEqual(ts.repr, repr)
            self.assertEqual(ts.dt, value)


def get_data(filepath: str, report_type: str) -> [Path]:
    """
    Returns a glob iterable of JSON files
    """
    path = Path(filepath).parent.joinpath("data", report_type)
    return path.glob("*.json")
