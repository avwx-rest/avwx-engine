"""
GFS service forecast parsing tests
"""

# pylint: disable=protected-access,missing-class-docstring

# library
import pytest

# module
from avwx.forecast import gfs

# tests
from tests.util import assert_number, get_data
from .test_base import ForecastBase


def test_thunder():
    """Tests that a line is converted into Number tuples"""
    text = "T06     12/16  0/ 5"
    _values = (None, None, (("12", 12), ("16", 16)), None, (("0", 0), ("5", 5)))
    for codes, values in zip(gfs._thunder(text), _values):
        if values is None:
            assert codes is None
        else:
            for code, value in zip(codes, values):
                assert_number(code, *value)


@pytest.mark.parametrize("ref,icao,issued", get_data(__file__, "mav"))
class TestMav(ForecastBase):
    report = gfs.Mav


@pytest.mark.parametrize("ref,icao,issued", get_data(__file__, "mex"))
class TestMex(ForecastBase):
    report = gfs.Mex
