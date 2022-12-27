"""
Report Sanitization Tests
"""

# stdlib
import json
from pathlib import Path

# module
from avwx.parsing import sanitization
from avwx.structs import Sanitization

from tests.util import BaseTest

DATA_PATH = Path(__file__).parent / "data"


class TestSanitization(BaseTest):
    """Test report sanitization functions"""

    def test_extra_space_exists(self):
        """Tests whether a space should exist between two elements"""
        for strings in (
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
        ):
            self.assertTrue(sanitization.extra_space_exists(*strings))
        for strings in (
            ("OVC020", "FEW"),
            ("BKN020", "SCT040"),
            ("Q", "12/34"),
            ("OVC", "12/34"),
        ):
            self.assertFalse(sanitization.extra_space_exists(*strings))

    def test_extra_space_needed(self):
        """Tests if two elements should be split and where"""
        for item, sep in (
            ("21016G28KTPROB40", 10),
            ("VCSHINTER", 4),
            ("151200Z18002KT", 7),
            ("2301/2303VRB02KT", 9),
            ("33015G25KT4500", 10),
            ("211600ZVRB04KT", 7),
            ("PROB30", None),
            ("A2992", None),
            ("TX32/2521ZTN24/2512Z", 10),
            ("TN24/2512ZTX32/2521Z", 10),
        ):
            self.assertEqual(sanitization.extra_space_needed(item), sep)

    def test_sanitize_report_string(self):
        """Tests a function which fixes common mistakes while the report is a string"""
        line = "KJFK 36010 ? TSFEW004SCT012FEW///CBBKN080 C A V O K A2992"
        fixed = "KJFK 36010   TS FEW004 SCT012 FEW///CB BKN080 CAVOK A2992"
        sans = Sanitization()
        self.assertEqual(sanitization.sanitize_report_string(line, sans), fixed)
        self.assertTrue(sans.errors_found)
        self.assertTrue(sans.extra_spaces_needed)
        self.assertFalse(sans.duplicates_found)
        self.assertFalse(sans.extra_spaces_found)
        self.assertEqual(sans.removed, ["?"])
        self.assertEqual(sans.replaced, {"C A V O K": "CAVOK"})

    def test_sanitize_report_list(self):
        """Tests a function which fixes common mistakes while the report is a list"""
        case_path = DATA_PATH / "sanitize_report_list_cases.json"
        for case in json.load(case_path.open()):
            line, fixed = case["report"].split(), case["fixed"].split()
            sans = Sanitization()
            data = sanitization.sanitize_report_list(line, sans)
            self.assertEqual(data, fixed)
            self.assertTrue(sans.errors_found)
            self.assertEqual(sans.removed, case["removed"])
            self.assertEqual(sans.replaced, case["replaced"])
            self.assertEqual(sans.duplicates_found, case["duplicates"])
            self.assertEqual(sans.extra_spaces_found, case["extra_spaces_found"])
            self.assertEqual(sans.extra_spaces_needed, case["extra_spaces_needed"])
