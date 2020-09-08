"""
Contains report sanitization functions
"""

# stdlib
import re
from itertools import permutations
from typing import List

# module
from avwx.parsing.core import dedupe, is_timerange, is_timestamp, is_unknown
from avwx.static.core import CLOUD_LIST, CLOUD_TRANSLATIONS
from avwx.static.taf import TAF_NEWLINE, TAF_NEWLINE_STARTSWITH

STR_REPL = {
    " C A V O K ": " CAVOK ",
    "?": " ",
    '"': "",
    "'": "",
    "`": "",
    ".": "",
    " VTB": " VRB",
    " VBR": " VRB",
    " VBB": " VRB",
    " ERB": " VRB",
    " VRV": " VRB",
    " BRV": " VRB",
    " VRN": " VRB",
    " BRB": " VRB",
    " VEB": " VRB",
    " VFB": " VRB",
    " VAB": " VRB",
    " VAR": " VRB",
    " VRG": " VRB",
    " VRR": " VRB",
    " VGB": " VRB",
    " VRC": " VRB",
    " WBB": " VRB",
    " VR0": " VRB0",
    " VB0": " VRB0",
    " RB0": " VRB0",
    " V0": " VRB0",
    " 0I0": " 090",
    " PROBB": " PROB",
    # "Z/ ": "Z ", NOTE: Too broad re pirep
    "KKT ": "KT ",
    "KLT ": "KT ",
    "TKT ": "KT ",
    " TMM": " TNM",
    "CALMKT ": "CALM ",
    "N0SIG": "NOSIG",
    " <1/": " M1/",  # <1/4SM <1/8SM
    " /34SM": "3/4SM",
}


def sanitize_report_string(txt: str) -> str:
    """
    Provides sanitization for operations that work better when the report is a string

    Returns the first pass sanitized report string
    """
    txt = txt.upper()
    if len(txt) < 4:
        return txt
    # Standardize whitespace
    txt = " ".join(txt.split())
    # Prevent changes to station ID
    stid, txt = txt[:4], txt[4:]
    # Replace invalid key-value pairs
    for key, rep in STR_REPL.items():
        txt = txt.replace(key, rep)
    # Check for missing spaces in front of cloud layers
    # Ex: TSFEW004SCT012FEW///CBBKN080
    for cloud in CLOUD_LIST:
        if cloud in txt and " " + cloud not in txt:
            start, counter = 0, 0
            while txt.count(cloud) != txt.count(" " + cloud):
                cloud_index = start + txt[start:].find(cloud)
                if len(txt[cloud_index:]) >= 3:
                    target = txt[
                        cloud_index + len(cloud) : cloud_index + len(cloud) + 3
                    ]
                    if target.isdigit() or not target.strip("/"):
                        txt = txt[:cloud_index] + " " + txt[cloud_index:]
                start = cloud_index + len(cloud) + 1
                # Prevent infinite loops
                if counter > txt.count(cloud):
                    break
                counter += 1
    return stid + txt


def extra_space_exists(str1: str, str2: str) -> bool:
    """
    Return True if a space shouldn't exist between two items
    """
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


def extra_space_needed(item: str) -> int:
    """
    Returns the index where the string should be separated or None
    """
    # For items starting with cloud list
    if item[:3] in CLOUD_LIST:
        for pattern in CLOUD_SPACE_PATTERNS:
            sep = pattern.search(item)
            if sep is None:
                continue
            if sep.start():
                return sep.start()
    # Connected timestamp
    for loc, check in ((7, is_timestamp), (9, is_timerange)):
        if len(item) > loc and check(item[:loc]):
            return loc
    # Connected to wind
    if len(item) > 5 and "KT" in item and not item.endswith("KT"):
        sep = item.find("KT")
        if sep > 4:
            return sep + 2
    # TAF newline connected to previous element
    for key in TAF_NEWLINE:
        if key in item and not item.startswith(key):
            return item.find(key)
    for key in TAF_NEWLINE_STARTSWITH:
        if key in item and not item.startswith(key):
            sep = item.find(key)
            if item[sep + len(key) :].isdigit():
                return sep
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
    "CORR",
    "TTF",
]
ITEM_REPL = {"CALM": "00000KT"}
VIS_PERMUTATIONS = ["".join(p) for p in permutations("P6SM")]
VIS_PERMUTATIONS.remove("6MPS")


