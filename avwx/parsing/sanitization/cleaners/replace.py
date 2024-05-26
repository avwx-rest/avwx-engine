"""Cleaners for elements that should be replaced."""

from avwx.parsing.sanitization.base import CleanItem

# These replacement dicts are applied when the report is still a string

_SHARED = {
    "!": "1",
    "@": "2",
    "#": "3",
    "%": "5",
    "^": "6",
    "&": "7",
    "*": "8",
    "?": " ",
    '"': "",
    "'": "",
    "`": "",
    ".": "",
    "(": " ",
    ")": " ",
    ";": " ",
}

_WIND = {
    "MISSINGKT": "",
    " 0I0": " 090",
    "NOSIGKT ": "KT NOSIG ",
    "KNOSIGT ": "KT NOSIG ",
    "/VRB": " VRB",
    "CALMKT ": "CALM ",
    "CLMKT ": "CALM ",
    "CLRKT ": "CALM ",
}

_VISIBILITY = {
    " <1/": " M1/",  # <1/4SM <1/8SM
    "/04SM": "/4SM",
    "/4SSM": "/4SM",
    "/08SM": "/8SM",
    " /34SM": "3/4SM",
    " 3/SM": " 3/4SM",
    "PQ6SM ": "P6SM ",
    "P6000F ": "P6000FT ",
    "P6000FTQ ": "P6000FT ",
}

_CLOUD = {
    " C A V O K ": " CAVOK ",
    "N0SIG": "NOSIG",
    "SCATTERED": "SCT",
    "BROKEN": "BKN",
    "OVERCAST": "OVC",
}

CURRENT = _SHARED | _WIND | _VISIBILITY | _CLOUD


# These are item replacements after the report has been split

ITEM_REPL = {"CALM": "00000KT", "A01": "AO1", "A02": "AO2", "PROB3O": "PROB30"}


class ReplaceItem(CleanItem):
    """Replace report elements after splitting."""

    def can_handle(self, item: str) -> bool:
        return item in ITEM_REPL

    def clean(self, item: str) -> str:
        return ITEM_REPL[item]
