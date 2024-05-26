"""Cleaning base classes."""

from __future__ import annotations


class Cleaner:
    """Base Cleaner type."""

    # Set to True if no more cleaners should check this item
    should_break: bool = False


class SingleItem(Cleaner):
    """Cleaner looks at a single item."""

    def can_handle(self, item: str) -> bool:
        """Return True if the element can and needs to be cleaned."""
        raise NotImplementedError


class DoubleItem(Cleaner):
    """Cleaner that looks at two neighboring items."""

    def can_handle(self, first: str, second: str) -> bool:
        """Return True if neighboring pairs need to be cleaned."""
        raise NotImplementedError


class RemoveItem(SingleItem):
    """Sanitization should remove item if handled."""

    should_break = True


class CleanItem(SingleItem):
    """Sanitization should clean/replace item if handled."""

    def clean(self, item: str) -> str:
        """Clean the raw string."""
        raise NotImplementedError


class CleanPair(DoubleItem):
    """Sanitization should clean both paired items."""

    def clean(self, first: str, second: str) -> tuple[str, str]:
        """Clean both raw strings."""
        raise NotImplementedError


class SplitItem(Cleaner):
    """Sanitization should split the item in two at an index if handled"""

    def split_at(self, item: str) -> int | None:
        """Return the string index where the item should be split."""
        raise NotImplementedError


class CombineItems(Cleaner):
    """Sanitization should combine two different items if handled."""

    def can_handle(self, first: str, second: str) -> bool:
        """Return True if both elements can and need to be combined."""
        raise NotImplementedError


CleanerListType = list[type[CleanItem] | type[CleanPair] | type[RemoveItem] | type[SplitItem] | type[CombineItems]]
