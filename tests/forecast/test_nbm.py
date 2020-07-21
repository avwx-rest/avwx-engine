"""
NBM service forecast parsing tests
"""

# pylint: disable=protected-access,missing-class-docstring

# module
from avwx.forecast import nbm

# tests
from .test_base import ForecastBase


class TestNbs(ForecastBase):
    def test_ceiling(self):
        """
        Tests that a line is converted into ceiling-specific Numbers
        """
        line = "CIG  12888    45"
        values = [
            ("12", 1200, "one two hundred"),
            ("888", None, "unlimited"),
            None,
            ("45", 4500, "four five hundred"),
        ]
        for number, expected in zip(nbm._ceiling(line), values):
            if expected is None:
                self.assertIsNone(number)
            else:
                self.assert_number(number, *expected)

    def test_nbs_ete(self):
        """
        Performs an end-to-end test of all MEX JSON files
        """
        self._test_forecast_ete(nbm.Nbs)
