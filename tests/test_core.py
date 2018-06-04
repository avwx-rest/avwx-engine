"""
Michael duPont - michael@mdupont.com
tests/test_core.py
"""

# pylint: disable=E1101,C0103

# library
import unittest
# module
from avwx import core, exceptions, static

class TestGlobal(unittest.TestCase):

    def test_valid_station(self):
        """
        While not designed to catch all non-existant station idents,
        valid_station should catch non-ICAO strings and filter based on known prefixes
        """
        # Good stations
        for station in ('KJFK', 'K123', 'EIGL', 'PHNL', 'MNAH'):
            core.valid_station(station)
        # Bad stations
        for station in ('12K', 'MAYT'):
            with self.assertRaises(exceptions.BadStation):
                core.valid_station(station)

    def test_uses_na_format(self):
        """
        METAR and TAF reports come in two flavors: North American and International
        
        uses_na_format should determine the format based on the station ident using prefixes
        """
        # NA stations
        for station in ('KJFK', 'PHNL', 'TNCM', 'MYNN'):
            self.assertTrue(core.uses_na_format(station))
        # IN stations
        for station in ('EGLL', 'MNAH', 'MUHA'):
            self.assertFalse(core.uses_na_format(station))
        # Bad stations
        for station in ('12K', 'MAYT'):
            with self.assertRaises(exceptions.BadStation):
                core.uses_na_format(station)

    def test_is_unknown(self):
        """
        Tests unknown value when a string value contains only backspace characters or empty
        """
        # Unknown values
        for i in range(10):
            self.assertTrue(core.is_unknown('/' * i))
        # Full or partially known values
        for value in ('abc', '/bc', 'a/c', 'ab/', 'a//', '/b/', '//c'):
            self.assertFalse(core.is_unknown(value))
        # Bad type
        with self.assertRaises(TypeError):
            core.is_unknown(None)

    def test_find_first_in_list(self):
        """
        Tests a function which finds the first occurence in a string from a list

        This is used to find remarks and TAF time periods
        """
        for string, targets, index in (
            ('012345', ('5', '2', '3'), 2),
            ('This is weird', ('me', 'you', 'we'), 8),
            ('KJFK NOPE LOL RMK HAHAHA', static.METAR_RMK, 13)
        ):
            self.assertEquals(core.find_first_in_list(string, targets), index)

    def test_extra_space_exists(self):
        """
        """
        for strings in (
            ('10', 'SM'),
            ('1', '0SM'),
            ('12', '/10'),
            ('12/', '10'),
            ('12/1', '0'),
            ('OVC', '040'),
            ('Q', '1001'),
            ('A', '2992'),
            ('36010G20', 'KT'),
            ('VRB10', 'KT'),
            ('36010G20K', 'T'),
            ('VRB10K', 'T'),
            ('OVC022', 'CB'),
            ('FM', '122400'),
            ('TL', '123456Z'),
            ('TX', '10/20'),
            ('TN', '05/10')
        ):
            self.assertTrue(core.extra_space_exists(*strings))
        for strings in (
            ('OVC020', 'FEW'),
            ('BKN020', 'SCT040'),
            ('Q', '12/34'),
            ('OVC', '12/34'),
        ):
            self.assertFalse(core.extra_space_exists(*strings))

class TestMetar(unittest.TestCase):

    def test_get_remarks(self):
        """
        Remarks get removed first with the remaining components split into a list
        """
        for raw, wx, rmk in (
            ('1 2 3 A2992 RMK Hi', ['1', '2', '3', 'A2992'], 'RMK Hi'),
            ('1 2 3 A2992 Hi', ['1', '2', '3', 'A2992'], 'Hi'),
            ('1 2 Q0900 NOSIG', ['1', '2', 'Q0900'], 'NOSIG'),
            ('1 2 3 BLU+ Hello', ['1', '2', '3'], 'BLU+ Hello')
        ):
            testwx, testrmk = core.get_remarks(raw)
            self.assertEqual(wx, testwx)
            self.assertEqual(rmk, testrmk)

    def test_sanitize_report_string(self):
        """
        """
        pass

class TestTaf(unittest.TestCase):

    def test_sanitize_line(self):
        """
        """
        pass