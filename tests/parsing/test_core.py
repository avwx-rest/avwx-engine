"""
Core Tests
"""

# pylint: disable=too-many-public-methods,invalid-name

# stdlib
from datetime import datetime, timezone

# library
import time_machine

# module
from avwx import static, structs
from avwx.parsing import core
from avwx.static.core import NA_UNITS, IN_UNITS
from avwx.structs import Fraction, Number, Units

# tests
from tests.util import BaseTest


class TestCore(BaseTest):
    """Test core parsing functions"""

    def test_dedupe(self):
        """Tests list deduplication"""
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
        """Tests unknown value when a string value contains only backspace characters or empty"""
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
        """Tests determining if a string is a timestamp element"""
        for ts in ("123456Z", "987654Z"):
            self.assertTrue(core.is_timestamp(ts))
        for nts in ("", "123456Z123", "1234", "1234Z"):
            self.assertFalse(core.is_timestamp(nts))

    def test_unpack_fraction(self):
        """Tests unpacking a fraction where the numerator can be greater than the denominator"""
        for fraction, unpacked in (
            ("", ""),
            ("1", "1"),
            ("1/2", "1/2"),
            ("3/2", "1 1/2"),
            ("10/3", "3 1/3"),
        ):
            self.assertEqual(core.unpack_fraction(fraction), unpacked)

    def test_remove_leading_zeros(self):
        """Tests removing leading zeros from a number"""
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
        """Tests converting digits into spoken values"""
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
        """Tests Number dataclass generation from a number string"""
        self.assertIsNone(core.make_number(""))
        for num, value, spoken in (
            ("1", 1, "one"),
            ("1.5", 1.5, "one point five"),
            ("060", 60, "six zero"),
            ("300", 300, "three hundred"),
            ("25000", 25000, "two five thousand"),
            ("M10", -10, "minus one zero"),
            ("P6SM", None, "greater than six"),
            ("M1/4", None, "less than one quarter"),
            ("FL310", 310, "flight level three one zero"),
            ("ABV FL480", 480, "above flight level four eight zero"),
        ):
            number = core.make_number(num)
            self.assertIsInstance(number, Number)
            self.assertEqual(number.repr, num)
            self.assertEqual(number.value, value)
            self.assertEqual(number.spoken, spoken)
        self.assertEqual(core.make_number("1234", "A1234").repr, "A1234")

    def test_make_number_fractions(self):
        """Tests Fraction dataclass generation from a number string"""
        for num, value, spoken, nmr, dnm, norm in (
            ("1/4", 0.25, "one quarter", 1, 4, "1/4"),
            ("5/2", 2.5, "two and one half", 5, 2, "2 1/2"),
            ("2-1/2", 2.5, "two and one half", 5, 2, "2 1/2"),
            ("3/4", 0.75, "three quarters", 3, 4, "3/4"),
            ("5/4", 1.25, "one and one quarter", 5, 4, "1 1/4"),
            ("11/4", 1.25, "one and one quarter", 5, 4, "1 1/4"),
        ):
            number = core.make_number(num)
            self.assertIsInstance(number, Fraction)
            self.assertEqual(number.value, value)
            self.assertEqual(number.spoken, spoken)
            self.assertEqual(number.numerator, nmr)
            self.assertEqual(number.denominator, dnm)
            self.assertEqual(number.normalized, norm)

    def test_make_number_speech(self):
        """Tests Number generation speech overrides"""
        number = core.make_number("040", speak="040")
        self.assertEqual(number.value, 40)
        self.assertEqual(number.spoken, "zero four zero")
        number = core.make_number("100", literal=True)
        self.assertEqual(number.value, 100)
        self.assertEqual(number.spoken, "one zero zero")

    def test_find_first_in_list(self):
        """Tests a function which finds the first occurrence in a string from a list

        This is used to find remarks and TAF time periods
        """
        for string, targets, index in (
            ("012345", ("5", "2", "3"), 2),
            ("This is weird", ("me", "you", "we"), 8),
            ("KJFK NOPE LOL RMK HAHAHA", static.metar.METAR_RMK, 13),
        ):
            self.assertEqual(core.find_first_in_list(string, targets), index)

    def test_is_possible_temp(self):
        """Tests if an element could be a formatted temperature"""
        for is_temp in ("10", "22", "333", "M05", "5"):
            self.assertTrue(core.is_possible_temp(is_temp))
        for not_temp in ("A", "12.3", "MNA", "-13"):
            self.assertFalse(core.is_possible_temp(not_temp))

    def test_get_station_and_time(self):
        """Tests removal of station (first item) and potential timestamp"""
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
        """Tests that the wind item gets removed and split into its components"""
        # Both us knots as the default unit, so just test North American default
        for wx, unit, *wind, varv in (
            (["1"], "kt", (None,), (None,), (None,), []),
            (["12345", "G50", "1"], "kt", ("123", 123), ("45", 45), ("50", 50), []),
            (["01234G56", "1"], "kt", ("012", 12), ("34", 34), ("56", 56), []),
            (["G30KT", "1"], "kt", (None,), (None,), ("30", 30), []),
            (["10G18KT", "1"], "kt", (None,), ("10", 10), ("18", 18), []),
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
            (["03015G21MPH", "1"], "mi/h", ("030", 30), ("15", 15), ("21", 21), []),
            (["16006GP99KT", "1"], "kt", ("160", 160), ("06", 6), ("P99", None), []),
        ):
            units = structs.Units(**static.core.NA_UNITS)
            wx, *winds, var = core.get_wind(wx, units)
            self.assertEqual(wx, ["1"])
            for parsed, ref in zip(winds, wind):
                self.assert_number(parsed, *ref)
            if varv:
                self.assertIsInstance(varv, list)
                for i in range(2):
                    self.assert_number(var[i], *varv[i])
            self.assertEqual(units.wind_speed, unit)

    def test_get_visibility(self):
        """Tests that the visibility item(s) gets removed and cleaned"""
        for wx, unit, visibility in (
            (["1"], "sm", (None,)),
            (["05SM", "1"], "sm", ("5", 5)),
            (["10SM", "1"], "sm", ("10", 10)),
            (["P6SM", "1"], "sm", ("P6",)),
            (["M1/2SM", "1"], "sm", ("M1/2",)),
            (["M1/4SM", "1"], "sm", ("M1/4",)),
            (["1/2SM", "1"], "sm", ("1/2", 0.5)),
            (["2", "1/2SM", "1"], "sm", ("5/2", 2.5)),
            (["1000", "1"], "m", ("1000", 1000)),
            (["1000E", "1"], "m", ("1000", 1000)),
            (["1000NDV", "1"], "m", ("1000", 1000)),
            (["M1000", "1"], "m", ("1000", 1000)),
            (["2KM", "1"], "m", ("2000", 2000)),
            (["15KM", "1"], "m", ("15000", 15000)),
        ):
            units = structs.Units(**static.core.NA_UNITS)
            wx, vis = core.get_visibility(wx, units)
            self.assertEqual(wx, ["1"])
            self.assert_number(vis, *visibility)
            self.assertEqual(units.visibility, unit)

    def test_get_digit_list(self):
        """Tests that digits are removed after an index but before a non-digit item"""
        items = ["1", "T", "2", "3", "ODD", "Q", "4", "C"]
        items, ret = core.get_digit_list(items, 1)
        self.assertEqual(items, ["1", "ODD", "Q", "4", "C"])
        self.assertEqual(ret, ["2", "3"])
        items, ret = core.get_digit_list(items, 2)
        self.assertEqual(items, ["1", "ODD", "C"])
        self.assertEqual(ret, ["4"])

    def test_sanitize_cloud(self):
        """Tests the common cloud issues are fixed before parsing"""
        for bad, good in (
            ("OVC", "OVC"),
            ("010", "010"),
            ("SCT060", "SCT060"),
            ("FEWO03", "FEW003"),
            ("BKNC015", "BKN015C"),
            ("FEW027///", "FEW027///"),
            ("UNKN021-TOP023", "UNKN021-TOP023"),
        ):
            self.assertEqual(core.sanitize_cloud(bad), good)

    def test_make_cloud(self):
        """Tests helper function which returns a Cloud dataclass"""
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
        """Tests that clouds are removed, fixed, and split correctly"""
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
        """Tests that the proper flight rule is calculated for a set visibility and ceiling

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
        """Tests that the ceiling is properly identified from a list of clouds"""
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

    def test_is_altitude(self):
        """Tests if an element is an altitude"""
        for altitude in ("SFC/FL030", "FL020/030", "6000FT/FL020", "300FT"):
            self.assertTrue(core.is_altitude(altitude))
        for item in ("", "50SE", "KFFT"):
            self.assertFalse(core.is_altitude(item))

    def test_make_altitude(self):
        """Tests converting altitude text into Number"""
        for text, force, value, unit, speak in (
            ("FL030", False, 30, "ft", "flight level three zero"),
            ("030", False, 30, "ft", "three zero"),
            ("030", True, 30, "ft", "flight level three zero"),
            ("6000FT", False, 6000, "ft", "six thousand"),
            ("10000FT", False, 10000, "ft", "one zero thousand"),
            ("2000M", False, 2000, "m", "two thousand"),
            ("ABV FL450", False, 450, "ft", "above flight level four five zero"),
        ):
            units = Units(**IN_UNITS)
            altitude, units = core.make_altitude(text, units, force_fl=force)
            self.assertEqual(altitude.repr, text)
            self.assertEqual(units.altitude, unit)
            self.assertEqual(altitude.value, value)
            self.assertEqual(altitude.spoken, speak)

    def test_parse_date(self):
        """Tests that report timestamp is parsed into a datetime object"""
        today = datetime.now(tz=timezone.utc)
        rts = today.strftime(r"%d%H%MZ")
        parsed = core.parse_date(rts)
        self.assertIsInstance(parsed, datetime)
        self.assertEqual(parsed.day, today.day)
        self.assertEqual(parsed.hour, today.hour)
        self.assertEqual(parsed.minute, today.minute)

    @time_machine.travel("2020-06-22 12:00")
    def test_midnight_rollover(self):
        """Tests that hour > 23 gets rolled into the next day"""
        parsed = core.parse_date("2224")
        self.assertIsInstance(parsed, datetime)
        self.assertEqual(parsed.day, 23)
        self.assertEqual(parsed.hour, 0)
        self.assertEqual(parsed.minute, 0)

    def test_make_timestamp(self):
        """Tests that a report timestamp is converted into a Timestamp dataclass"""
        for dt, fmt, target in (
            (datetime.now(tz=timezone.utc), r"%d%HZ", False),
            (datetime.now(tz=timezone.utc), r"%d%H%MZ", False),
            (datetime(2010, 2, 2, 2, 2, tzinfo=timezone.utc), r"%d%HZ", True),
            (datetime(2010, 2, 2, 2, 2, tzinfo=timezone.utc), r"%d%H%MZ", True),
        ):
            dt_repr = dt.strftime(fmt)
            target = dt.date() if target else None
            dt = dt.replace(second=0, microsecond=0)
            if "%M" not in fmt:
                dt = dt.replace(minute=0)
            ts = core.make_timestamp(dt_repr, target_date=target)
            self.assert_timestamp(ts, dt_repr, dt)

    def test_relative_humidity(self):
        """Tests calculating relative humidity from temperatrue and dewpoint"""
        for temperature, dewpoint, humidity in (
            (10, 5, 0.7107),
            (27, 24, 0.83662),
            (15, 0, 0.35868),
            (10, 10, 1.0),
        ):
            value = core.relative_humidity(temperature, dewpoint)
            self.assertEqual(round(value, 5), humidity)

    def test_pressure_altitude(self):
        """Tests calculating pressure altitude in feet"""
        for pressure, altitude, pressure_altitude in (
            (29.92, 0, 0),
            (30.12, 6400, 6200),
            (30.28, 12000, 11640),
            (29.78, 1200, 1340),
            (30.09, 0, -170),
        ):
            value = core.pressure_altitude(pressure, altitude)
            self.assertEqual(value, pressure_altitude)

    def test_density_altitude(self):
        """Tests calculating density altitude in feet"""
        units = Units(**NA_UNITS)
        for pressure, temperature, altitude, density in (
            (29.92, 15, 0, 0),
            (30.12, 10, 6400, 7136),
            (30.28, -10, 12000, 11520),
            (29.78, 18, 1200, 1988),
            (30.09, 31, 0, 1750),
            (30.02, 0, 0, -1900),
        ):
            value = core.density_altitude(pressure, temperature, altitude, units)
            self.assertEqual(value, density)
