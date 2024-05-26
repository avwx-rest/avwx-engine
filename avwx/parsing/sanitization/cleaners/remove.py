"""Cleaners for elements that should be removed."""

from avwx.parsing.sanitization.base import RemoveItem

_SHARED = {
    "$",
    "KT",  # Place after extra-space-exists cleaners
    "M",
    ".",
    "1/SM",
}

_CURRENT = {
    "AUTO",
    "COR",
    "NSC",
    "NCD",
    "RTD",
    "SPECI",
    "CORR",
}

_METAR = {
    *_SHARED,
    *_CURRENT,
    "METAR",
    "CLR",
    "SKC",
}

_TAF = {
    *_SHARED,
    *_CURRENT,
    "TAF",
    "TTF",
}


def remove_items_in(filter_out: set[str]) -> type[RemoveItem]:
    """Generate a RemoveItem cleaner to filter a given set of strings."""

    class RemoveInList(RemoveItem):
        """Cleaner to remove items in a list"""

        def can_handle(self, item: str) -> bool:
            return item in filter_out

    return RemoveInList


RemoveFromMetar = remove_items_in(_METAR)
RemoveFromTaf = remove_items_in(_TAF)


class RemoveTafAmend(RemoveItem):
    """Remove amend signifier from start of report ('CCA', 'CCB', etc)."""

    def can_handle(self, item: str) -> bool:
        return len(item) == 3 and item.startswith("CC") and item[2].isalpha()
