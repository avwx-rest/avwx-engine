"""
AIRMET SIGMET Report Tests
"""

# stdlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

# library
from shapely.geometry import LineString

# module
from avwx import structs
from avwx.current import airsigmet
from avwx.parsing import core
from avwx.static.core import CARDINAL_DEGREES, IN_UNITS
from avwx.structs import Code, Coord, Movement, Units

# tests
from tests.util import BaseTest, datetime_parser, round_coordinates


# Used for location filtering tests
COORD_REPORTS = [
    "N1000 W01000 - N1000 E01000 - S1000 E01000 - S1000 W01000",
    "N1000 W00000 - N1000 E02000 - S1000 E02000 - S1000 W00000",
    "N0000 W00000 - N0000 E02000 - S2000 E02000 - S2000 W00000",
    "N0000 W00100 - N0000 E01000 - S2000 E01000 - S2000 W01000",
]
_PRE = "WAUS43 KKCI 230245 CHIT WA 230245 TS VALID UNTIL 230900 NYC FIR "
COORD_REPORTS = [airsigmet.AirSigmet.from_report(_PRE + r) for r in COORD_REPORTS]


class TestAirSigmet(BaseTest):
    """Tests AirSigmet class and parsing"""

    maxDiff = None

    def test_repr(self):
        """Test class name in repr string"""
        self.assertEqual(repr(airsigmet.AirSigmet()), "<avwx.AirSigmet>")

    def test_parse_prep(self):
        """Test report elements are replaced to aid parsing"""
        for source, target in (
            ("1...2..3.. 4. 5.1 6.", "1 <elip> 2 <elip> 3 <elip> 4 <break> 5.1 6"),
            ("CIG BLW 010/VIS PCPN/BR/FG.", "CIG BLW 010 <vis> VIS PCPN/BR/FG"),
            (
                "THRU 15Z. FRZLVL...RANGING FROM",
                "THRU 15Z <break> FRZLVL <elip> RANGING FROM",
            ),
            ("AIRMET ICE...NV UT", "AIRMET ICE <elip> NV UT"),
        ):
            self.assertEqual(airsigmet._parse_prep(source), target.split())

    def test_bulletin(self):
        """Test Bulletin parsing"""
        for repr, type, country, number in (
            ("WSRH31", "sigmet", "RH", 31),
            ("WAUS01", "airmet", "US", 1),
        ):
            bulletin = airsigmet._bulletin(repr)
            self.assertEqual(bulletin.repr, repr)
            self.assertEqual(bulletin.type.value, type)
            self.assertEqual(bulletin.country, country)
            self.assertEqual(bulletin.number, number)

    def test_header(self):
        """Test report header element extraction"""
        for wx, bulletin, issuer, time, correction in (
            ("WSCI35 ZGGG 210031 1 2", "WSCI35", "ZGGG", "210031", None),
            ("WAUS46 KKCI 230416 AAA 1 2", "WAUS46", "KKCI", "230416", "AAA"),
        ):
            ret_wx, *ret = airsigmet._header(wx.split())
            self.assertEqual(ret_wx, ["1", "2"])
            self.assertEqual(ret[0], airsigmet._bulletin(bulletin))
            self.assertEqual(ret[1], issuer)
            self.assertEqual(ret[2], time)
            self.assertEqual(ret[3], correction)

    def test_spacetime(self):
        """Text place, type, and timestamp extraction"""
        for wx, area, report_type, start_time, end_time, station in (
            (
                "SIGE CONVECTIVE SIGMET 74E VALID UNTIL 2255Z 1 2",
                "SIGE",
                "CONVECTIVE SIGMET 74E",
                None,
                "2255Z",
                None,
            ),
            (
                "LDZO SIGMET U01 VALID 050200/050600 LDZA- 1 2",
                "LDZO",
                "SIGMET U01",
                "050200",
                "050600",
                "LDZA",
            ),
            (
                "CHIT WA 230245 AIRMET TANGO FOR TURB AND LLWS VALID UNTIL 230900 1 2",
                "CHI",
                "AIRMET TANGO FOR TURB AND LLWS",
                None,
                "230900",
                None,
            ),
            (
                "SBAZ SIGMET 9 VALID 250700/251100 SBAZ - 1 2",
                "SBAZ",
                "SIGMET 9",
                "250700",
                "251100",
                "SBAZ",
            ),
        ):
            ret_wx, *ret = airsigmet._spacetime(wx.split())
            self.assertEqual(ret_wx, ["1", "2"])
            self.assertEqual(ret[0], area)
            self.assertEqual(ret[1], report_type)
            self.assertEqual(ret[2], start_time)
            self.assertEqual(ret[3], end_time)
            self.assertEqual(ret[4], station)

    def test_first_index(self):
        """Test util to find the first occurence of n strings"""
        source = [str(i) for i in range(10)]
        for index, *targets in (
            (1, "1"),
            (4, "4", "8"),
            (2, "a", "b", "2", "0"),
        ):
            self.assertEqual(airsigmet._first_index(source, *targets), index)

    def test_region(self):
        """Test region extraction"""
        for wx, region, extra in (
            ("FL CSTL WTRS FROM 100SSW", "FL CSTL WTRS", "FROM 100SSW"),
            ("OH LE 50W", "OH LE", "50W"),
            ("OH LE FROM 50W", "OH LE", "FROM 50W"),
            ("ZGZU GUANGZHOU FIR SEV ICE", "ZGZU GUANGZHOU FIR", "SEV ICE"),
        ):
            ret_wx, ret_region = airsigmet._region(wx.split())
            self.assertEqual(ret_wx, extra.split())
            self.assertEqual(ret_region, region)

    def test_time(self):
        """Test observation start and end time extraction"""
        for wx, start, end, extra in (
            (
                "OUTLOOK VALID 230555-230955 FROM 30SSW",
                core.make_timestamp("230555"),
                core.make_timestamp("230955"),
                "FROM 30SSW",
            ),
            (
                "THRU 15Z <break> OTLK VALID 0900-1500Z",
                core.make_timestamp("0900", True),
                core.make_timestamp("1500Z", True),
                "THRU 15Z <break>",
            ),
            (
                "VA CLD OBS AT 0110Z SFC/FL160",
                core.make_timestamp("0110Z", True),
                None,
                "VA CLD SFC/FL160",
            ),
        ):
            ret_wx, ret_start, ret_end = airsigmet._time(wx.split())
            self.assertEqual(ret_wx, extra.split())
            self.assertEqual(ret_start, start)
            self.assertEqual(ret_end, end)

    def test_coord_value(self):
        """Test string to float coordinate component"""
        for coord, value in (
            ("N1429", 14.29),
            ("S0250", -2.5),
            ("N2900", 29.0),
            ("W09053", -90.53),
            ("E01506", 15.06),
            ("E15000", 150.0),
        ):
            self.assertEqual(airsigmet._coord_value(coord), value)

    def test_position(self):
        """Test position coordinate extraction"""
        for wx, coord, extra in (
            ("1 2 3", None, "1 2 3"),
            (
                "VA FUEGO PSN N1428 W09052 VA",
                Coord(14.28, -90.52, "N1428 W09052"),
                "VA FUEGO VA",
            ),
        ):
            ret_wx, ret_coord = airsigmet._position(wx.split())
            self.assertEqual(ret_wx, extra.split())
            self.assertEqual(ret_coord, coord)

    def test_movement(self):
        """Test weather movement extraction"""
        for wx, movement, unit, extra in (
            ("1 2 3", None, "kt", "1 2 3"),
            ("270226Z CNL MOV CNL", None, "kt", "270226Z CNL"),
            (
                "SFC/FL030 STNR WKN=",
                Movement("STNR", None, core.make_number("STNR")),
                "kt",
                "SFC/FL030 WKN=",
            ),
            (
                "FL060/300 MOV E 45KMH NC=",
                Movement(
                    "MOV E 45KMH",
                    core.make_number("E", literal=True, special=CARDINAL_DEGREES),
                    core.make_number("45"),
                ),
                "kmh",
                "FL060/300 NC=",
            ),
            (
                "AREA TS MOV FROM 23040KT",
                Movement(
                    "MOV FROM 23040KT", core.make_number("230"), core.make_number("40")
                ),
                "kt",
                "AREA TS",
            ),
            (
                "ABV FL040 MOV NW",
                Movement(
                    "MOV NW",
                    core.make_number("NW", literal=True, special=CARDINAL_DEGREES),
                    None,
                ),
                "kt",
                "ABV FL040",
            ),
            (
                "TOP FL480 MOV W 05-10KT",
                Movement(
                    "MOV W 05-10KT",
                    core.make_number("W", literal=True, special=CARDINAL_DEGREES),
                    core.make_number("10"),
                ),
                "kt",
                "TOP FL480",
            ),
            (
                "TOP FL390 MOV N/NE 08KT",
                Movement(
                    "MOV N/NE 08KT",
                    core.make_number("NNE", literal=True, special=CARDINAL_DEGREES),
                    core.make_number("08"),
                ),
                "kt",
                "TOP FL390",
            ),
        ):
            units = Units(**IN_UNITS)
            ret_wx, units, ret_movement = airsigmet._movement(wx.split(), units)
            self.assertEqual(ret_wx, extra.split())
            self.assertEqual(ret_movement, movement)
            self.assertEqual(units.wind_speed, unit)

    def test_bounds_from_latterals(self):
        """Test extracting latteral bound strings from the report"""
        for report, bounds, start, extra in (
            (
                "FCST N OF N2050 AND S OF N2900 FL060/300",
                ["N OF N2050", "S OF N2900"],
                5,
                "FCST   AND   FL060/300",
            ),
            ("FCST N OF N33 TOP", ["N OF N33"], 5, "FCST   TOP"),
        ):
            ret_report, ret_bounds, ret_start = airsigmet._bounds_from_latterals(
                report, -1
            )
            self.assertEqual(ret_report, extra)
            self.assertEqual(ret_bounds, bounds)
            self.assertEqual(ret_start, start)

    def test_coords_from_text(self):
        """Test extracting coords from NESW string pairs in the report"""
        for report, coords, start, extra in (
            (
                "LINE BTN N6916 W06724 - N6825 W06700 - N6753 W06524",
                ((69.16, -67.24), (68.25, -67.00), (67.53, -65.24)),
                9,
                "LINE BTN      ",
            ),
            (
                "WI N4523 E01356 <break> N6753 W06524",
                ((45.23, 13.56),),
                3,
                "WI   <break> N6753 W06524",
            ),
        ):
            ret_report, ret_coords, ret_start = airsigmet._coords_from_text(report, -1)
            self.assertEqual(ret_report, extra)
            self.assertEqual(ret_start, start)
            for coord, (lat, lon) in zip(ret_coords, coords):
                self.assertEqual(coord.lat, lat)
                self.assertEqual(coord.lon, lon)

    def test_coords_from_navaids(self):
        """Test extracting coords from relative navaidlocations in the report"""
        for report, coords, start, extra in (
            (
                "1 FROM 30SSW BNA-40W MGM-30ENE LSU 1",
                ((35.67, -86.92), (32.22, -87.11), (4.74, 115.96)),
                7,
                "1 FROM     1",
            ),
            (
                "FROM 100SSW TLH-80W PIE-160WSW SRQ",
                ((28.85, -85.08), (27.9, -84.19), (26.35, -85.3)),
                5,
                "FROM    ",
            ),
        ):
            ret_report, ret_coords, ret_start = airsigmet._coords_from_navaids(
                report, -1
            )
            self.assertEqual(ret_report, extra)
            self.assertEqual(ret_start, start)
            for coord, (lat, lon) in zip(ret_coords, coords):
                self.assertEqual(round(coord.lat, 2), lat)
                self.assertEqual(round(coord.lon, 2), lon)

    def test_bounds(self):
        """Test extracting all pre-break bounds and coordinates from the report"""
        for wx, coords, bounds, extra in (
            (
                "FCST N OF N2050 AND S OF N2900 FL060/300",
                [],
                ["N OF N2050", "S OF N2900"],
                "FCST FL060/300",
            ),
            (
                "LINE BTN N6916 W06724 - N6825 W06700 - N6753 W06524",
                ((69.16, -67.24), (68.25, -67.00), (67.53, -65.24)),
                [],
                "LINE BTN",
            ),
            (
                "OBS WI N4523 E01356 <break> N6753 W06524",
                ((45.23, 13.56),),
                [],
                "<break> N6753 W06524",
            ),
            (
                "1 FROM 30SSW BNA-40W MGM-30ENE LSU 1",
                ((35.67, -86.92), (32.22, -87.11), (4.74, 115.96)),
                [],
                "1 1",
            ),
            (
                "FROM 100SSW TLH-80W PIE-160WSW SRQ",
                ((28.85, -85.08), (27.9, -84.19), (26.35, -85.3)),
                [],
                "",
            ),
        ):
            ret_wx, ret_coords, ret_bounds = airsigmet._bounds(wx.split())
            self.assertEqual(ret_wx, extra.split())
            self.assertEqual(ret_bounds, bounds)
            for coord, (lat, lon) in zip(ret_coords, coords):
                self.assertEqual(round(coord.lat, 2), lat)
                self.assertEqual(round(coord.lon, 2), lon)

    def test_altitudes(self):
        """Tests extracting floor and ceiling altitudes from report"""
        for wx, floor, ceiling, unit, extra in (
            ("1 FL060/300 2", 60, 300, "ft", "1 2"),
            ("0110Z SFC/FL160", 0, 160, "ft", "0110Z"),
            ("0110Z SFC/10000FT", 0, 10000, "ft", "0110Z"),
            ("1 TOPS TO FL310 <break> 2", None, 310, "ft", "1 <break> 2"),
            ("1 SFC/2000M 2", 0, 2000, "m", "1 2"),
            ("1 TOPS ABV FL450 2", None, 450, "ft", "1 2"),
            ("TURB BTN FL180 AND FL330", 180, 330, "ft", "TURB"),
            ("1 CIG BLW 010 2", None, 10, "ft", "1 2"),
            ("1 TOP BLW FL380 2", None, 380, "ft", "1 2"),
        ):
            units = Units(**IN_UNITS)
            ret_wx, units, ret_floor, ret_ceiling = airsigmet._altitudes(
                wx.split(), units
            )
            self.assertEqual(ret_wx, extra.split())
            self.assertEqual(units.altitude, unit)
            if floor is None:
                self.assertIsNone(ret_floor)
            else:
                self.assertEqual(ret_floor.value, floor)
            if ceiling is None:
                self.assertIsNone(ceiling)
            else:
                self.assertEqual(ret_ceiling.value, ceiling)

    def test_weather_type(self):
        """Tests extracting weather type code from report"""
        for wx, code, name, extra in (
            ("1 2 3 4", None, None, "1 2 3 4"),
            ("FIR SEV ICE FCST N", "SEV ICE", "Severe icing", "FIR FCST N"),
            ("W09052 VA CLD OBS AT", "VA CLD", "Volcanic cloud", "W09052 OBS AT"),
        ):
            ret_wx, weather = airsigmet._weather_type(wx.split())
            self.assertEqual(ret_wx, extra.split())
            if code is None:
                self.assertIsNone(weather)
            else:
                self.assertEqual(weather, Code(code, name))

    def test_intensity(self):
        """Tests extracting intensity code from report"""
        for wx, code, name, extra in (
            ("1 2 3 4", None, None, "1 2 3 4"),
            ("1 2 3 NC", "NC", "No change", "1 2 3"),
            ("1 2 3 INTSF", "INTSF", "Intensifying", "1 2 3"),
            ("1 2 3 WKN", "WKN", "Weakening", "1 2 3"),
        ):
            ret_wx, intensity = airsigmet._intensity(wx.split())
            self.assertEqual(ret_wx, extra.split())
            if code is None:
                self.assertIsNone(intensity)
            else:
                self.assertEqual(intensity, Code(code, name))

    def test_sanitize(self):
        """Tests report sanitization"""
        for report, clean in (
            ("WAUS43 KKCI  1 \n 2 3 NC=", "WAUS43 KKCI 1 2 3 NC"),
            ("TOP FL520 MO V NNW 05KT NC", "TOP FL520 MOV NNW 05KT NC"),
            ("FL450 MOV NE05KT INTSF=", "FL450 MOV NE 05KT INTSF"),
        ):
            self.assertEqual(airsigmet.sanitize(report), clean)

    def test_parse(self):
        """Tests returned structs from the parse function"""
        report = (
            "WAUS43 KKCI 230245 CHIT WA 230245 AIRMET TANGO FOR TURB AND LLWS "
            "VALID UNTIL 230900 AIRMET TURB...ND SD NE MN IA WI LM LS MI LH "
            "FROM 70N SAW TO SSM TO YVV TO 50SE GRB TO 20SW DLL TO ONL TO BFF "
            "TO 70SW RAP TO 50W DIK TO BIS TO 50SE BJI TO 70N SAW MOD TURB "
            "BTN FL180 AND FL330. CONDS CONTG BYD 09Z THRU 15Z"
        )
        data, units = airsigmet.parse(report)
        self.assertIsInstance(data, structs.AirSigmetData)
        self.assertIsInstance(units, structs.Units)
        self.assertEqual(data.raw, report)

    def test_contains(self):
        """Tests if report contains a coordinate"""
        for lat, lon, results in (
            (5, 5, (True, True, False, False)),
            (5, -15, (False, False, False, False)),
            (5, 15, (False, True, False, False)),
            (5, -5, (True, False, False, False)),
            (0, 0, (True, False, False, False)),
        ):
            coord = Coord(lat, lon)
            for report, result in zip(COORD_REPORTS, results):
                self.assertEqual(report.contains(coord), result)

    def test_intersects(self):
        """Testsif report intersects a path"""
        for coords, results in (
            (((20, 20), (0, 0), (-20, -20)), (True, True, True, True)),
            (((20, 20), (10, 0), (-20, -20)), (True, True, False, False)),
            (((-20, 20), (-10, -10), (-20, -20)), (True, False, True, True)),
            (((-20, 20), (-15, -15), (-20, -20)), (False, False, True, True)),
        ):
            path = LineString(coords)
            for report, result in zip(COORD_REPORTS, results):
                self.assertEqual(report.intersects(path), result)

    def test_airsigmet_ete(self):
        """Performs an end-to-end test of reports in the AIRSIGMET JSON file"""
        path = Path(__file__).parent / "data" / "airsigmet.json"
        for ref in json.load(path.open(), object_hook=datetime_parser):
            created = ref.pop("created").date()
            airsig = airsigmet.AirSigmet()
            self.assertIsNone(airsig.last_updated)
            self.assertIsNone(airsig.issued)
            self.assertTrue(airsig.parse(ref["data"]["raw"], issued=created))
            self.assertIsInstance(airsig.last_updated, datetime)
            self.assertEqual(airsig.issued, created)
            self.assertEqual(round_coordinates(asdict(airsig.data)), ref["data"])


class TestAirSigManager(BaseTest):
    """Tests AirSigManager filtering"""

    def test_contains(self):
        """Tests filtering reports that contain a coordinate"""
        manager = airsigmet.AirSigManager()
        manager.reports = COORD_REPORTS
        for lat, lon, count in (
            (5, 5, 2),
            (5, -15, 0),
            (5, 15, 1),
            (5, -5, 1),
            (0, 0, 1),
        ):
            coord = Coord(lat, lon)
            self.assertEqual(len(manager.contains(coord)), count)

    def test_along(self):
        """Tests filtering reports the fall along a flight path"""
        manager = airsigmet.AirSigManager()
        manager.reports = COORD_REPORTS
        for coords, count in (
            (((20, 20), (0, 0), (-20, -20)), 4),
            (((20, 20), (10, 0), (-20, -20)), 2),
            (((-20, 20), (-10, -10), (-20, -20)), 3),
            (((-20, 20), (-15, -15), (-20, -20)), 2),
        ):
            path = [Coord(c[0], c[1]) for c in coords]
            self.assertEqual(len(manager.along(path)), count)
