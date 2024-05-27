"""NBM service forecast parsing tests."""

# ruff: noqa: SLF001

# library
import pytest

# module
from avwx.forecast import nbm

# tests
from tests.util import assert_number, get_data

from .test_base import ForecastBase


def test_ceiling() -> None:
    """Test that a line is converted into ceiling-specific Numbers."""
    line = "CIG  12888    45"
    values = [
        ("12", 1200, "one two hundred"),
        ("888", None, "unlimited"),
        None,
        ("45", 4500, "four five hundred"),
    ]
    for number, expected in zip(nbm._ceiling(line), values, strict=True):
        if expected is None:
            assert number is None
        else:
            assert_number(number, *expected)


def test_wind() -> None:
    """Test that a line is converted into wind-specific Numbers."""
    line = "GST  12 NG    45"
    values = [
        ("12", 12, "one two"),
        ("NG", 0, "zero"),
        None,
        ("45", 45, "four five"),
    ]
    for number, expected in zip(nbm._wind(line), values, strict=True):
        if expected is None:
            assert number is None
        else:
            assert_number(number, *expected)


@pytest.mark.parametrize(("ref", "icao", "issued"), get_data(__file__, "nbh"))
class TestNbh(ForecastBase):
    report = nbm.Nbh


@pytest.mark.parametrize(("ref", "icao", "issued"), get_data(__file__, "nbs"))
class TestNbs(ForecastBase):
    report = nbm.Nbs


@pytest.mark.parametrize(("ref", "icao", "issued"), get_data(__file__, "nbe"))
class TestNbe(ForecastBase):
    report = nbm.Nbe


@pytest.mark.parametrize(("ref", "icao", "issued"), get_data(__file__, "nbx"))
class TestNbx(ForecastBase):
    report = nbm.Nbx
