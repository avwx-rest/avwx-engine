"""
Report Sanitization Tests
"""

# stdlib
import json
from pathlib import Path
from typing import List, Optional

# library
import pytest

# module
from avwx.parsing import sanitization
from avwx.structs import Sanitization

DATA_PATH = Path(__file__).parent / "data"
CASE_DATA = DATA_PATH / "sanitize_report_list_cases.json"


@pytest.mark.parametrize(
    "strings",
    (
        ("10", "SM"),
        ("1", "0SM"),
        ("12", "/10"),
        ("12/", "10"),
        ("12/1", "0"),
        ("OVC", "040"),
        ("Q", "1001"),
        ("A", "2992"),
        ("36010G20", "KT"),
        ("VRB10", "KT"),
        ("36010G20K", "T"),
        ("VRB10K", "T"),
        ("OVC022", "CB"),
        ("FM", "122400"),
        ("TL", "123456Z"),
        ("TX", "10/20"),
        ("TN", "05/10"),
    ),
)
def test_extra_space_exists(strings: List[str]):
    """Tests whether a space should exist between two elements"""
    assert sanitization.extra_space_exists(*strings) is True


@pytest.mark.parametrize(
    "strings",
    (
        ("OVC020", "FEW"),
        ("BKN020", "SCT040"),
        ("Q", "12/34"),
        ("OVC", "12/34"),
    ),
)
def test_extra_space_does_not_exist(strings: List[str]):
    assert sanitization.extra_space_exists(*strings) is False


@pytest.mark.parametrize(
    "item,sep",
    (
        ("21016G28KTPROB40", 10),
        ("VCSHINTER", 4),
        ("151200Z18002KT", 7),
        ("2301/2303VRB02KT", 9),
        ("2902/2904VRB03KT", 9),
        ("33015G25KT4500", 10),
        ("211600ZVRB04KT", 7),
        ("PROB30", None),
        ("A2992", None),
        ("TX32/2521ZTN24/2512Z", 10),
        ("TN24/2512ZTX32/2521Z", 10),
    ),
)
def test_extra_space_needed(item: str, sep: Optional[int]):
    """Tests if two elements should be split and where"""
    assert sanitization.extra_space_needed(item) == sep


def test_sanitize_report_string():
    """Tests a function which fixes common mistakes while the report is a string"""
    line = "KJFK 36010 ? TSFEW004SCT012FEW///CBBKN080 R02L/4000VP6000F C A V O K A2992"
    fixed = (
        "KJFK 36010   TS FEW004 SCT012 FEW///CB BKN080 R02L/4000VP6000FT CAVOK A2992"
    )
    sans = Sanitization()
    assert sanitization.sanitize_report_string(line, sans) == fixed
    assert sans.errors_found is True
    assert sans.extra_spaces_needed is True
    assert sans.duplicates_found is False
    assert sans.extra_spaces_found is False
    assert sans.removed == ["?"]
    assert sans.replaced == {"C A V O K": "CAVOK", "P6000F": "P6000FT"}


@pytest.mark.parametrize("case", json.load(CASE_DATA.open()))
def test_sanitize_report_list(case: dict):
    """Tests a function which fixes common mistakes while the report is a list"""
    line, fixed = case["report"].split(), case["fixed"].split()
    sans = Sanitization()
    data = sanitization.sanitize_report_list(line, sans)
    assert data == fixed
    assert sans.errors_found is True
    assert sans.removed == case["removed"]
    assert sans.replaced == case["replaced"]
    assert sans.duplicates_found == case["duplicates"]
    assert sans.extra_spaces_found == case["extra_spaces_found"]
    assert sans.extra_spaces_needed == case["extra_spaces_needed"]
