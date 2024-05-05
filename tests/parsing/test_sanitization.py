"""
Report Sanitization Tests
"""

# stdlib
import json
from pathlib import Path
from typing import Callable

# library
import pytest

# module
from avwx.parsing.sanitization.metar import clean_metar_list, clean_metar_string
from avwx.parsing.sanitization.taf import clean_taf_list
from avwx.structs import Sanitization

DATA_PATH = Path(__file__).parent / "data"
METAR_CASES = DATA_PATH / "sanitize_metar_list_cases.json"
TAF_CASES = DATA_PATH / "sanitize_taf_list_cases.json"


def test_sanitize_report_string():
    """Tests a function which fixes common mistakes while the report is a string"""
    line = "KJFK 36010 ? TSFEW004SCT012FEW///CBBKN080 R02L/4000VP6000F C A V O K A2992"
    fixed = (
        "KJFK 36010   TS FEW004 SCT012 FEW///CB BKN080 R02L/4000VP6000FT CAVOK A2992"
    )
    sans = Sanitization()
    assert clean_metar_string(line, sans) == fixed
    assert sans.errors_found is True
    assert sans.extra_spaces_needed is True
    assert sans.duplicates_found is False
    assert sans.extra_spaces_found is False
    assert sans.removed == ["?"]
    assert sans.replaced == {"C A V O K": "CAVOK", "P6000F": "P6000FT"}


def test_sanitize_empty_report_string():
    """Tests that the sanitization minimaly affects short text"""
    assert clean_metar_string("  MVP=", Sanitization()) == "MVP"


def _test_list_sanitizer(cleaner: Callable, case: dict):
    """Tests a function which fixes common mistakes while the report is a list"""
    line, fixed = case["report"].split(), case["fixed"].split()
    sans = Sanitization()
    data = cleaner(line, sans)
    assert data == fixed
    assert sans.errors_found is True
    assert sans.removed == case["removed"]
    assert sans.replaced == case["replaced"]
    assert sans.duplicates_found == case["duplicates"]
    assert sans.extra_spaces_found == case["extra_spaces_found"]
    assert sans.extra_spaces_needed == case["extra_spaces_needed"]


@pytest.mark.parametrize("case", json.load(METAR_CASES.open()))
def test_clean_metar_list(case: dict):
    _test_list_sanitizer(clean_metar_list, case)


@pytest.mark.parametrize("case", json.load(TAF_CASES.open()))
def test_clean_taf_list(case: dict):
    _test_list_sanitizer(clean_taf_list, case)
