"""Cleaners for wind elements."""

import re

from avwx.parsing.core import is_unknown
from avwx.parsing.sanitization.base import CleanItem, RemoveItem

WIND_REMV = ("/", "-", "{", "}", "(N)", "(E)", "(S)", "(W)")

WIND_REPL = {
    "O": "0",
    "|": "1",
    "MPSM": "MPS",  # conflict with SM
    "FG": "G",
    "GG": "G",
    "GT": "G",
    "GS": "G",
    "SQ": "G",
    "CT": "KT",
    "JT": "KT",
    "SM": "KT",
    "KTKT": "KT",  # Must come before TK
    "TK": "KT",
    "LKT": "KT",
    "ZKT": "KT",
    "KKT": "KT",
    "JKT": "KT",
    "KLT": "KT",
    "TKT": "KT",
    "GKT": "KT",
    "PKT": "KT",
    "XKT": "KT",
    "VRBL": "VRB",  # Not caught in WIND_VRB
}

WIND_VRB = ("WBB",)

KT_PATTERN = re.compile(r"\b[\w\d]*\d{2}K[^T]\b")


def sanitize_wind(text: str) -> str:
    """Fix rare wind issues that may be too broad otherwise."""
    for rep in WIND_REMV:
        text = text.replace(rep, "")
    for key, rep in WIND_REPL.items():
        text = text.replace(key, rep)
    if len(text) > 4 and not text.startswith("VRB") and not text[:3].isdigit():
        # Catches majority of cases where at least two valid letters are found
        if len(set(text[:4]).intersection({"V", "R", "B"})) > 1:
            for i, char in enumerate(text):
                if char.isdigit():
                    text = f"VRB{text[i:]}"
                    break
        else:
            for key in WIND_VRB:
                if text.startswith(key):
                    zero = "0" if key[-1] == "0" else ""
                    text = text.replace(key, f"VRB{zero}")
                    break
    # Final check for end units. Remainder of string would be fixed at this point if valid
    # For now, it's only checking for K(T) since that is most instances
    # The parser can still handle/expect missing and spearated units
    if KT_PATTERN.match(text):
        text = f"{text[:-1]}T"
    if text.endswith("K"):
        text += "T"
    return text


class EmptyWind(RemoveItem):
    """Remove empty wind /////KT."""

    def can_handle(self, item: str) -> bool:
        return item.endswith("KT") and is_unknown(item[:-2])


# TODO: Generalize to find anywhere in wind. Maybe add to other wind sans?
class MisplaceWindKT(CleanItem):
    """Fix misplaced KT 22022KTG40."""

    def can_handle(self, item: str) -> bool:
        return len(item) == 10 and "KTG" in item and item[:5].isdigit()

    def clean(self, item: str) -> str:
        return item.replace("KTG", "G") + "KT"


class DoubleGust(CleanItem):
    """Fix gust double G.
    Ex: 360G17G32KT
    """

    def can_handle(self, item: str) -> bool:
        return len(item) > 10 and item.endswith("KT") and item[3] == "G"

    def clean(self, item: str) -> str:
        return item[:3] + item[4:]


class WindLeadingMistype(CleanItem):
    """Fix leading character mistypes in wind."""

    def can_handle(self, item: str) -> bool:
        return (
            len(item) > 7
            and not item[0].isdigit()
            and not item.startswith("VRB")
            and item.endswith("KT")
            and not item.startswith("WS")
        )

    def clean(self, item: str) -> str:
        while item and not item[0].isdigit() and not item.startswith("VRB"):
            item = item[1:]
        return item


class NonGGust(CleanItem):
    """Fix non-G gust.
    Ex: 14010-15KT
    """

    def can_handle(self, item: str) -> bool:
        return len(item) == 10 and item.endswith("KT") and item[5] != "G"

    def clean(self, item: str) -> str:
        return f"{item[:5]}G{item[6:]}"


class RemoveVrbLeadingDigits(CleanItem):
    """Fix leading digits on VRB wind.
    Ex: 2VRB02KT
    """

    def can_handle(self, item: str) -> bool:
        return len(item) > 7 and item.endswith("KT") and "VRB" in item and item[0].isdigit() and "Z" not in item

    def clean(self, item: str) -> str:
        while item[0].isdigit():
            item = item[1:]
        return item
