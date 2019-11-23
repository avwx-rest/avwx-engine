"""
Michael duPont - michael@mdupont.com
tests/test_speech.py
"""

# library
import unittest

# module
from avwx import _core, speech, static, structs


class TestSpeech(unittest.TestCase):
    def test_wind(self):
        """
        Tests converting wind data into a spoken string
        """
        for *wind, vardir, spoken in (
            ("", "", "", None, "unknown"),
            (
                "360",
                "12",
                "20",
                ["340", "020"],
                "three six zero (variable three four zero to zero two zero) at 12kt gusting to 20kt",
            ),
            ("000", "00", "", None, "Calm"),
            ("VRB", "5", "12", None, "Variable at 5kt gusting to 12kt"),
            (
                "270",
                "10",
                "",
                ["240", "300"],
                "two seven zero (variable two four zero to three zero zero) at 10kt",
            ),
        ):
            wind = [_core.make_number(i) for i in wind]
            if vardir:
                vardir = [_core.make_number(i, speak=i) for i in vardir]
            self.assertEqual(speech.wind(*wind, vardir), "Winds " + spoken)

    def test_temperature(self):
        """
        Tests converting a temperature into a spoken string
        """
        for temp, unit, spoken in (
            ("", "F", "unknown"),
            ("20", "F", "two zero degrees Fahrenheit"),
            ("M20", "F", "minus two zero degrees Fahrenheit"),
            ("20", "C", "two zero degrees Celsius"),
            ("1", "C", "one degree Celsius"),
        ):
            self.assertEqual(
                speech.temperature("Temp", _core.make_number(temp), unit),
                "Temp " + spoken,
            )

    def test_visibility(self):
        """
        Tests converting visibility distance into a spoken string
        """
        for vis, unit, spoken in (
            ("", "m", "unknown"),
            ("0000", "m", "zero kilometers"),
            ("2000", "m", "two kilometers"),
            ("0900", "m", "point nine kilometers"),
            ("P6", "sm", "greater than six miles"),
            ("M1/4", "sm", "less than one quarter of a mile"),
            ("3/4", "sm", "three quarters of a mile"),
            ("3/2", "sm", "one and one half miles"),
            ("3", "sm", "three miles"),
        ):
            self.assertEqual(
                speech.visibility(_core.make_number(vis), unit), "Visibility " + spoken
            )

    def test_altimeter(self):
        """
        Tests converting altimeter reading into a spoken string
        """
        for alt, unit, spoken in (
            ("", "hPa", "unknown"),
            ("1020", "hPa", "one zero two zero"),
            ("0999", "hPa", "zero nine nine nine"),
            ("1012", "hPa", "one zero one two"),
            ("3000", "inHg", "three zero point zero zero"),
            ("2992", "inHg", "two nine point nine two"),
            ("3005", "inHg", "three zero point zero five"),
        ):
            self.assertEqual(
                speech.altimeter(_core.make_number(alt), unit), "Altimeter " + spoken
            )

    def test_other(self):
        """
        Tests converting wxcodes into a spoken string
        """
        for code, spoken in (
            ([], ""),
            (["R03/03002V03"], "R03/03002V03"),
            (
                ["+RATS", "VCFC"],
                "Heavy Rain Thunderstorm. Funnel Cloud in the Vicinity",
            ),
            (
                ["-GR", "FZFG", "BCBLSN"],
                "Light Hail. Freezing Fog. Patchy Blowing Snow",
            ),
        ):
            self.assertEqual(speech.other(code), spoken)

    def test_metar(self):
        """
        Tests converting METAR data into into a single spoken string
        """
        units = structs.Units(**static.NA_UNITS)
        data = {
            "altimeter": _core.make_number("2992"),
            "clouds": [_core.make_cloud("BKN015CB")],
            "dewpoint": _core.make_number("M01"),
            "other": ["+RA"],
            "temperature": _core.make_number("03"),
            "visibility": _core.make_number("3"),
            "wind_direction": _core.make_number("360"),
            "wind_gust": _core.make_number("20"),
            "wind_speed": _core.make_number("12"),
            "wind_variable_direction": [
                _core.make_number("340"),
                _core.make_number("020", speak="020"),
            ],
        }
        data.update(
            {
                k: None
                for k in (
                    "raw",
                    "remarks",
                    "station",
                    "time",
                    "flight_rules",
                    "remarks_info",
                    "runway_visibility",
                    "sanitized",
                )
            }
        )
        data = structs.MetarData(**data)
        spoken = (
            "Winds three six zero (variable three four zero to zero two zero) "
            "at 12kt gusting to 20kt. Visibility three miles. "
            "Temperature three degrees Celsius. Dew point minus one degree Celsius. "
            "Altimeter two nine point nine two. Heavy Rain. "
            "Broken layer at 1500ft (Cumulonimbus)"
        )
        ret = speech.metar(data, units)
        self.assertIsInstance(ret, str)
        self.assertEqual(ret, spoken)

    def test_type_and_times(self):
        """
        Tests line start from type, time, and probability values
        """
        for type, *times, prob, spoken in (
            (None, None, None, None, ""),
            ("FROM", "2808", "2815", None, "From 8 to 15 zulu,"),
            ("FROM", "2822", "2903", None, "From 22 to 3 zulu,"),
            ("BECMG", "3010", None, None, "At 10 zulu becoming"),
            (
                "PROB",
                "1303",
                "1305",
                "30",
                r"From 3 to 5 zulu, there's a 30% chance for",
            ),
            (
                "INTER",
                "1303",
                "1305",
                "45",
                r"From 3 to 5 zulu, there's a 45% chance for intermittent",
            ),
            ("INTER", "2423", "2500", None, "From 23 to midnight zulu, intermittent"),
            ("TEMPO", "0102", "0103", None, "From 2 to 3 zulu, temporary"),
        ):
            times = [_core.make_timestamp(time) for time in times]
            if prob is not None:
                prob = _core.make_number(prob)
            ret = speech.type_and_times(type, *times, prob)
            self.assertIsInstance(ret, str)
            self.assertEqual(ret, spoken)

    def test_wind_shear(self):
        """
        Tests converting wind shear code into a spoken string
        """
        for shear, spoken in (
            ("", "Wind shear unknown"),
            ("WS020/07040KT", "Wind shear 2000ft from zero seven zero at 40kt"),
            ("WS100/20020KT", "Wind shear 10000ft from two zero zero at 20kt"),
        ):
            self.assertEqual(speech.wind_shear(shear), spoken)

    def test_taf_line(self):
        """
        Tests converting TAF line data into into a single spoken string
        """
        units = structs.Units(**static.NA_UNITS)
        line = {
            "altimeter": _core.make_number("2992"),
            "clouds": [_core.make_cloud("BKN015CB")],
            "end_time": _core.make_timestamp("1206"),
            "icing": ["611005"],
            "other": ["+RA"],
            "start_time": _core.make_timestamp("1202"),
            "turbulence": ["540553"],
            "type": "FROM",
            "visibility": _core.make_number("3"),
            "wind_direction": _core.make_number("360"),
            "wind_gust": _core.make_number("20"),
            "wind_shear": "WS020/07040KT",
            "wind_speed": _core.make_number("12"),
        }
        line.update(
            {k: None for k in ("flight_rules", "probability", "raw", "sanitized")}
        )
        line = structs.TafLineData(**line)
        spoken = (
            "From 2 to 6 zulu, Winds three six zero at 12kt gusting to 20kt. "
            "Wind shear 2000inHg from zero seven zero at 40kt. Visibility three miles. "
            "Altimeter two nine point nine two. Heavy Rain. "
            "Broken layer at 1500ft (Cumulonimbus). "
            "Occasional moderate turbulence in clouds from 5500ft to 8500ft. "
            "Light icing from 10000ft to 15000ft"
        )
        ret = speech.taf_line(line, units)
        self.assertIsInstance(ret, str)
        self.assertEqual(ret, spoken)

    def test_taf(self):
        """
        Tests converting a TafData report into a single spoken string
        """
        units = structs.Units(**static.NA_UNITS)
        empty_line = {k: None for k in structs.TafLineData.__dataclass_fields__.keys()}
        forecast = [
            structs.TafLineData(**{**empty_line, **line})
            for line in (
                {
                    "type": "FROM",
                    "start_time": _core.make_timestamp("0410Z"),
                    "end_time": _core.make_timestamp("0414Z"),
                    "visibility": _core.make_number("3"),
                    "wind_direction": _core.make_number("360"),
                    "wind_gust": _core.make_number("20"),
                    "wind_speed": _core.make_number("12"),
                },
                {
                    "type": "PROB",
                    "probability": _core.make_number("45"),
                    "start_time": _core.make_timestamp("0412Z"),
                    "end_time": _core.make_timestamp("0414Z"),
                    "visibility": _core.make_number("M1/4"),
                },
            )
        ]
        taf = structs.TafData(
            raw=None,
            remarks=None,
            station=None,
            time=None,
            forecast=forecast,
            start_time=_core.make_timestamp("0410Z"),
            end_time=_core.make_timestamp("0414Z"),
        )
        ret = speech.taf(taf, units)
        spoken = (
            f"Starting on {taf.start_time.dt.strftime('%B')} 4th - From 10 to 14 zulu, "
            "Winds three six zero at 12kt gusting to 20kt. Visibility three miles. "
            r"From 12 to 14 zulu, there's a 45% chance for Visibility "
            "less than one quarter of a mile"
        )
        self.assertIsInstance(ret, str)
        self.assertEqual(ret, spoken)
