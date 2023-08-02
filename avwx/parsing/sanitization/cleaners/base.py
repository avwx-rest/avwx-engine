"""
Cleaning base classes
"""

# pylint: disable=too-few-public-methods,abstract-method

from typing import List, Optional, Type, Union


class Cleaner:
    """Base Cleaner type"""

    # Set to True if no more cleaners should check this item
    should_break: bool = False


class SingleItem(Cleaner):
    """Cleaner looks at a single item"""

    def can_handle(self, item: str) -> bool:
        """Returns True if the element can and needs to be cleaned"""
        raise NotImplementedError()


class RemoveItem(SingleItem):
    """Sanitization should remove item if handled"""

    should_break = True


class CleanItem(SingleItem):
    """Sanitization should clean/replace item if handled"""

    def clean(self, item: str) -> str:
        """Cleans the raw string"""
        raise NotImplementedError()


class SplitItem(Cleaner):
    """Sanitization should split the item in two at an index if handled"""

    def split_at(self, item: str) -> Optional[int]:
        """Returns the string index where the item should be split"""
        raise NotImplementedError()


class CombineItems(Cleaner):
    """Sanitization should combine two different items if handled"""

    def can_handle(self, first: str, second: str) -> bool:
        """Returns True if both elements can and need to be combined"""
        raise NotImplementedError()


CleanerListType = List[
    Union[Type[CleanItem], Type[RemoveItem], Type[SplitItem], Type[CombineItems]]
]
