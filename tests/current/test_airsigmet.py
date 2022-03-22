"""
AIRMET SIGMET Report Tests
"""

# module
from avwx.current import airsigmet
from avwx.parsing import core
from avwx.static.core import CARDINAL_DEGREES, IN_UNITS
from avwx.structs import Coord, Movement, Units

# tests
from tests.util import BaseTest


class TestAirSigmet(BaseTest):
    """Tests AirSigmet class and parsing"""

    maxDiff = None

    def test_parse_prep(self):
        """"""

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
        ):
            units = Units(**IN_UNITS)
            ret_wx, units, ret_movement = airsigmet._movement(wx.split(), units)
            self.assertEqual(ret_wx, extra.split())
            self.assertEqual(ret_movement, movement)
            self.assertEqual(units.wind_speed, unit)

    def test_info_from_match(self):
        """"""

    def test_bounds_from_latterals(self):
        """"""

    def test_coords_from_text(self):
        """"""

    def test_coords_from_navaids(self):
        """"""

    def test_bounds(self):
        """"""

    def test_is_altitude(self):
        """"""

    def test_make_altitude(self):
        """"""

    def test_altitudes(self):
        """"""

    def test_weather_type(self):
        """"""

    def test_intensity(self):
        """"""
