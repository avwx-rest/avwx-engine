"""
Item replacement cleaner tests
"""

import pytest

from avwx.parsing.sanitization.cleaners import replace as cleaners


@pytest.mark.parametrize(
    "item,clean",
    (
        ("CALM", "00000KT"),
        ("A01", "AO1"),
        ("PROB3O", "PROB30"),
    ),
)
def test_replace_item(item: str, clean: str):
    cleaner = cleaners.ReplaceItem()
    assert cleaner.can_handle(item) is True
    assert cleaner.clean(item) == clean


@pytest.mark.parametrize("item", ("KMCO", "VRB12KT"))
def test_not_replace_item(item: str):
    assert cleaners.ReplaceItem().can_handle(item) is False
