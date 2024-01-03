"""
Other cleaner tests
"""

import pytest

from avwx.parsing.sanitization.cleaners import cleaners, base as abc


@pytest.mark.parametrize("item", ("/" * i for i in range(1, 8)))
def test_only_slashes(item: str):
    assert cleaners.OnlySlashes().can_handle(item) is True


@pytest.mark.parametrize("item", ("/////KT", "KMCO", "//SM", "TX12/1234"))
def test_not_only_slashes(item: str):
    assert cleaners.OnlySlashes().can_handle(item) is False


@pytest.mark.parametrize(
    "item,clean",
    (
        ("REVCTS", "VCTS"),
        ("REBR", "BR"),
    ),
)
def test_trim_wx_code(item: str, clean: str):
    cleaner = cleaners.TrimWxCode()
    assert cleaner.can_handle(item) is True
    assert cleaner.clean(item) == clean


@pytest.mark.parametrize("item", ("REMARKS", "RE", "REF", "RECON", "REQ", "BR", "VCTS"))
def test_not_trim_wx_code(item: str):
    assert cleaners.TrimWxCode().can_handle(item) is False


def test_cleaner_abc():
    """Test that cleaner base classes don't implement core methods"""
    for cleaner in (abc.SingleItem, abc.RemoveItem, abc.CleanItem):
        with pytest.raises(NotImplementedError):
            cleaner().can_handle("")
    with pytest.raises(NotImplementedError):
        abc.CleanItem().clean("")
    with pytest.raises(NotImplementedError):
        abc.SplitItem().split_at("")
    with pytest.raises(NotImplementedError):
        abc.CombineItems().can_handle("", "")
