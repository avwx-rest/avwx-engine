"""
Contains report sanitization functions
"""

# pylint: disable=too-many-boolean-expressions,too-many-return-statements,too-many-branches

# stdlib
import re
from itertools import permutations
from typing import List, Optional

# module
from avwx.parsing.core import (
    dedupe,
    is_runway_visibility,
    is_timerange,
    is_timestamp,
    is_unknown,
    is_variable_wind_direction,
    is_wind,
)
from avwx.static.core import CLOUD_LIST, CLOUD_TRANSLATIONS
from avwx.static.taf import TAF_NEWLINE, TAF_NEWLINE_STARTSWITH
from avwx.structs import Sanitization

WIND_REMV = ("/", "-", "(N)", "(E)", "(S)", "(W)")

WIND_REPL = {
    "O": "0",
    "|": "1",
    "GG": "G",
    "GT": "G",
    "GS": "G",
    "K5": "KT",
    "JT": "KT",
    "LKT": "KT",
    "ZKT": "KT",
    "KTKT": "KT",
    "KKT": "KT",
    "JKT": "KT",
    "KLT": "KT",
    "TKT": "KT",
    "GKT": "KT",
    "PKT": "KT",
    "XKT": "KT",
    "MPSM": "MPS",
}

WIND_VRB = ("V0", "WBB")


def sanitize_wind(text: str) -> str:
    """Fix rare wind issues that may be too broad otherwise"""
    for rep in WIND_REMV:
        text = text.replace(rep, "")
    for key, rep in WIND_REPL.items():
        text = text.replace(key, rep)
    if len(text) > 4 and not (text.startswith("VRB") or text[:3].isdigit()):
        # Catches majority of cases where at least two valid letters are found
        if len(set(text[:4]).intersection({"V", "R", "B"})) > 1:
            for i, char in enumerate(text):
                if char.isdigit():
                    text = "VRB" + text[i:]
                    break
        else:
            for key in WIND_VRB:
                if text.startswith(key):
                    zero = "0" if key[-1] == "0" else ""
                    text = text.replace(key, "VRB" + zero)
                    break
    return text


STR_REPL = {
    " C A V O K ": " CAVOK ",
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
    "MISSINGKT": "",
    " 0I0": " 090",
    " PROBB": " PROB",
    " PROBN": " PROB",
    " PROB3P": "PROB30",
    # "Z/ ": "Z ", NOTE: Too broad re pirep
    "NOSIGKT ": "KT NOSIG ",
    "KNOSIGT ": "KT NOSIG ",
    " TMM": " TNM",
    " TMN": " TNM",
    " TXN": " TXM",
    " TNTN": " TN",
    " TXTX": " TX",
    " TXX": " TX",
    "/VRB": " VRB",
    "CALMKT ": "CALM ",
    "CLMKT ": "CALM ",
    "CLRKT ": "CALM ",
    "N0SIG": "NOSIG",
    " <1/": " M1/",  # <1/4SM <1/8SM
    "/04SM": "/4SM",
    "/4SSM": "/4SM",
    "/08SM": "/8SM",
    " /34SM": "3/4SM",
    " 3/SM": " 3/4SM",
    "SCATTERED": "SCT",
    "BROKEN": "BKN",
    "OVERCAST": "OVC",
    "P6000F ": "P6000FT ",
    "P6000FTQ ": "P6000FT ",
}

FINAL_ITEM_STRIP = "./\\"


def separate_cloud_layers(text: str) -> str:
    """Check for missing spaces in front of cloud layers
    Ex: TSFEW004SCT012FEW///CBBKN080
    """
    for cloud in CLOUD_LIST:
        if cloud in text and " " + cloud not in text:
            start, counter = 0, 0
            while text.count(cloud) != text.count(" " + cloud):
                cloud_index = start + text[start:].find(cloud)
                if len(text[cloud_index:]) >= 3:
                    target = text[
                        cloud_index + len(cloud) : cloud_index + len(cloud) + 3
                    ]
                    if target.isdigit() or not target.strip("/"):
                        text = text[:cloud_index] + " " + text[cloud_index:]
                start = cloud_index + len(cloud) + 1
                # Prevent infinite loops
                if counter > text.count(cloud):
                    break
                counter += 1
    return text


def sanitize_report_string(text: str, sans: Sanitization) -> str:
    """Provides sanitization for operations that work better when the report is a string

    Returns the first pass sanitized report string
    """
    text = text.upper().rstrip("=")
    if len(text) < 4:
        return text
    # Standardize whitespace
    text = " ".join(text.split())
    # Prevent changes to station ID
    stid, text = text[:4], text[4:]
    # Replace invalid key-value pairs
    for key, rep in STR_REPL.items():
        if key in text:
            text = text.replace(key, rep)
            sans.log(key, rep)
    separated = separate_cloud_layers(text)
    if text != separated:
        sans.extra_spaces_needed = True
    return stid + separated


