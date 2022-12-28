"""
METAR Report Tests
"""

# pylint: disable=invalid-name

# stdlib
from dataclasses import asdict
from datetime import datetime

# module
from avwx import static, structs
from avwx.current import metar

# tests
from tests.util import BaseTest, get_data


class TestMetar(BaseTest):
    """Tests Metar class and parsing"""

    maxDiff = None

    def test_repr(self):
        """Test type and code in repr string"""
        self.assertEqual(repr(metar.Metar("KMCO")), "<avwx.Metar code=KMCO>")

    def test_get_remarks(self):
        """Remarks get removed first with the remaining components split into a list"""
        for raw, wx, rmk in (
            ("1 2 3 A2992 RMK Hi", ["1", "2", "3", "A2992"], "RMK Hi"),
            ("1 2 3 A2992 Hi", ["1", "2", "3", "A2992"], "Hi"),
            ("1 2 Q0900 NOSIG", ["1", "2", "Q0900"], "NOSIG"),
            ("1 2 3 BLU+ Hello", ["1", "2", "3"], "BLU+ Hello"),
        ):
            test_wx, test_rmk = metar.get_remarks(raw)
            self.assertEqual(wx, test_wx)
            self.assertEqual(rmk, test_rmk)

    def test_get_temp_and_dew(self):
        """Tests temperature and dewpoint extraction"""
        for wx, temp, dew in (
            (["1", "2"], (None,), (None,)),
            (["1", "2", "07/05"], ("07", 7), ("05", 5)),
            (["07/05", "1", "2"], ("07", 7), ("05", 5)),
            (["M05/M10", "1", "2"], ("M05", -5), ("M10", -10)),
            (["///20", "1", "2"], (None,), ("20", 20)),
            (["10///", "1", "2"], ("10", 10), (None,)),
            (["/////", "1", "2"], (None,), (None,)),
            (["XX/01", "1", "2"], (None,), ("01", 1)),
        ):
            ret_wx, ret_temp, ret_dew = metar.get_temp_and_dew(wx)
            self.assertEqual(ret_wx, ["1", "2"])
            self.assert_number(ret_temp, *temp)
            self.assert_number(ret_dew, *dew)
        self.assertEqual(metar.get_temp_and_dew(["MX/01"]), (["MX/01"], None, None))

    def test_get_relative_humidity(self):
        """Tests calculating relative humidity from available temperatures"""
        units = metar.Units(**metar.NA_UNITS)
        for temp, dew, rmk, humidity in (
            (None, None, "", None),
            (12, 5, "", 0.62228),
            (12, 5, "RMK T01230054", 0.62732),
            (None, None, "RMK T00121123", 0.35818),
            (None, 12, "", None),
            (12, None, "", None),
            (12, None, "RMK T12341345", 0.35408),
        ):
            if temp is not None:
                temp = metar.Number("", temp, "")
            if dew is not None:
                dew = metar.Number("", dew, "")
            remarks_info = metar.remarks.parse(rmk)
            value = metar.get_relative_humidity(temp, dew, remarks_info, units)
            if value is not None:
                value = round(value, 5)
            self.assertEqual(humidity, value)

    def test_parse_altimeter(self):
        """Tests that an atlimiter is correctly parsed into a Number"""
        for text, alt in (
            ("A2992", (29.92, "two nine point nine two")),
            ("2992", (29.92, "two nine point nine two")),
            ("A3000", (30.00, "three zero point zero zero")),
            ("Q1000", (1000, "one zero zero zero")),
            ("Q.1000", (1000, "one zero zero zero")),
            ("Q0998", (998, "zero nine nine eight")),
            ("Q1000/10", (1000, "one zero zero zero")),
            ("QNH3003INS", (30.03, "three zero point zero three")),
        ):
            self.assert_number(metar.parse_altimeter(text), text, *alt)
        for text in (None, "12/10", "RMK", "ABCDE", "15KM", "10SM"):
            self.assertIsNone(metar.parse_altimeter(text))

    def test_get_altimeter(self):
        """Tests that the correct alimeter item gets removed from the end of the wx list"""
        for version, wx, alt, unit in (
            ("NA", ["1"], (None,), "inHg"),
            ("NA", ["1", "A2992"], ("A2992", 29.92, "two nine point nine two"), "inHg"),
            (
                "NA",
                ["1", "A3000"],
                ("A3000", 30.00, "three zero point zero zero"),
                "inHg",
            ),
            ("NA", ["1", "2992"], ("2992", 29.92, "two nine point nine two"), "inHg"),
            (
                "NA",
                ["1", "A2992", "Q1000"],
                ("A2992", 29.92, "two nine point nine two"),
                "inHg",
            ),
            (
                "NA",
                ["1", "Q1000", "A2992"],
                ("A2992", 29.92, "two nine point nine two"),
                "inHg",
            ),
            ("NA", ["1", "Q1000"], ("Q1000", 1000, "one zero zero zero"), "hPa"),
            ("IN", ["1"], (None,), "hPa"),
            ("IN", ["1", "Q.1000"], ("Q.1000", 1000, "one zero zero zero"), "hPa"),
            ("IN", ["1", "Q1000/10"], ("Q1000/10", 1000, "one zero zero zero"), "hPa"),
            (
                "IN",
                ["1", "A2992", "Q1000"],
                ("Q1000", 1000, "one zero zero zero"),
                "hPa",
            ),
            (
                "IN",
                ["1", "Q1000", "A2992"],
                ("Q1000", 1000, "one zero zero zero"),
                "hPa",
            ),
            ("IN", ["1", "A2992"], ("A2992", 29.92, "two nine point nine two"), "inHg"),
            (
                "IN",
                ["1", "QNH3003INS"],
                ("QNH3003INS", 30.03, "three zero point zero three"),
                "inHg",
            ),
        ):
            units = structs.Units(**getattr(static.core, version + "_UNITS"))
            ret, ret_alt = metar.get_altimeter(wx, units, version)
            self.assertEqual(ret, ["1"])
            self.assert_number(ret_alt, *alt)
            self.assertEqual(units.altimeter, unit)

    def test_parse_runway_visibility(self):
        """Tests parsing runway visibility range values"""
        for value, runway, vis, var, trend in (
            ("R35L/1000", "35L", ("1000", 1000, "one thousand"), None, None),
            ("R06/M0500", "06", ("M0500", None, "less than five hundred"), None, None),
            ("R33/////", "33", None, None, None),
            (
                "R29/A2000",
                "29",
                ("A2000", None, "greater than two thousand"),
                None,
                None,
            ),
            (
                "R09C/P6000D",
                "09C",
                ("P6000", None, "greater than six thousand"),
                None,
                structs.Code("D", "decreasing"),
            ),
            (
                "R36/1600V3000U",
                "36",
                None,
                (("1600", 1600, "one six hundred"), ("3000", 3000, "three thousand")),
                structs.Code("U", "increasing"),
            ),
            (
                "R16/5000VP6000FT/U",
                "16",
                None,
                (
                    ("5000", 5000, "five thousand"),
                    ("P6000", None, "greater than six thousand"),
                ),
                structs.Code("U", "increasing"),
            ),
            (
                "R16/1400FT/N",
                "16",
                ("1400", 1400, "one four hundred"),
                None,
                structs.Code("N", "no change"),
            ),
        ):
            rvr = metar.parse_runway_visibility(value)
            self.assertEqual(rvr.runway, runway)
            if vis is None:
                self.assertIsNone(rvr.visibility)
            else:
                self.assert_number(rvr.visibility, *vis)
            if var:
                for original, items in zip(rvr.variable_visibility, var):
                    self.assert_number(original, *items)
            self.assertEqual(rvr.trend, trend)

    def test_get_runway_visibility(self):
        """Tests extracting runway visibility"""
        for wx, count in (
            (["1", "2"], 0),
            (["1", "2", "R10/10"], 1),
            (["1", "2", "R02/05", "R34/04"], 2),
        ):
            items, rvr = metar.get_runway_visibility(wx)
            self.assertEqual(items, ["1", "2"])
            self.assertEqual(len(rvr), count)

    def test_sanitize(self):
        """Tests report sanitization"""
        report = "METAR AUTO KJFK 032151ZVRB08KT FEW034BKN250 ? C A V O K RMK TEST"
        clean = "KJFK 032151Z VRB08KT FEW034 BKN250 CAVOK RMK TEST"
        remarks = "RMK TEST"
        data = ["KJFK", "032151Z", "VRB08KT", "FEW034", "BKN250", "CAVOK"]
        sans = structs.Sanitization(
            ["METAR", "AUTO", "?"], {"C A V O K": "CAVOK"}, extra_spaces_needed=True
        )
        ret_clean, ret_remarks, ret_data, ret_sans = metar.sanitize(report)
        self.assertEqual(clean, ret_clean)
        self.assertEqual(remarks, ret_remarks)
        self.assertEqual(data, ret_data)
        self.assertEqual(sans, ret_sans)

    def test_parse(self):
        """Tests returned structs from the parse function"""
        report = (
            "KJFK 032151Z 16008KT 10SM FEW034 FEW130 BKN250 27/23 A3013 RMK AO2 SLP201"
        )
        data, units, sans = metar.parse(report[:4], report)
        self.assertIsInstance(data, structs.MetarData)
        self.assertIsInstance(units, structs.Units)
        self.assertIsInstance(sans, structs.Sanitization)
        self.assertEqual(data.raw, report)

    def test_parse_awos(self):
        """Tests an AWOS weather report. Only used for advisory"""
        report = "3J0 140347Z AUTO 05003KT 07/02 RMK ADVISORY A01  $"
        data, units, sans = metar.parse("KJFK", report, use_na=True)
        self.assertIsInstance(data, structs.MetarData)
        self.assertIsInstance(units, structs.Units)
        self.assertIsInstance(sans, structs.Sanitization)
        self.assertEqual(data.raw, report)
        self.assertEqual(units.altimeter, "inHg")

    def test_metar_ete(self):
        """Performs an end-to-end test of all METAR JSON files"""
        for ref, icao, issued in get_data(__file__, "metar"):
            station = metar.Metar(icao)
            raw = ref["data"]["raw"]
            self.assertEqual(station.sanitize(raw), ref["data"]["sanitized"])
            self.assertIsNone(station.last_updated)
            self.assertIsNone(station.issued)
            self.assertIsNone(station.sanitization)
            self.assertTrue(station.parse(raw, issued=issued))
            self.assertIsInstance(station.last_updated, datetime)
            self.assertEqual(station.issued, issued)
            self.assertIsInstance(station.sanitization, structs.Sanitization)
            self.assertEqual(asdict(station.data), ref["data"])
            self.assertEqual(asdict(station.translations), ref["translations"])
            self.assertEqual(station.summary, ref["summary"])
            self.assertEqual(station.speech, ref["speech"])
