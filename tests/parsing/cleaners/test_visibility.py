"""Visibility cleaner tests."""

import pytest

from avwx.parsing.sanitization.cleaners import visibility as cleaners


@pytest.mark.parametrize("item", ["TP6SM", "6PSM"])
def test_visibility_greater_than(item: str) -> None:
    cleaner = cleaners.VisibilityGreaterThan()
    assert cleaner.can_handle(item) is True
    assert cleaner.clean(item) == "P6SM"


@pytest.mark.parametrize("item", ["6MPS"])
def test_not_visibility_greater_than(item: str) -> None:
    assert cleaners.VisibilityGreaterThan().can_handle(item) is False


@pytest.mark.parametrize(
    ("item", "clean"),
    [
        ("R02L/4000VP6000F", "R02L/4000VP6000FT"),
        ("R31C/1000F", "R31C/1000FT"),
    ],
)
def test_runway_visibility_unit(item: str, clean: str) -> None:
    cleaner = cleaners.RunwayVisibilityUnit()
    assert cleaner.can_handle(item) is True
    assert cleaner.clean(item) == clean


@pytest.mark.parametrize("item", ["R21/2000", "R01/1500M", "R01R/2000V4000FT"])
def test_not_runway_visibility_unit(item: str) -> None:
    assert cleaners.RunwayVisibilityUnit().can_handle(item) is False
