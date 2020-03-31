"""
Core Tests
"""

# pylint: disable=E1101,C0103

# stdlib
import unittest

# stdlib
from datetime import datetime, timezone

# module
from avwx import static, structs
from avwx.parsing import core

from tests.util import BaseTest


class TestGlobal(BaseTest):
    def test_dedupe(self):
        """
        Tests list deduplication
        """
        for before, after in (
            ([1, 2, 3, 2, 1], [1, 2, 3]),
            ([4, 4, 4, 4], [4]),
            ([1, 5, 1, 1, 3, 5], [1, 5, 3]),
        ):
            self.assertEqual(core.dedupe(before), after)
        for before, after in (
            ([1, 2, 3, 2, 1], [1, 2, 3, 2, 1]),
            ([4, 4, 4, 4], [4]),
            ([1, 5, 1, 1, 3, 5], [1, 5, 1, 3, 5]),
        ):
            self.assertEqual(core.dedupe(before, only_neighbors=True), after)

    def test_is_unknown(self):
        """
        Tests unknown value when a string value contains only backspace characters or empty
        """
        # Unknown values
        for i in range(10):
            self.assertTrue(core.is_unknown("/" * i))
        # Full or partially known values
        for value in ("abc", "/bc", "a/c", "ab/", "a//", "/b/", "//c"):
            self.assertFalse(core.is_unknown(value))
        # Bad type
        with self.assertRaises(TypeError):
            core.is_unknown(None)

    def test_is_timestamp(self):
        """
        Tests determining if a string is a timestamp element
        """
        for ts in ("123456Z", "987654Z"):
            self.assertTrue(core.is_timestamp(ts))
        for nts in ("", "123456Z123", "1234", "1234Z"):
            self.assertFalse(core.is_timestamp(nts))

    def test_unpack_fraction(self):
        """
        Tests unpacking a fraction where the numerator can be greater than the denominator
        """
        for fraction, unpacked in (
            ("", ""),
            ("1", "1"),
            ("1/2", "1/2"),
            ("3/2", "1 1/2"),
            ("10/3", "3 1/3"),
        ):
            self.assertEqual(core.unpack_fraction(fraction), unpacked)

    def test_remove_leading_zeros(self):
        """
        Tests removing leading zeros from a number
        """
        for num, stripped in (
            ("", ""),
            ("5", "5"),
            ("010", "10"),
            ("M10", "M10"),
            ("M002", "M2"),
            ("-09.9", "-9.9"),
            ("000", "0"),
            ("M00", "0"),
        ):
            self.assertEqual(core.remove_leading_zeros(num), stripped)

    def test_spoken_number(self):
        """
        Tests converting digits into spoken values
        """
        for num, spoken in (
            ("1", "one"),
            ("5", "five"),
            ("20", "two zero"),
            ("937", "nine three seven"),
            ("4.8", "four point eight"),
            ("29.92", "two nine point nine two"),
            ("1/2", "one half"),
            ("3 3/4", "three and three quarters"),
        ):
            self.assertEqual(core.spoken_number(num), spoken)

    def test_make_number(self):
        """
        Tests Number dataclass generation from a number string
        """
        self.assertIsNone(core.make_number(""))
        for num, value, spoken in (
            ("1", 1, "one"),
            ("1.5", 1.5, "one point five"),
            ("060", 60, "six zero"),
            ("M10", -10, "minus one zero"),
            ("P6SM", None, "greater than six"),
            ("M1/4", None, "less than one quarter"),
        ):
            number = core.make_number(num)
            self.assertEqual(number.repr, num)
            self.assertEqual(number.value, value)
            self.assertEqual(number.spoken, spoken)
        for num, value, spoken, nmr, dnm, norm in (
            ("1/4", 0.25, "one quarter", 1, 4, "1/4"),
            ("5/2", 2.5, "two and one half", 5, 2, "2 1/2"),
            ("3/4", 0.75, "three quarters", 3, 4, "3/4"),
            ("5/4", 1.25, "one and one quarter", 5, 4, "1 1/4"),
            ("11/4", 1.25, "one and one quarter", 5, 4, "1 1/4"),
        ):
            number = core.make_number(num)
            self.assertEqual(number.value, value)
            self.assertEqual(number.spoken, spoken)
            self.assertEqual(number.numerator, nmr)
            self.assertEqual(number.denominator, dnm)
            self.assertEqual(number.normalized, norm)
        self.assertEqual(core.make_number("1234", "A1234").repr, "A1234")
        number = core.make_number("040", speak="040")
        self.assertEqual(number.value, 40)
        self.assertEqual(number.spoken, "zero four zero")

    def test_find_first_in_list(self):
        """
        Tests a function which finds the first occurrence in a string from a list

        This is used to find remarks and TAF time periods
        """
        for string, targets, index in (
            ("012345", ("5", "2", "3"), 2),
            ("This is weird", ("me", "you", "we"), 8),
            ("KJFK NOPE LOL RMK HAHAHA", static.metar.METAR_RMK, 13),
        ):
            self.assertEqual(core.find_first_in_list(string, targets), index)

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
            self.assertTrue(core.extra_space_exists(*strings))
        for strings in (
            ("OVC020", "FEW"),
            ("BKN020", "SCT040"),
            ("Q", "12/34"),
            ("OVC", "12/34"),
        ):
            self.assertFalse(core.extra_space_exists(*strings))

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
            self.assertEqual(core.extra_space_needed(item), sep)

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
            self.assertEqual(core.sanitize_report_list(line), fixed)

    def test_is_possible_temp(self):
        """
        Tests if an element could be a formatted temperature
        """
        for is_temp in ("10", "22", "333", "M05", "5"):
            self.assertTrue(core.is_possible_temp(is_temp))
        for not_temp in ("A", "12.3", "MNA", "-13"):
            self.assertFalse(core.is_possible_temp(not_temp))

    def test_get_station_and_time(self):
        """
        Tests removal of station (first item) and potential timestamp
        """
        for wx, ret, station, time in (
            (["KJFK", "123456Z", "1"], ["1"], "KJFK", "123456Z"),
            (["KJFK", "123456", "1"], ["1"], "KJFK", "123456Z"),
            (["KJFK", "1234Z", "1"], ["1"], "KJFK", "1234Z"),
            (["KJFK", "1234", "1"], ["1234", "1"], "KJFK", None),
            (["KJFK", "1"], ["1"], "KJFK", None),
            (["KJFK"], [], "KJFK", None),
        ):
            self.assertEqual(core.get_station_and_time(wx), (ret, station, time))

    def test_get_wind(self):
        """
        Tests that the wind item gets removed and split into its components
        """
        # Both us knots as the default unit, so just test North American default
        for wx, unit, *wind, varv in (
            (["1"], "kt", (None,), (None,), (None,), []),
            (["12345(E)", "G50", "1"], "kt", ("123", 123), ("45", 45), ("50", 50), []),
            (["O1234G56", "1"], "kt", ("012", 12), ("34", 34), ("56", 56), []),
            (
                ["36010KTS", "G20", "300V060", "1"],
                "kt",
                ("360", 360),
                ("10", 10),
                ("20", 20),
                [("300", 300), ("060", 60)],
            ),
            (["VRB10MPS", "1"], "m/s", ("VRB",), ("10", 10), (None,), []),
            (["VRB20G30KMH", "1"], "km/h", ("VRB",), ("20", 20), ("30", 30), []),
        ):
            units = structs.Units(**static.core.NA_UNITS)
            wx, *winds, var = core.get_wind(wx, units)
            self.assertEqual(wx, ["1"])
            for i in range(len(wind)):
                self.assert_number(winds[i], *wind[i])
            if varv:
                self.assertIsInstance(varv, list)
                for i in range(2):
                    self.assert_number(var[i], *varv[i])
            self.assertEqual(units.wind_speed, unit)

    def test_get_visibility(self):
        """
        Tests that the visibility item(s) gets removed and cleaned
        """
        for wx, unit, visibility in (
            (["1"], "sm", (None,)),
            (["05SM", "1"], "sm", ("5", 5)),
            (["10SM", "1"], "sm", ("10", 10)),
            (["P6SM", "1"], "sm", ("P6",)),
            (["M1/4SM", "1"], "sm", ("M1/4",)),
            (["1/2SM", "1"], "sm", ("1/2", 0.5)),
            (["2", "1/2SM", "1"], "sm", ("5/2", 2.5)),
            (["1000", "1"], "m", ("1000", 1000)),
            (["1000E", "1"], "m", ("1000", 1000)),
            (["1000NDV", "1"], "m", ("1000", 1000)),
            (["M1000", "1"], "m", ("1000", 1000)),
            (["2KM", "1"], "m", ("2000", 2000)),
        ):
            units = structs.Units(**static.core.NA_UNITS)
            wx, vis = core.get_visibility(wx, units)
            self.assertEqual(wx, ["1"])
            self.assert_number(vis, *visibility)
            self.assertEqual(units.visibility, unit)

    def test_get_digit_list(self):
        """
        Tests that digits are removed after an index but before a non-digit item
        """
        items = ["1", "T", "2", "3", "ODD", "Q", "4", "C"]
        items, ret = core.get_digit_list(items, 1)
        self.assertEqual(items, ["1", "ODD", "Q", "4", "C"])
        self.assertEqual(ret, ["2", "3"])
        items, ret = core.get_digit_list(items, 2)
        self.assertEqual(items, ["1", "ODD", "C"])
        self.assertEqual(ret, ["4"])

    def test_sanitize_cloud(self):
        """
        Tests the common cloud issues are fixed before parsing
        """
        for bad, good in (
            ("OVC", "OVC"),
            ("010", "010"),
            ("SCT060", "SCT060"),
            ("FEWO03", "FEW003"),
            ("BKNC015", "BKN015C"),
            ("FEW027///", "FEW027///"),
        ):
            self.assertEqual(core.sanitize_cloud(bad), good)

    def test_make_cloud(self):
        """
        Tests helper function which returns a Cloud dataclass
        """
        for cloud, out in (
            ("SCT060", ["SCT", 60, None, None]),
            ("FEWO03", ["FEW", 3, None, None]),
            ("BKNC015", ["BKN", 15, None, "C"]),
            ("OVC120TS", ["OVC", 120, None, "TS"]),
            ("VV002", ["VV", 2, None, None]),
            ("SCT", ["SCT", None, None, None]),
            ("FEW027///", ["FEW", 27, None, None]),
            ("FEW//////", ["FEW", None, None, None]),
            ("FEW///TS", ["FEW", None, None, "TS"]),
            ("OVC100-TOP110", ["OVC", 100, 110, None]),
            ("OVC065-TOPUNKN", ["OVC", 65, None, None]),
            ("SCT-BKN050-TOP100", ["SCT-BKN", 50, 100, None]),
        ):
            ret_cloud = core.make_cloud(cloud)
            self.assertIsInstance(ret_cloud, structs.Cloud)
            self.assertEqual(ret_cloud.repr, cloud)
            for i, key in enumerate(("type", "base", "top", "modifier")):
                self.assertEqual(getattr(ret_cloud, key), out[i])

    def test_get_clouds(self):
        """
        Tests that clouds are removed, fixed, and split correctly
        """
        for wx, clouds in (
            (["1"], []),
            (["SCT060", "1"], [["SCT", 60, None]]),
            (
                ["OVC100", "1", "VV010", "SCTO50C"],
                [["VV", 10, None], ["SCT", 50, "C"], ["OVC", 100, None]],
            ),
            (["1", "BKN020", "SCT050"], [["BKN", 20, None], ["SCT", 50, None]]),
        ):
            wx, ret_clouds = core.get_clouds(wx)
            self.assertEqual(wx, ["1"])
            for i, cloud in enumerate(ret_clouds):
                self.assertIsInstance(cloud, structs.Cloud)
                for j, key in enumerate(("type", "base", "modifier")):
                    self.assertEqual(getattr(cloud, key), clouds[i][j])

    def test_get_flight_rules(self):
        """
        Tests that the proper flight rule is calculated for a set visibility and ceiling

        Note: Only 'Broken', 'Overcast', and 'Vertical Visibility' are considered ceilings
        """
        for vis, ceiling, rule in (
            (None, None, "IFR"),
            ("10", None, "VFR"),
            ("P6SM", ["OCV", 50], "VFR"),
            ("6", ["OVC", 20], "MVFR"),
            ("6", ["OVC", 7], "IFR"),
            ("2", ["OVC", 20], "IFR"),
            ("6", ["OVC", 4], "LIFR"),
            ("1/2", ["OVC", 30], "LIFR"),
            ("M1/4", ["OVC", 30], "LIFR"),
        ):
            vis = core.make_number(vis)
            if ceiling:
                ceiling = structs.Cloud(None, *ceiling)
            self.assertEqual(
                static.core.FLIGHT_RULES[core.get_flight_rules(vis, ceiling)], rule
            )

    def test_get_ceiling(self):
        """
        Tests that the ceiling is properly identified from a list of clouds
        """
        for clouds, ceiling in (
            ([], None),
            ([["FEW", 10], ["SCT", 10]], None),
            ([["OVC", None]], None),
            ([["VV", 5]], ["VV", 5]),
            ([["OVC", 20], ["BKN", 30]], ["OVC", 20]),
            ([["OVC", None], ["BKN", 30]], ["BKN", 30]),
            ([["FEW", 10], ["OVC", 20]], ["OVC", 20]),
        ):
            clouds = [structs.Cloud(None, *cloud) for cloud in clouds]
            if ceiling:
                ceiling = structs.Cloud(None, *ceiling)
            self.assertEqual(core.get_ceiling(clouds), ceiling)

    def test_parse_date(self):
        """
        Tests that report timestamp is parsed into a datetime object
        """
        today = datetime.now(tz=timezone.utc)
        rts = today.strftime(r"%d%H%MZ")
        parsed = core.parse_date(rts)
        self.assertIsInstance(parsed, datetime)
        self.assertEqual(parsed.day, today.day)
        self.assertEqual(parsed.hour, today.hour)
        self.assertEqual(parsed.minute, today.minute)

    def test_make_timestamp(self):
        """
        Tests that a report timestamp is converted into a Timestamp dataclass
        """
        today = datetime.now(tz=timezone.utc)
        rts = today.strftime(r"%d%HZ")
        date = core.make_timestamp(rts)
        self.assertIsInstance(date, structs.Timestamp)
        self.assertEqual(date.repr, rts)
        self.assertEqual(date.dt.day, today.day)
        self.assertEqual(date.dt.hour, today.hour)

    def test_sanitize_report_string(self):
        """
        Tests a function which fixes common mistakes while the report is a string
        """
        line = "KJFK 36010 ? TSFEW004SCT012FEW///CBBKN080 C A V O K A2992"
        fixed = "KJFK 36010   TS FEW004 SCT012 FEW///CB BKN080 CAVOK A2992"
        self.assertEqual(core.sanitize_report_string(line), fixed)
