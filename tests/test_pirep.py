"""
PIREP Report Tests
"""

# stdlib
import json
import unittest
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

# module
from avwx import Pireps, pirep, structs


class TestPirepHandlers(unittest.TestCase):
    """
    Tests PIREP element handlers
    """

    def _test_num(self, src: "Number/None", exp: "int/None"):
        """
        Tests a nNumber value or is None
        """
        if exp is None:
            self.assertIsNone(src)
        else:
            self.assertEqual(src.value, exp)

    def test_root(self):
        """
        Tests station and type identification
        """
        for root, station, report_type in (
            ("JAX UA", "JAX", "UA"),
            ("DMW UUA", "DMW", "UUA"),
            ("UA", None, "UA"),
            ("MCO", "MCO", None),
        ):
            ret_root = pirep._root(root)
            self.assertIsInstance(ret_root, dict)
            self.assertEqual(ret_root["station"], station)
            self.assertEqual(ret_root["type"], report_type)

    def test_location(self):
        """
        Tests location unpacking
        """
        for loc, station, direction, distance in (
            ("MLB", "MLB", None, None),
            ("MKK360002", "MKK", 360, 2),
            ("KLGA220015", "KLGA", 220, 15),
            ("10 WGON", "GON", 270, 10),
            ("GON 270010", "GON", 270, 10),
        ):
            ret_loc = pirep._location(loc)
            self.assertIsInstance(ret_loc, structs.Location)
            self.assertEqual(ret_loc.repr, loc)
            self.assertEqual(ret_loc.station, station)
            self._test_num(ret_loc.direction, direction)
            self._test_num(ret_loc.distance, distance)

    def test_time(self):
        """
        Tests time parsing
        """
        for time in ("1930", "0000", "2359", "0515"):
            ret_time = pirep._time(time)
            self.assertIsInstance(ret_time, structs.Timestamp)
            self.assertEqual(ret_time.repr, time)
            self.assertEqual(ret_time.dt.hour, int(time[:2]))
            self.assertEqual(ret_time.dt.minute, int(time[2:]))
            self.assertEqual(ret_time.dt.second, 0)
        self.assertIsNone(pirep._time(None))

    def test_altitude(self):
        """
        Tests converting altitude to Number
        """
        for alt, num in (("2000", 2000), ("9999", 9999), ("0500", 500)):
            ret_alt = pirep._altitude(alt)
            self.assertIsInstance(ret_alt, structs.Number)
            self.assertEqual(ret_alt.repr, alt)
            self.assertEqual(ret_alt.value, num)
        self.assertIsInstance(pirep._altitude("test"), str)

    def test_aircraft(self):
        """
        Tests converting aircraft code into Aircraft
        """
        for code, name in (
            ("B752", "Boeing 757-200"),
            ("PC12", "Pilatus PC-12"),
            ("C172", "Cessna 172"),
        ):
            aircraft = pirep._aircraft(code)
            self.assertIsInstance(aircraft, structs.Aircraft)
            self.assertEqual(aircraft.code, code)
            self.assertEqual(aircraft.type, name)
        self.assertIsInstance(pirep._aircraft("not a code"), str)

    def test_cloud_tops(self):
        """
        Tests converting clouds with tops
        """
        for cloud, out in (
            ("OVC100-TOP110", ["OVC", 100, 110]),
            ("OVC065-TOPUNKN", ["OVC", 65, None]),
            ("OVCUNKN-TOP150", ["OVC", None, 150]),
            ("SCT-BKN050-TOP100", ["SCT-BKN", 50, 100]),
            ("BKN-OVCUNKN-TOP060", ["BKN-OVC", None, 60]),
            ("BKN120-TOP150", ["BKN", 120, 150]),
            ("OVC-TOP085", ["OVC", None, 85]),
        ):
            parsed = pirep._clouds(cloud)[0]
            self.assertIsInstance(parsed, structs.Cloud)
            self.assertEqual(parsed.repr, cloud)
            for i, key in enumerate(("type", "base", "top")):
                self.assertEqual(getattr(parsed, key), out[i])

    def test_number(self):
        """
        Tests converting value into a Number
        """
        for num, value in (("01", 1), ("M01", -1), ("E", 90), ("1/4", 0.25)):
            ret_num = pirep._number(num)
            self.assertIsInstance(ret_num, structs.Number)
            self.assertEqual(ret_num.repr, num)
            self.assertEqual(ret_num.value, value)
        self.assertIsNone(pirep._number(""))

    def test_turbulence(self):
        """
        Tests converting turbulence string to Turbulence
        """
        for turb, severity, floor, ceiling in (
            ("MOD CHOP", "MOD CHOP", None, None),
            ("LGT-MOD CAT 160-260", "LGT-MOD CAT", 160, 260),
            ("LGT-MOD 180-280", "LGT-MOD", 180, 280),
            ("LGT", "LGT", None, None),
            ("CONT LGT CHOP BLO 250", "CONT LGT CHOP", None, 250),
        ):
            ret_turb = pirep._turbulence(turb)
            self.assertIsInstance(ret_turb, structs.Turbulence)
            self.assertEqual(ret_turb.severity, severity)
            self._test_num(ret_turb.floor, floor)
            self._test_num(ret_turb.ceiling, ceiling)

    def test_icing(self):
        """
        Tests converting icing string to Icing
        """
        for ice, severity, itype, floor, ceiling in (
            ("MOD RIME", "MOD", "RIME", None, None),
            ("LGT RIME 025", "LGT", "RIME", 25, 25),
            ("LIGHT MIXED", "LIGHT", "MIXED", None, None),
            ("NEG", "NEG", None, None, None),
            ("TRACE RIME 070-090", "TRACE", "RIME", 70, 90),
            ("LGT RIME 220-260", "LGT", "RIME", 220, 260),
        ):
            ret_ice = pirep._icing(ice)
            print(ret_ice)
            self.assertIsInstance(ret_ice, structs.Icing)
            self.assertEqual(ret_ice.severity, severity)
            self.assertEqual(ret_ice.type, itype)
            self._test_num(ret_ice.floor, floor)
            self._test_num(ret_ice.ceiling, ceiling)

    def test_remarks(self):
        """
        Tests remarks pass through
        """
        for rmk in ("Test", "12345", "IT WAS MOSTLY SMOOTH"):
            ret_rmk = pirep._remarks(rmk)
            self.assertIsInstance(ret_rmk, str)
            self.assertEqual(ret_rmk, rmk)

    def test_wx(self):
        """
        Tests wx split and visibility ident
        """
        for txt, wx in (("VCFC", ["VCFC"]), ("+RATS -GR", ["+RATS", "-GR"])):
            ret_wx = pirep._wx(txt)
            self.assertIsInstance(ret_wx, dict)
            self.assertEqual(ret_wx["wx"], wx)
        ret_wx = pirep._wx("FV1000 VCFC")
        self.assertIsInstance(ret_wx, dict)
        self.assertEqual(ret_wx["wx"], ["VCFC"])
        self.assertIsInstance(ret_wx["flight_visibility"], structs.Number)
        self.assertEqual(ret_wx["flight_visibility"].value, 1000)


