"""
Testing utilities
"""

# stdlib
import unittest
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


def get_data(filepath: str, report_type: str) -> [Path]:
    """
    Returns a glob iterable of JSON files
    """
    path = Path(filepath).parent.joinpath("data", report_type)
    return path.glob("*.json")
