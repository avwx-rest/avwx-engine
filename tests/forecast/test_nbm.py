"""NBM service forecast parsing tests."""

# ruff: noqa: SLF001

# library
import pytest

# module
from avwx.forecast import nbm

# tests
from tests.util import assert_measurement, get_data

from .test_base import ForecastBase


def test_ceiling() -> None:
    """Test that a line is converted into ceiling-specific Measurements."""
    line = "CIG  12888    45"
    values = [1200, None, None, 4500]
    for number, expected in zip(nbm._ceiling(line), values, strict=True):
        assert_measurement(number, expected)


def test_wind() -> None:
    """Test that a line is converted into wind-specific Measurements."""
    line = "GST  12 NG    45"
    values = [12, 0, None, 45]
    for number, expected in zip(nbm._wind(line), values, strict=True):
        assert_measurement(number, expected)


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
