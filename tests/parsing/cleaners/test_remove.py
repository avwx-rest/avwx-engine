"""
Item removal cleaner tests
"""

import pytest

from avwx.parsing.sanitization.cleaners.base import RemoveItem
from avwx.parsing.sanitization.cleaners import remove as cleaners


def test_remove_items_in():
    cleaner = cleaners.remove_items_in({"2", "4"})()
    assert isinstance(cleaner, RemoveItem)
    items = [str(i) for i in range(1, 6)]
    filtered = [i for i in items if not cleaner.can_handle(i)]
    assert filtered == ["1", "3", "5"]


@pytest.mark.parametrize("item", ("CCA", "CCB", "CCZ"))
def test_remove_taf_amend(item: str):
    assert cleaners.RemoveTafAmend().can_handle(item) is True


@pytest.mark.parametrize("item", ("CCTV", "CB"))
def test_not_remove_taf_amend(item: str):
    assert cleaners.RemoveTafAmend().can_handle(item) is False