def sanitize_report_list(
    wxdata: List[str], remove_clr_and_skc: bool = True
) -> List[str]:
    """
    Sanitize wxData

    We can remove and identify "one-off" elements and fix other issues before parsing a line
    """
    for i, item in reversed(list(enumerate(wxdata))):
        ilen = len(item)
        # Remove elements containing only '/'
        if is_unknown(item):
            wxdata.pop(i)
            continue
        # Remove empty wind /////KT
        if item.endswith("KT") and is_unknown(item[:-2]):
            wxdata.pop(i)
            continue
        # Remove RE from wx codes, REVCTS -> VCTS
        if ilen in [4, 6] and item.startswith("RE"):
            wxdata[i] = item[2:]
        # Fix a slew of easily identifiable conditions where a space does not belong
        elif i and extra_space_exists(wxdata[i - 1], item):
            wxdata[i - 1] += wxdata.pop(i)
        # Remove spurious elements
        elif item in ITEM_REMV:
            wxdata.pop(i)
        # Remove 'Sky Clear' from METAR but not TAF
        elif remove_clr_and_skc and item in ["CLR", "SKC"]:
            wxdata.pop(i)
        # Replace certain items
        elif item in ITEM_REPL:
            wxdata[i] = ITEM_REPL[item]
        # Remove amend signifier from start of report ('CCA', 'CCB',etc)
        elif ilen == 3 and item.startswith("CC") and item[2].isalpha():
            wxdata.pop(i)
        # Fix inconsistent 'P6SM' Ex: TP6SM or 6PSM -> P6SM
        elif ilen > 3 and item[-4:] in VIS_PERMUTATIONS:
            wxdata[i] = "P6SM"
        # Fix misplaced KT 22022KTG40
        elif ilen == 10 and "KTG" in item and item[:5].isdigit():
            wxdata[i] = item.replace("KTG", "G") + "KT"
        # Fix backwards KT Ex: 06012G22TK
        if (
            ilen >= 7
            and (item[:3].isdigit() or item[:3] == "VRB")
            and item.endswith("TK")
        ):
            wxdata[i] = item[:-2] + "KT"
        # Fix gust double G Ex: 360G17G32KT
        elif ilen > 10 and item.endswith("KT") and item[3] == "G":
            wxdata[i] = item[:3] + item[4:]
        # Fix leading character mistypes in wind
        elif (
            ilen > 7
            and not item[0].isdigit()
            and not item.startswith("VRB")
            and item.endswith("KT")
            and not item.startswith("WS")
        ):
            while not item[0].isdigit() and not item.startswith("VRB"):
                item = item[1:]
            wxdata[i] = item
        # Fix non-G gust Ex: 14010-15KT
        elif ilen == 10 and item.endswith("KT") and item[5] != "G":
            wxdata[i] = item[:5] + "G" + item[6:]
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
            wxdata[i] = item[:-1] + "KT"
        # Fix joined TX-TN
        elif ilen > 16 and len(item.split("/")) == 3:
            if item.startswith("TX") and "TN" not in item:
                tn_index = item.find("TN")
                wxdata.insert(i + 1, item[:tn_index])
                wxdata[i] = item[tn_index:]
            elif item.startswith("TN") and item.find("TX") != -1:
                tx_index = item.find("TX")
                wxdata.insert(i + 1, item[:tx_index])
                wxdata[i] = item[tx_index:]
        # Fix situations where a space is missing
        sep = extra_space_needed(item)
        if sep:
            wxdata.insert(i + 1, item[sep:])
            wxdata[i] = item[:sep]
    wxdata = dedupe(wxdata, only_neighbors=True)
    return wxdata
