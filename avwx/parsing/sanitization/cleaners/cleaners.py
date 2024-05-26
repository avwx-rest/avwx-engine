"""Cleaners for elements not found in other files."""

from textwrap import wrap

from avwx.parsing.core import is_unknown
from avwx.parsing.sanitization.base import CleanItem, RemoveItem
from avwx.static.core import WX_TRANSLATIONS


class OnlySlashes(RemoveItem):
    """Remove elements containing only '/'."""

    def can_handle(self, item: str) -> bool:
        return is_unknown(item)


class TrimWxCode(CleanItem):
    """Remove RE from wx codes: REVCTS -> VCTS."""

    def can_handle(self, item: str) -> bool:
        if not item.startswith("RE") or item == "RE":
            return False
        return all(sub in WX_TRANSLATIONS for sub in wrap(item[2:], 2))

    def clean(self, item: str) -> str:
        return item[2:]
