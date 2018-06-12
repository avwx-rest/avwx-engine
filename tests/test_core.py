"""
Michael duPont - michael@mdupont.com
tests/test_core.py
"""

# pylint: disable=E1101,C0103

# library
import unittest
# module
from avwx import core, exceptions, static, structs

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
        Tests whether a space should exist between two elements
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

    def test_sanitize_report_list(self):
        """
        Tests a function which fixes common mistakes while the report is a list
        """
        for line, fixed in (
            ('KJFK AUTO 123456Z ////// KT 10SM 20/10', 'KJFK 123456Z 10SM 20/10'),
            ('METAR EGLL CALM RETS 6SPM CLR Q 1000', 'EGLL 00000KT TS P6SM Q1000'),
        ):
            line, fixed = line.split(), fixed.split()
            self.assertEqual(core.sanitize_report_list(line), (fixed, [], ''))
        # Test extracting runway visibility and wind shear
        line = 'EGLL 12345 KT R10/10 RETS WS100/20KT 6SPM'.split()
        fixed = 'EGLL 12345KT TS P6SM'.split()
        self.assertEqual(core.sanitize_report_list(line), (fixed, ['R10/10'], 'WS100/20'))

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
        Tests a function which fixes common mistakes while the report is a string
        """
        line = 'KJFK 36010 ? TSFEW004SCT012FEW///CBBKN080 C A V O K A2992'
        fixed = 'KJFK 36010   TS FEW004 SCT012 FEW///CB BKN080 CAVOK A2992'
        self.assertEqual(core.sanitize_report_string(line), fixed)

    def test_get_altimeter(self):
        """
        Tests that the correct alimeter item gets removed from the end of the wx list
        """
        # North American default
        units = structs.Units(**static.NA_UNITS)
        for wx, altim,  in (
            (['1', '2'], ''),
            (['1', '2', 'A2992'], '2992'),
            (['1', '2', '2992'], '2992'),
            (['1', '2', 'A2992', 'Q1000'], '2992'),
            (['1', '2', 'Q1000', 'A2992'], '2992'),
            (['1', '2', 'Q1000'], '1000')
        ):
            self.assertEqual(units.altimeter, 'inHg')
            self.assertEqual(core.get_altimeter(wx, units), (['1', '2'], altim))
        # The last one should have changed the unit
        self.assertEqual(units.altimeter, 'hPa')
        # International
        units = structs.Units(**static.IN_UNITS)
        for wx, altim,  in (
            (['1', '2'], ''),
            (['1', '2', 'Q.1000'], '1000'),
            (['1', '2', 'Q1000/10'], '1000'),
            (['1', '2', 'A2992', 'Q1000'], '1000'),
            (['1', '2', 'Q1000', 'A2992'], '1000'),
            (['1', '2', 'A2992'], '2992')
        ):
            self.assertEqual(units.altimeter, 'hPa')
            self.assertEqual(core.get_altimeter(wx, units, 'IN'), (['1', '2'], altim))
        # The last one should have changed the unit
        self.assertEqual(units.altimeter, 'inHg')

class TestTaf(unittest.TestCase):

    def test_sanitize_line(self):
        """
        Tests a function which fixes common new-line signifiers in TAF reports
        """
        for line in ('1 BEC 1', '1 BE CMG1', '1 BEMG 1'):
            self.assertEqual(core.sanitize_line(line), '1 BECMG 1')
        for line in ('1 TEMP0 1', '1 TEMP 1', '1 TEMO1', '1 T EMPO1'):
            self.assertEqual(core.sanitize_line(line), '1 TEMPO 1')
        self.assertEqual(core.sanitize_line('1 2 3 4 5'), '1 2 3 4 5')

    def test_is_not_tempo_or_prob(self):
        """
        Tests a function which checks that an item signifies a new time period
        """
        for rtype in ('1', 'TEMPORARY', 'TEMP0', 'PROBABLY', 'PROB'):
            self.assertTrue(core.is_not_tempo_or_prob(rtype))
        for rtype in ('TEMPO', 'PROB30', 'PROBNA'):
            self.assertFalse(core.is_not_tempo_or_prob(rtype))
