"""Cleaners where two items are joined."""

from __future__ import annotations

import re

from avwx.parsing.core import is_timerange, is_timestamp
from avwx.parsing.sanitization.base import SplitItem
from avwx.static.core import CLOUD_LIST
from avwx.static.taf import TAF_NEWLINE, TAF_NEWLINE_STARTSWITH

_CLOUD_GROUP = "(" + "|".join(CLOUD_LIST) + ")"
CLOUD_SPACE_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        f"(?=.+){_CLOUD_GROUP}" + r"\d{3}(\w{2,3})?$",  # SCT010BKN021
        r"M?\d{2}\/M?\d{2}$",  # BKN01826/25
    )
]


class JoinedCloud(SplitItem):
    """For items starting with cloud list."""

    def split_at(self, item: str) -> int | None:
        if item[:3] in CLOUD_LIST:
            for pattern in CLOUD_SPACE_PATTERNS:
                match = pattern.search(item)
                if match is None:
                    continue
                if match.start():
                    return match.start()
        return None


_TIMESTAMP_BREAKS = ((7, is_timestamp), (9, is_timerange))


class JoinedTimestamp(SplitItem):
    """Connected timestamp."""

    def split_at(self, item: str) -> int | None:
        return next(
            (loc for loc, check in _TIMESTAMP_BREAKS if len(item) > loc and check(item[:loc])),
            None,
        )


class JoinedWind(SplitItem):
    """Connected to wind."""

    def split_at(self, item: str) -> int | None:
        if len(item) > 5 and "KT" in item and not item.endswith("KT"):
            index = item.find("KT")
            if index > 4:
                return index + 2
        return None


class JoinedTafNewLine(SplitItem):
    """TAF newline connected to previous element."""

    def split_at(self, item: str) -> int | None:
        for key in TAF_NEWLINE:
            if key in item and not item.startswith(key):
                return item.find(key)
        for key in TAF_NEWLINE_STARTSWITH:
            if key in item and not item.startswith(key):
                index = item.find(key)
                if item[index + len(key) :].isdigit():
                    return index
        return None


class JoinedMinMaxTemperature(SplitItem):
    """Connected TAF min/max temp."""

    def split_at(self, item: str) -> int | None:
        if "TX" in item and "TN" in item and item.endswith("Z") and "/" in item:
            tx_index, tn_index = item.find("TX"), item.find("TN")
            return max(tx_index, tn_index)
        return None


RVR_PATTERN = re.compile(r"R\d{2}[RCL]?/\S+")


class JoinedRunwayVisibility(SplitItem):
    """Connected RVR elements.
    Ex: R36/1500DR18/P2000
    """

    def split_at(self, item: str) -> int | None:
        return match.start() + 1 if (match := RVR_PATTERN.search(item[1:])) else None
