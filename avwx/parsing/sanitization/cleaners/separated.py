"""Cleaners where an element is separated."""

from avwx.parsing.sanitization.base import CombineItems
from avwx.static.core import CLOUD_LIST, CLOUD_TRANSLATIONS, WIND_UNITS


class SeparatedDistance(CombineItems):
    """Distance digit and/or unit.
    Ex: 10 SM
    """

    def can_handle(self, first: str, second: str) -> bool:
        return first.isdigit() and second in {"SM", "0SM"}


class SeparatedFirstTemperature(CombineItems):
    """Temperature before slash.
    Ex: 12 /10
    """

    def can_handle(self, first: str, second: str) -> bool:
        return first.isdigit() and len(second) > 2 and second[0] == "/" and second[1:].isdigit()


class SeparatedCloudAltitude(CombineItems):
    """Known cloud types.
    Ex: OVC 040
    """

    def can_handle(self, first: str, second: str) -> bool:
        return second.isdigit() and first in CLOUD_LIST


class SeparatedSecondTemperature(CombineItems):
    """Temperature after slash.
    Ex: 12/ 10
    """

    def can_handle(self, first: str, second: str) -> bool:
        return second.isdigit() and len(first) > 2 and first.endswith("/") and first[:-1].isdigit()


class SeparatedAltimeterLetter(CombineItems):
    """Altimeter letter prefix.
    Ex: Q 1001
    """

    def can_handle(self, first: str, second: str) -> bool:
        if not second.isdigit():
            return False
        if first == "Q":
            return second[0] in {"0", "1"}
        return second[0] in {"2", "3"} if first == "A" else False


class SeparatedTemperatureTrailingDigit(CombineItems):
    """Dewpoint split.
    Ex: 12/1 0
    """

    def can_handle(self, first: str, second: str) -> bool:
        return (
            len(second) == 1
            and second.isdigit()
            and len(first) > 3
            and first[:2].isdigit()
            and "/" in first
            and first[3:].isdigit()
        )


class SeparatedWindUnit(CombineItems):
    """Wind unit disconnected or split in two."""

    def can_handle(self, first: str, second: str) -> bool:
        # 36010G20 KT
        if (
            second in WIND_UNITS
            and first[-1].isdigit()
            and (first[:5].isdigit() or (first.startswith("VRB") and first[3:5].isdigit()))
        ):
            return True
        # 36010K T
        return (
            second == "T"
            and len(first) >= 6
            and (first[:5].isdigit() or (first.startswith("VRB") and first[3:5].isdigit()))
            and first[-1] == "K"
        )


class SeparatedCloudQualifier(CombineItems):
    """Cloud descriptors.
    Ex: OVC022 CB
    """

    def can_handle(self, first: str, second: str) -> bool:
        return second in CLOUD_TRANSLATIONS and second not in CLOUD_LIST and len(first) >= 3 and first[:3] in CLOUD_LIST


class SeparatedTafTimePrefix(CombineItems):
    """TAF new time period.
    Ex: FM 122400
    """

    def can_handle(self, first: str, second: str) -> bool:
        return first in {"FM", "TL"} and (second.isdigit() or (second.endswith("Z") and second[:-1].isdigit()))


class SeparatedMinMaxTemperaturePrefix(CombineItems):
    """TAF min max temperature prefix.
    Ex: TX 20/10
    """

    def can_handle(self, first: str, second: str) -> bool:
        return first in {"TX", "TN"} and "/" in second
