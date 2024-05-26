"""Cleaners for visibility elements."""

from itertools import permutations

from avwx.parsing.core import is_runway_visibility
from avwx.parsing.sanitization.base import CleanItem

VIS_PERMUTATIONS = ["".join(p) for p in permutations("P6SM")]
VIS_PERMUTATIONS.remove("6MPS")
VIS_PERMUTATIONS += ["6+SM"]


class VisibilityGreaterThan(CleanItem):
    """Fix inconsistent 'P6SM'.
    Ex: TP6SM or 6PSM -> P6SM
    """

    def can_handle(self, item: str) -> bool:
        return len(item) > 3 and item[-4:] in VIS_PERMUTATIONS

    def clean(self, _: str) -> str:
        return "P6SM"


class RunwayVisibilityUnit(CleanItem):
    """Fix RVR where FT unit is cut short."""

    def can_handle(self, item: str) -> bool:
        return is_runway_visibility(item) and item.endswith("F")

    def clean(self, item: str) -> str:
        return f"{item}T"