def extra_space_exists(str1: str, str2: str) -> bool:
    """Return True if a space shouldn't exist between two items"""
    ls1, ls2 = len(str1), len(str2)
    if str1.isdigit():
        # 10 SM
        if str2 in ["SM", "0SM"]:
            return True
        # 12 /10
        if ls2 > 2 and str2[0] == "/" and str2[1:].isdigit():
            return True
    if str2.isdigit():
        # OVC 040
        if str1 in CLOUD_LIST:
            return True
        # 12/ 10
        if ls1 > 2 and str1.endswith("/") and str1[:-1].isdigit():
            return True
        # 12/1 0
        if (
            ls2 == 1
            and ls1 > 3
            and str1[:2].isdigit()
            and "/" in str1
            and str1[3:].isdigit()
        ):
            return True
        # Q 1001
        if str1 in ["Q", "A"]:
            return True
    # 36010G20 KT
    if (
        str2 == "KT"
        and str1[-1].isdigit()
        and (str1[:5].isdigit() or (str1.startswith("VRB") and str1[3:5].isdigit()))
    ):
        return True
    # 36010K T
    if (
        str2 == "T"
        and ls1 >= 6
        and (str1[:5].isdigit() or (str1.startswith("VRB") and str1[3:5].isdigit()))
        and str1[-1] == "K"
    ):
        return True
    # OVC022 CB
    if (
        str2 in CLOUD_TRANSLATIONS
        and str2 not in CLOUD_LIST
        and ls1 >= 3
        and str1[:3] in CLOUD_LIST
    ):
        return True
    # FM 122400
    if str1 in ["FM", "TL"] and (
        str2.isdigit() or (str2.endswith("Z") and str2[:-1].isdigit())
    ):
        return True
    # TX 20/10
    if str1 in ["TX", "TN"] and str2.find("/") != -1:
        return True
    return False


_CLOUD_GROUP = "(" + "|".join(CLOUD_LIST) + ")"
CLOUD_SPACE_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"(?=.+)" + _CLOUD_GROUP + r"\d{3}(\w{2,3})?$",  # SCT010BKN021
        r"M?\d{2}\/M?\d{2}$",  # BKN01826/25
    )
]
RVR_PATTERN = re.compile(r"R\d{2}[RCL]?/\S+")


def extra_space_needed(item: str) -> Optional[int]:
    """Returns the index where the string should be separated or None"""
    # For items starting with cloud list
    if item[:3] in CLOUD_LIST:
        for pattern in CLOUD_SPACE_PATTERNS:
            match = pattern.search(item)
            if match is None:
                continue
            if match.start():
                return match.start()
    # Connected timestamp
    for loc, check in ((7, is_timestamp), (9, is_timerange)):
        if len(item) > loc and check(item[:loc]):
            return loc
    # Connected to wind
    if len(item) > 5 and "KT" in item and not item.endswith("KT"):
        index = item.find("KT")
        if index > 4:
            return index + 2
    # TAF newline connected to previous element
    for key in TAF_NEWLINE:
        if key in item and not item.startswith(key):
            return item.find(key)
    for key in TAF_NEWLINE_STARTSWITH:
        if key in item and not item.startswith(key):
            index = item.find(key)
            if item[index + len(key) :].isdigit():
                return index
    # Connected TAF min/max temp
    if "TX" in item and "TN" in item and item.endswith("Z") and "/" in item:
        tx_index, tn_index = item.find("TX"), item.find("TN")
        return max(tx_index, tn_index)
    # Connected RVR elements Ex: R36/1500DR18/P2000
    if match := RVR_PATTERN.search(item[1:]):
        return match.start() + 1
    return None


ITEM_REMV = [
    "AUTO",
    "COR",
    "NSC",
    "NCD",
    "$",
    "KT",
    "M",
    ".",
    "RTD",
    "SPECI",
    "METAR",
    "TAF",
    "CORR",
    "TTF",
    "1/SM",
]
ITEM_REPL = {"CALM": "00000KT", "A01": "AO1", "A02": "AO2"}
VIS_PERMUTATIONS = ["".join(p) for p in permutations("P6SM")]
VIS_PERMUTATIONS.remove("6MPS")


