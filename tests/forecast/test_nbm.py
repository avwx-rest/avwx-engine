"""
NBM service forecast parsing tests
"""

# pylint: disable=protected-access,missing-class-docstring

# module
from avwx.forecast import nbm

# tests
from .test_base import ForecastBase


class TestNbm(ForecastBase):
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

    def test_wind(self):
        """
        Tests that a line is converted into wind-specific Numbers
        """
        line = "GST  12 NG    45"
        values = [
            ("12", 12, "one two"),
            ("NG", 0, "zero"),
            None,
            ("45", 45, "four five"),
        ]
        for number, expected in zip(nbm._wind(line), values):
            if expected is None:
                self.assertIsNone(number)
            else:
                self.assert_number(number, *expected)

    def test_nbh_ete(self):
        """
        Performs an end-to-end test of all NBH JSON files
        """
        self._test_forecast_ete(nbm.Nbh)

    def test_nbs_ete(self):
        """
        Performs an end-to-end test of all NBS JSON files
        """
        self._test_forecast_ete(nbm.Nbs)

    def test_nbe_ete(self):
        """
        Performs an end-to-end test of all NBE JSON files
        """
        self._test_forecast_ete(nbm.Nbe)
