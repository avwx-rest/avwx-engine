"""
Report Sanitization Tests
"""

# module
from avwx.parsing import sanitization

from tests.util import BaseTest


class TestSanitization(BaseTest):
    """
    Test report sanitization functions
    """

    def test_extra_space_exists(self):
        """
        Tests whether a space should exist between two elements
        """
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
        """
        Tests if two elements should be split and where
        """
        for item, sep in (
            ("21016G28KTPROB40", 10),
            ("VCSHINTER", 4),
            ("151200Z18002KT", 7),
            ("2301/2303VRB02KT", 9),
            ("33015G25KT4500", 10),
            ("211600ZVRB04KT", 7),
            ("PROB30", None),
            ("A2992", None),
        ):
            self.assertEqual(sanitization.extra_space_needed(item), sep)

    def test_sanitize_report_string(self):
        """
        Tests a function which fixes common mistakes while the report is a string
        """
        line = "KJFK 36010 ? TSFEW004SCT012FEW///CBBKN080 C A V O K A2992"
        fixed = "KJFK 36010   TS FEW004 SCT012 FEW///CB BKN080 CAVOK A2992"
        self.assertEqual(sanitization.sanitize_report_string(line), fixed)

    def test_sanitize_report_list(self):
        """
        Tests a function which fixes common mistakes while the report is a list
        """
        for line, fixed in (
            ("KJFK AUTO 123456Z ////// KT 10SM 20/10", "KJFK 123456Z 10SM 20/10"),
            ("METAR EGLL CALM RETS 6SPM CLR Q 1000", "EGLL 00000KT TS P6SM Q1000"),
            ("TLPL 111200Z 111200Z11020KT Q1015", "TLPL 111200Z 11020KT Q1015"),
            ("SECU 151200Z 151200Z18002KT Q1027", "SECU 151200Z 18002KT Q1027"),
            ("OAKB 211230Z 360G17G32KT Q1011", "OAKB 211230Z 36017G32KT Q1011"),
            ("MHLC 090024Z 06012G22TK 5000", "MHLC 090024Z 06012G22KT 5000"),
            ("SKCL 211600Z 211600ZVRB04KT A3010", "SKCL 211600Z VRB04KT A3010"),
            (
                "SVMG 072200Z //////KT 9999 FEW010 XX/XX Q1012",
                "SVMG 072200Z 9999 FEW010 Q1012",
            ),
            ("KJFK 1 1 1 1 1 1 2 1", "KJFK 1 2 1"),
        ):
            line, fixed = line.split(), fixed.split()
            self.assertEqual(sanitization.sanitize_report_list(line), fixed)
