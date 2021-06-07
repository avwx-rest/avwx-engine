"""
Tests remarks elements parsing
"""

# stdlib
from typing import Optional, Union

# library
import unittest

# module
from avwx import structs
from avwx.parsing import remarks


class TestRemarks(unittest.TestCase):
    """Tests remarks elements parsing"""

    def assertValueEquals(
        self, number: Optional[structs.Number], value: Union[None, int, float]
    ):
        """Asserts that the .value matches or both are None"""
        if number is None:
            self.assertIsNone(value)
        else:
            self.assertEqual(number.value, value)

    def test_decimal_code(self):
        """Tests that a 4-digit number gets decoded into a temperature number"""
        for code, temp in (("1045", -4.5), ("0237", 23.7), ("0987", 98.7)):
            self.assertEqual(remarks.decimal_code(code).value, temp)

    def test_temp_dew_decimal(self):
        """Tests extracting temperature and dewpoint decimal values"""
        for codes, temperature, dewpoint in (
            (["123"], None, None),
            (["123", "T01231234"], 12.3, -23.4),
        ):
            codes, temp, dew = remarks.temp_dew_decimal(codes)
            self.assertEqual(codes, ["123"])
            self.assertValueEquals(temp, temperature)
            self.assertValueEquals(dew, dewpoint)

    def test_temp_minmax(self):
        """Tests extracting 24-hour min max temperatures"""
        for codes, maximum, minimum in (
            (["123"], None, None),
            (["123", "401231432"], 12.3, -43.2),
        ):
            codes, tmax, tmin = remarks.temp_minmax(codes)
            self.assertEqual(codes, ["123"])
            self.assertValueEquals(tmax, maximum)
            self.assertValueEquals(tmin, minimum)

    def test_precip_snow(self):
        """Tests extracting hourly precipitation and snow accumulation"""
        for codes, precipitation, snowlevel in (
            (["123"], None, None),
            (["123", "P1234"], 12.34, None),
            (["123", "4/123"], None, 123),
            (["123", "P0987", "4/098"], 9.87, 98),
        ):
            codes, precip, snow = remarks.precip_snow(codes)
            self.assertEqual(codes, ["123"])
            self.assertValueEquals(precip, precipitation)
            self.assertValueEquals(snow, snowlevel)

    def test_sea_level_pressure(self):
        """Tests extracting the inferred sea level pressure in mb"""
        for codes, pressure in (
            (["123"], None),
            (["123", "SLP988"], 998.8),
            (["123", "SLP241"], 1024.1),
        ):
            codes, sea = remarks.sea_level_pressure(codes)
            self.assertEqual(codes, ["123"])
            self.assertValueEquals(sea, pressure)

            codes = ["123", "SLPNO"]
            new_codes, sea = remarks.sea_level_pressure(codes)
            self.assertEqual(codes, new_codes)
            self.assertIsNone(sea)

    def test_parse_pressure(self):
        """Tests parsing a 5-digit code to PressureTendency"""
        for code, value, text in (
            ("51234", 23.4, "Increasing, then steady"),
            ("54567", 56.7, "Steady"),
        ):
            pressure = remarks.parse_pressure(code)
            self.assertEqual(pressure, structs.PressureTendency(code, text, value))

    def test_parse_precipitation(self):
        """Tests parsing a 5-digit precipitation amount code"""
        for code, value in (
            ("61234", 12.34),
            ("70123", 1.23),
            ("70012", 0.12),
        ):
            self.assertValueEquals(remarks.parse_precipitation(code), value)

    def test_parse(self):
        """Tests full remarks parsing"""
        self.assertIsNone(remarks.parse(""))
        rmk = (
            "RMK 10123 21234 51234 61234 74321 98321 "
            "T01231234 403451567 P1234 4/123 SLP998 "
            "ACFT MSHP TSB20 AO2 $"
        )
        data = remarks.parse(rmk)
        # 5-digit codes
        self.assertValueEquals(data.maximum_temperature_6, 12.3)
        self.assertValueEquals(data.minimum_temperature_6, -23.4)
        pressure = structs.PressureTendency("51234", "Increasing, then steady", 23.4)
        self.assertEqual(data.pressure_tendency, pressure)
        self.assertValueEquals(data.precip_36_hours, 12.34)
        self.assertValueEquals(data.precip_24_hours, 43.21)
        self.assertValueEquals(data.sunshine_minutes, 321)
        # Other parsed data
        self.assertValueEquals(data.temperature_decimal, 12.3)
        self.assertValueEquals(data.dewpoint_decimal, -23.4)
        self.assertValueEquals(data.maximum_temperature_24, 34.5)
        self.assertValueEquals(data.minimum_temperature_24, -56.7)
        self.assertValueEquals(data.precip_hourly, 12.34)
        self.assertValueEquals(data.snow_depth, 123)
        self.assertValueEquals(data.sea_level_pressure, 999.8)
        # Static codes
        static_codes = [
            structs.Code("$", "ASOS requires maintenance"),
            structs.Code("ACFT MSHP", "Aircraft mishap"),
            structs.Code("AO2", "Automated with precipitation sensor"),
            structs.Code("TSB20", "Thunderstorm began at :20"),
        ]
        self.assertEqual(data.codes, static_codes)
