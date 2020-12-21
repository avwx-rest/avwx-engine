"""
GFS service forecast parsing tests
"""

# pylint: disable=protected-access,missing-class-docstring

# module
from avwx.forecast import gfs

# tests
from .test_base import ForecastBase


class TestMav(ForecastBase):
    def test_thunder(self):
        """Tests that a line is converted into Number tuples"""
        text = "T06     12/16  0/ 5"
        _values = (None, None, (("12", 12), ("16", 16)), None, (("0", 0), ("5", 5)))
        for codes, values in zip(gfs._thunder(text), _values):
            if values is None:
                self.assertIsNone(codes)
            else:
                for code, value in zip(codes, values):
                    self.assert_number(code, *value)

    def test_mav_ete(self):
        """Performs an end-to-end test of all MAV JSON files"""
        self._test_forecast_ete(gfs.Mav)


class TestMex(ForecastBase):
    def test_mex_ete(self):
        """Performs an end-to-end test of all MEX JSON files"""
        self._test_forecast_ete(gfs.Mex)