def sanitize_report_list(
    wxdata: List[str], sans: Sanitization, remove_clr_and_skc: bool = True
) -> List[str]:
    """Sanitize wxData

    We can remove and identify "one-off" elements and fix other issues before parsing a line
    """
    # pylint: disable=too-many-statements
    for i, item in reversed(list(enumerate(wxdata))):
        ilen = len(item)
        # Remove elements containing only '/'
        if is_unknown(item):
            sans.log(wxdata.pop(i))
            continue
        # Remove empty wind /////KT
        if item.endswith("KT") and is_unknown(item[:-2]):
            sans.log(wxdata.pop(i))
            continue
        # Remove RE from wx codes, REVCTS -> VCTS
        if ilen in [4, 6] and item.startswith("RE"):
            replaced = item[2:]
            wxdata[i] = replaced
            sans.log(item, replaced)
        # Fix a slew of easily identifiable conditions where a space does not belong
        elif i and extra_space_exists(wxdata[i - 1], item):
            wxdata[i - 1] += wxdata.pop(i)
            sans.extra_spaces_found = True
        # Remove spurious elements
        elif item in ITEM_REMV:
            sans.log(wxdata.pop(i))
        # Remove 'Sky Clear' from METAR but not TAF
        elif remove_clr_and_skc and item in ["CLR", "SKC"]:
            sans.log(wxdata.pop(i))
        # Replace certain items
        elif item in ITEM_REPL:
            replaced = ITEM_REPL[item]
            wxdata[i] = replaced
            sans.log(item, replaced)
        # Remove amend signifier from start of report ('CCA', 'CCB',etc)
        elif ilen == 3 and item.startswith("CC") and item[2].isalpha():
            sans.log(wxdata.pop(i))
        # Fix inconsistent 'P6SM' Ex: TP6SM or 6PSM -> P6SM
        elif ilen > 3 and item[-4:] in VIS_PERMUTATIONS:
            wxdata[i] = "P6SM"
            sans.log(item, "P6SM")
        # Fix misplaced KT 22022KTG40
        elif ilen == 10 and "KTG" in item and item[:5].isdigit():
            replaced = item.replace("KTG", "G") + "KT"
            wxdata[i] = replaced
            sans.log(item, replaced)
        # Fix cut-short RVR unit
        elif is_runway_visibility(item) and item.endswith("F"):
            replaced = item + "T"
            wxdata[i] = replaced
            sans.log(item, replaced)
        # Fix malformed KT Ex: 06012G22TK
        if (
            ilen >= 7
            and (item[:3].isdigit() or item[:3] == "VRB")
            and item[-2:] in ("TK", "GT")
        ):
            replaced = item[:-2] + "KT"
            wxdata[i] = replaced
            sans.log(item, replaced)
        # Fix gust double G Ex: 360G17G32KT
        elif ilen > 10 and item.endswith("KT") and item[3] == "G":
            replaced = item[:3] + item[4:]
            wxdata[i] = replaced
            sans.log(item, replaced)
        # Fix leading character mistypes in wind
        elif (
            ilen > 7
            and not item[0].isdigit()
            and not item.startswith("VRB")
            and item.endswith("KT")
            and not item.startswith("WS")
        ):
            while item and not item[0].isdigit() and not item.startswith("VRB"):
                item = item[1:]
            sans.log(wxdata[i], item)
            wxdata[i] = item
        # Fix non-G gust Ex: 14010-15KT
        elif ilen == 10 and item.endswith("KT") and item[5] != "G":
            replaced = item[:5] + "G" + item[6:]
            wxdata[i] = replaced
            sans.log(item, replaced)
        # Fix leading digits on VRB wind Ex: 2VRB02KT
        elif (
            ilen > 7
            and item.endswith("KT")
            and "VRB" in item
            and item[0].isdigit()
            and "Z" not in item
        ):
            while item[0].isdigit():
                item = item[1:]
            sans.log(wxdata[i], item)
            wxdata[i] = item
        # Fix wind T
        elif not item.endswith("KT") and (
            (
                ilen == 6
                and item[5] in ["K", "T"]
                and (
                    item[:5].isdigit()
                    or (item.startswith("VRB") and item[:3].isdigit())
                )
            )
            or (
                ilen == 9
                and item[8] in ["K", "T"]
                and item[5] == "G"
                and (item[:5].isdigit() or item.startswith("VRB"))
            )
        ):
            replaced = item[:-1] + "KT"
            wxdata[i] = replaced
            sans.log(item, replaced)
        # Fix situations where a space is missing
        index = extra_space_needed(item)
        if index:
            wxdata.insert(i + 1, item[index:])
            wxdata[i] = item[:index]
            sans.extra_spaces_needed = True
    # Check for wind sanitization
    for i, item in enumerate(wxdata):
        if is_variable_wind_direction(item):
            replaced = item[:7]
            wxdata[i] = replaced
            sans.log(item, replaced)
            continue
        possible_wind = sanitize_wind(item)
        if is_wind(possible_wind):
            if item != possible_wind:
                sans.log(item, possible_wind)
            wxdata[i] = possible_wind
    # Strip extra characters before dedupe
    stripped = [i.strip(FINAL_ITEM_STRIP) for i in wxdata]
    if wxdata != stripped:
        sans.log_list(wxdata, stripped)
    deduped = dedupe(stripped, only_neighbors=True)
    if len(deduped) != len(wxdata):
        sans.duplicates_found = True
    return deduped