class TestPirep(unittest.TestCase):
    """
    Test Pirep class and parsing
    """

    maxDiff = None

    def test_parse(self):
        """
        Tests returned structs from the parse function
        """
        for report in (
            "EWR UA /OV SBJ090/010/TM 2108/FL060/TP B738/TB MOD",
            "SMQ UA /OV BWZ/TM 0050/FL280/TP A320/TB MOD",
        ):
            data = pirep.parse(report)
            self.assertIsInstance(data, structs.PirepData)
            self.assertEqual(data.raw, report)

    def test_pirep_ete(self):
        """
        Performs an end-to-end test of all PIREP JSON files
        """
        for path in Path(__file__).parent.joinpath("pirep").glob("*.json"):
            path = Path(path)
            ref = json.load(path.open())
            station = Pireps(path.stem)
            self.assertIsNone(station.last_updated)
            reports = [report["data"]["raw"] for report in ref["reports"]]
            self.assertTrue(station.update(reports))
            self.assertIsInstance(station.last_updated, datetime)
            for i, report in enumerate(ref["reports"]):
                # Clear timestamp due to parse_date limitations
                station.data[i].time = None
                self.assertEqual(asdict(station.data[i]), report["data"])
            self.assertEqual(asdict(station.station_info), ref["station_info"])
