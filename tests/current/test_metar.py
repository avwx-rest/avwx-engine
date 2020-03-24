"""
METAR Report Tests
"""

# stdlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

# module
from avwx import static, structs
from avwx.current import metar

# tests
from tests.util import BaseTest, get_data


class TestMetar(BaseTest):
    """
    Tests Metar class and parsing
    """

    maxDiff = None

    def test_get_remarks(self):
        """
        Remarks get removed first with the remaining components split into a list
        """
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
        """
        Tests temperature and dewpoint extraction
        """
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
            retwx, ret_temp, ret_dew = metar.get_temp_and_dew(wx)
            self.assertEqual(retwx, ["1", "2"])
            self.assert_number(ret_temp, *temp)
            self.assert_number(ret_dew, *dew)
        self.assertEqual(metar.get_temp_and_dew(["MX/01"]), (["MX/01"], None, None))

    def test_get_altimeter(self):
        """
        Tests that the correct alimeter item gets removed from the end of the wx list
        """
        # North American default
        units = structs.Units(**static.core.NA_UNITS)
        for wx, alt in (
            (["1", "2"], (None,)),
            (["1", "2", "A2992"], ("2992", 29.92)),
            (["1", "2", "2992"], ("2992", 29.92)),
            (["1", "2", "A2992", "Q1000"], ("2992", 29.92)),
            (["1", "2", "Q1000", "A2992"], ("2992", 29.92)),
            (["1", "2", "Q1000"], ("1000", 1000)),
        ):
            self.assertEqual(units.altimeter, "inHg")
            retwx, ret_alt = metar.get_altimeter(wx, units)
            self.assertEqual(retwx, ["1", "2"])
            self.assert_number(ret_alt, *alt)
        # The last one should have changed the unit
        self.assertEqual(units.altimeter, "hPa")
        # International
        units = structs.Units(**static.core.IN_UNITS)
        for wx, alt in (
            (["1", "2"], (None,)),
            (["1", "2", "Q.1000"], ("1000", 1000)),
            (["1", "2", "Q1000/10"], ("1000", 1000)),
            (["1", "2", "A2992", "Q1000"], ("1000", 1000)),
            (["1", "2", "Q1000", "A2992"], ("1000", 1000)),
            (["1", "2", "A2992"], ("2992", 29.92)),
        ):
            self.assertEqual(units.altimeter, "hPa")
            retwx, ret_alt = metar.get_altimeter(wx, units, "IN")
            self.assertEqual(retwx, ["1", "2"])
            self.assert_number(ret_alt, *alt)
        # The last one should have changed the unit
        self.assertEqual(units.altimeter, "inHg")

    def test_get_runway_visibility(self):
        """
        Tests extracting runway visibility
        """
        for wx, rvis in (
            (["1", "2"], []),
            (["1", "2", "R10/10"], ["R10/10"]),
            (["1", "2", "R02/05", "R34/04"], ["R02/05", "R34/04"]),
        ):
            self.assertEqual(metar.get_runway_visibility(wx), (["1", "2"], rvis))

    def test_parse(self):
        """
        Tests returned structs from the parse function
        """
        report = (
            "KJFK 032151Z 16008KT 10SM FEW034 FEW130 BKN250 27/23 A3013 RMK AO2 SLP201"
        )
        data, units = metar.parse(report[:4], report)
        self.assertIsInstance(data, structs.MetarData)
        self.assertIsInstance(units, structs.Units)
        self.assertEqual(data.raw, report)

    def test_metar_ete(self):
        """
        Performs an end-to-end test of all METAR JSON files
        """
        for path in get_data(__file__, "metar"):
            path = Path(path)
            ref = json.load(path.open())
            station = metar.Metar(path.stem)
            self.assertIsNone(station.last_updated)
            self.assertTrue(station.update(ref["data"]["raw"]))
            self.assertIsInstance(station.last_updated, datetime)
            # Clear timestamp due to parse_date limitations
            station.data.time = None
            self.assertEqual(asdict(station.data), ref["data"])
            self.assertEqual(asdict(station.translations), ref["translations"])
            self.assertEqual(station.summary, ref["summary"])
            self.assertEqual(station.speech, ref["speech"])
            self.assertEqual(asdict(station.station), ref["station"])
