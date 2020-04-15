"""
TAF Report Tests
"""


# stdlib
import json
import unittest
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

# module
from avwx import static, structs
from avwx.current import taf
from avwx.parsing import core

from tests.util import get_data


class TestTaf(unittest.TestCase):
    """
    Tests Taf class and parsing
    """

    maxDiff = None

    def test_get_taf_remarks(self):
        """
        Tests that remarks are removed from a TAF report
        """
        for txt, rmk in (
            ("KJFK test", ""),
            ("KJFK test RMK test", "RMK test"),
            ("KJFK test FCST test", "FCST test"),
            ("KJFK test AUTOMATED test", "AUTOMATED test"),
        ):
            report, remarks = taf.get_taf_remarks(txt)
            self.assertEqual(report, "KJFK test")
            self.assertEqual(remarks, rmk)

    def test_sanitize_line(self):
        """
        Tests a function which fixes common new-line signifiers in TAF reports
        """
        for line in ("1 BEC 1", "1 BE CMG1", "1 BEMG 1"):
            self.assertEqual(taf.sanitize_line(line), "1 BECMG 1")
        for line in ("1 TEMP0 1", "1 TEMP 1", "1 TEMO1", "1 T EMPO1"):
            self.assertEqual(taf.sanitize_line(line), "1 TEMPO 1")
        self.assertEqual(taf.sanitize_line("1 2 3 4 5"), "1 2 3 4 5")

    def test_is_tempo_or_prob(self):
        """
        Tests a function which checks that an item signifies a new time period
        """
        for line in (
            {"type": "TEMPO"},
            {"probability": 30},
            {"probability": "PROBNA"},
            {"type": "FROM", "probability": 30},
        ):
            self.assertTrue(taf._is_tempo_or_prob(line))
        for line in ({"type": "FROM"}, {"type": "FROM", "probability": None}):
            self.assertFalse(taf._is_tempo_or_prob(line))

    def test_get_alt_ice_turb(self):
        """
        Tests that report global altimeter, icing, and turbulence get removed
        """
        for wx, *data in (
            (["1"], "", [], []),
            (["1", "512345", "612345"], "", ["612345"], ["512345"]),
            (["QNH1234", "1", "612345"], core.make_number("1234"), ["612345"], []),
        ):
            self.assertEqual(taf.get_alt_ice_turb(wx), (["1"], *data))

    def test_starts_new_line(self):
        """
        Tests that certain items are identified as new line markers in TAFs
        """
        for item in [
            *static.taf.TAF_NEWLINE,
            "PROB30",
            "PROB45",
            "PROBNA",
            "FM12345678",
        ]:
            self.assertTrue(taf.starts_new_line(item))
        for item in ("KJFK", "12345Z", "2010/2020", "FEW060", "RMK"):
            self.assertFalse(taf.starts_new_line(item))

    def test_split_taf(self):
        """
        Tests that TAF reports are split into the correct time periods
        """
        for report, num in (
            ("KJFK test", 1),
            ("KJFK test FM12345678 test", 2),
            ("KJFK test TEMPO test", 2),
            ("KJFK test TEMPO test TEMPO test", 3),
            ("KJFK test PROB30 test TEMPO test", 3),
            ("KJFK test PROB30 TEMPO test TEMPO test", 3),
        ):
            split = taf.split_taf(report)
            self.assertEqual(len(split), num)
            self.assertEqual(split[0], "KJFK test")

    def test_get_type_and_times(self):
        """
        Tests TAF line type, start time, and end time extraction
        """
        for wx, *data in (
            (["1"], "FROM", "", ""),
            (["INTER", "1"], "INTER", "", ""),
            (["TEMPO", "0101/0103", "1"], "TEMPO", "0101", "0103"),
            (["PROB30", "0101/0103", "1"], "PROB30", "0101", "0103"),
            (["FM120000", "1"], "FROM", "1200", ""),
            (["FM1200/1206", "1"], "FROM", "1200", "1206"),
            (["FM120000", "TL120600", "1"], "FROM", "1200", "1206"),
        ):
            self.assertEqual(taf.get_type_and_times(wx), (["1"], *data))

    def test_find_missing_taf_times(self):
        """
        Tests that missing forecast times can be interpretted by 
        """
        good_lines = [
            {"type": "FROM", "start_time": "3021", "end_time": "3023"},
            {"type": "FROM", "start_time": "3023", "end_time": "0105"},
            {"type": "FROM", "start_time": "0105", "end_time": "0108"},
            {"type": "FROM", "start_time": "0108", "end_time": "0114"},
        ]
        for line in good_lines:
            for key in ("start_time", "end_time"):
                line[key] = core.make_timestamp(line[key])
        bad_lines = deepcopy(good_lines)
        bad_lines[0]["start_time"] = None
        bad_lines[1]["start_time"] = None
        bad_lines[2]["end_time"] = None
        bad_lines[3]["end_time"] = None
        start, end = good_lines[0]["start_time"], good_lines[-1]["end_time"]
        self.assertEqual(taf.find_missing_taf_times(bad_lines, start, end), good_lines)

    def test_get_temp_min_and_max(self):
        """
        Tests that temp max and min times are extracted and assigned properly
        """
        for wx, *temps in (
            (["1"], "", ""),
            (["1", "TX12/1316Z", "TNM03/1404Z"], "TX12/1316Z", "TNM03/1404Z"),
            (["1", "TM03/1404Z", "T12/1316Z"], "TX12/1316Z", "TNM03/1404Z"),
        ):
            self.assertEqual(taf.get_temp_min_and_max(wx), (["1"], *temps))

    def test_get_oceania_temp_and_alt(self):
        """
        Tests that Oceania-specific elements are identified and removed
        """
        items = ["1", "T", "2", "3", "ODD", "Q", "4", "C"]
        items, tlist, qlist = taf.get_oceania_temp_and_alt(items)
        self.assertEqual(items, ["1", "ODD", "C"])
        self.assertEqual(tlist, ["2", "3"])
        self.assertEqual(qlist, ["4"])

    def test_get_wind_shear(self):
        """
        Tests extracting wind shear
        """
        for wx, shear in (
            (["1", "2"], None),
            (["1", "2", "WS020/07040"], "WS020/07040"),
        ):
            self.assertEqual(taf.get_wind_shear(wx), (["1", "2"], shear))

    # def test_get_taf_flight_rules(self):
    #     """
    #     """
    #     pass

    def test_parse(self):
        """
        Tests returned structs from the parse function
        """
        report = (
            "PHNL 042339Z 0500/0606 06018G25KT P6SM FEW030 SCT060 FM050600 06010KT "
            "P6SM FEW025 SCT060 FM052000 06012G20KT P6SM FEW030 SCT060"
        )
        data, units = taf.parse(report[:4], report)
        self.assertIsInstance(data, structs.TafData)
        self.assertIsInstance(units, structs.Units)
        self.assertEqual(data.raw, report)

    def test_prob_line(self):
        """
        Even though PROB__ is not in TAF_NEWLINE, it should still separate,
        add a new line, and include the prob value in line.probability
        """
        report = (
            "TAF AMD CYBC 271356Z 2714/2802 23015G25KT P6SM BKN090 "
            "TEMPO 2714/2718 P6SM -SHRA BKN060 OVC090 "
            "FM271800 22015G25KT P6SM OVC040 "
            "TEMPO 2718/2724 6SM -SHRA "
            "PROB30 2718/2724 VRB25G35KT 1SM +TSRA BR BKN020 OVC040CB "
            "FM280000 23008KT P6SM BKN040 RMK FCST BASED ON AUTO OBS. NXT FCST BY 272000Z"
        )
        tafobj = taf.Taf("CYBC")
        tafobj.update(report)
        lines = tafobj.data.forecast
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[3].probability, None)
        self.assertEqual(lines[4].probability, core.make_number("30"))
        self.assertTrue(lines[4].raw.startswith("PROB30"))

    def test_prob_end(self):
        """
        PROB and TEMPO lines are discrete times and should not affect FROM times
        """
        report = (
            "MMMX 242331Z 2500/2606 24005KT P6SM VC RA SCT020CB SCT080 BKN200 TX25/2521Z TN14/2513Z "
            "TEMPO 2500/2504 6SM TSRA BKN020CB "
            "FM250600 04010KT P6SM SCT020 BKN080 "
            "TEMPO 2512/2515 3SM HZ BKN015 "
            "FM251600 22005KT 4SM HZ BKN020 "
            "FM251800 22010KT 6SM HZ SCT020 BKN200 "
            "PROB40 2522/2602 P6SM TSRA BKN020CB"
        )
        tafobj = taf.Taf("CYBC")
        tafobj.update(report)
        lines = tafobj.data.forecast
        self.assertEqual(lines[0].start_time.repr, "2500")
        self.assertEqual(lines[0].end_time.repr, "2506")
        self.assertEqual(lines[1].start_time.repr, "2500")
        self.assertEqual(lines[1].end_time.repr, "2504")
        self.assertEqual(lines[-2].start_time.repr, "2518")
        self.assertEqual(lines[-2].end_time.repr, "2606")
        self.assertEqual(lines[-1].start_time.repr, "2522")
        self.assertEqual(lines[-1].end_time.repr, "2602")

    def test_wind_shear(self):
        """
        Wind shear should be recognized as its own element in addition to wind
        """
        report = (
            "TAF AMD CYOW 282059Z 2821/2918 09008KT WS015/20055KT P6SM BKN220 "
            "BECMG 2821/2823 19015G25KT "
            "FM290300 21013G23KT P6SM -SHRA BKN040 OVC100 "
            "TEMPO 2903/2909 4SM BR OVC020 "
            "FM290900 25012KT P6SM SCT030 "
            "FM291300 32017G27KT P6SM OVC030 "
            "TEMPO 2913/2918 P6SM -SHRA OVC020 RMK NXT FCST BY 290000Z"
        )
        tafobj = taf.Taf("CYBC")
        tafobj.update(report)
        lines = tafobj.data.forecast
        self.assertEqual(len(lines), 7)
        self.assertEqual(lines[0].wind_shear, "WS015/20055")
        self.assertEqual(tafobj.translations.forecast[1].clouds, None)

    def test_prob_tempo(self):
        """
        Non-PROB types should take precident but still fill the probability value
        """
        report = (
            "EGLL 192253Z 2000/2106 28006KT 9999 BKN035 "
            "PROB30 TEMPO 2004/2009 BKN012 "
            "PROB30 TEMPO 2105/2106 8000 BKN006"
        )
        tafobj = taf.Taf("EGLL")
        tafobj.update(report)
        lines = tafobj.data.forecast
        for line in lines:
            self.assertIsInstance(line.start_time, structs.Timestamp)
            self.assertIsInstance(line.end_time, structs.Timestamp)
        for i in range(1, 3):
            self.assertEqual(lines[i].type, "TEMPO")
            self.assertEqual(lines[i].probability.value, 30)

    def test_taf_ete(self):
        """
        Performs an end-to-end test of all TAF JSON files
        """
        nodate = lambda s: s[s.find("-") + 2 :]
        for path in get_data(__file__, "taf"):
            ref = json.load(path.open())
            station = taf.Taf(path.stem)
            self.assertIsNone(station.last_updated)
            self.assertTrue(station.update(ref["data"]["raw"]))
            self.assertIsInstance(station.last_updated, datetime)
            # Clear timestamp due to parse_date limitations
            nodt = deepcopy(station.data)
            for key in ("time", "start_time", "end_time"):
                setattr(nodt, key, None)
            for i in range(len(nodt.forecast)):
                for key in ("start_time", "end_time"):
                    setattr(nodt.forecast[i], key, None)
            self.assertEqual(asdict(nodt), ref["data"])
            self.assertEqual(asdict(station.translations), ref["translations"])
            self.assertEqual(station.summary, ref["summary"])
            self.assertEqual(nodate(station.speech), nodate(ref["speech"]))

    def test_rule_inherit(self):
        """
        Tests if TAF forecast periods selectively inherit features to calculate flight rules
        """
        report = (
            "CYKF 020738Z 0208/0220 34005KT P6SM FEW015 BKN070 "
            "FM020900 VRB03KT P6SM FEW070 SCT120 "
            "BECMG 0214/0216 12006KT "
            "FM021800 14008KT P6SM BKN025 OVC090"
        )
        expected_rules = ("VFR", "VFR", "VFR", "MVFR")
        tafobj = taf.Taf(report[:4])
        tafobj.update(report)
        for i, line in enumerate(tafobj.data.forecast):
            self.assertEqual(line.flight_rules, expected_rules[i])
