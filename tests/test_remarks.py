"""
Michael duPont - michael@mdupont.com
tests/test_remarks.py
"""

# library
import unittest
# module
from avwx import core, remarks, static, structs

class TestRemarks(unittest.TestCase):

    def test_tdec(self):
        """
        Tests that a 4-digit number gets decoded into a readable temperature
        """
        for code, temp in (
            ('1045', '-4.5°C'),
            ('0237', '23.7°C'),
            ('0987', '98.7°C'),
        ):
            self.assertEqual(remarks._tdec(code), temp)

    def test_temp_minmax(self):
        """
        Tests the minimum and maximum temperature translation string
        """
        for code, ttype, temp in (
            ('21045', 'minimum', '-4.5°C'),
            ('10237', 'maximum', '23.7°C'),
            ('10987', 'maximum', '98.7°C'),
        ):
            equals = f'6-hour {ttype} temperature {temp}'
            self.assertEqual(remarks.temp_minmax(code), equals)

    def test_pressure_tendency(self):
        """
        Tests translating the pressure tendency code
        """
        for code, pressure in (
            ('50123', '12.3'),
            ('54987', '98.7'),
            ('51846', '84.6'),
        ):
            equals = ('3-hour pressure difference: +/- '
                f'{pressure} mb - {static.PRESSURE_TENDENCIES[code[1]]}')
            self.assertEqual(remarks.pressure_tendency(code), equals)

    def test_precip_36(self):
        """
        Tests translating the three and six hour precipitation code
        """
        for code, three, six in (
            ('60720', 7, 20),
            ('60000', 0, 0),
            ('60104', 1, 4),
        ):
            equals = f'Precipitation in the last 3 hours: {three} in. - 6 hours: {six} in.'
            self.assertEqual(remarks.precip_36(code), equals)

    def test_precip_24(self):
        """
        Tests translating the 24-hour precipitation code
        """
        for code, precip in (
            ('70016', 16),
            ('79999', 9999),
            ('70000', 0),
        ):
            equals = f'Precipitation in the last 24 hours: {precip} in.'
            self.assertEqual(remarks.precip_24(code), equals)

    def test_sunshine_duration(self):
        """
        Tests translating the sunshine duration code
        """
        for code, minutes in (
            ('90000', 0),
            ('99999', 9999),
            ('91234', 1234),
        ):
            equals = f'Duration of sunlight: {minutes} minutes'
            self.assertEqual(remarks.sunshine_duration(code), equals)

    def test_parse(self):
        """
        Tests generating RemarksData from a remarks string
        """
        for rmk, data in (
            ('', (None, None)),
            ('T09870123', ('12.3', '98.7')),
            ('RMK AO2 SLP141 T02670189 $', ('18.9', '26.7')),
        ):
            data = [core.make_number(d) for d in data]
            self.assertEqual(remarks.parse(rmk), structs.RemarksData(*data))

    def test_translate(self):
        """
        Tests extracting translations from the remarks string
        """
        for rmk, out in (
            ('RMK AO1 ACFT MSHP SLP137 T02720183 BINOVC', {
                'ACFT MSHP': 'Aircraft mishap',
                'AO1': 'Automated with no precipitation sensor',
                'BINOVC': 'Breaks in Overcast',
                'SLP137': 'Sea level pressure: 1013.7 hPa',
                'T02720183': 'Temperature 27.2°C and dewpoint 18.3°C'
            }),
            ('RMK AO2 51014 21045 60720 70016', {
                '21045': '6-hour minimum temperature -4.5°C',
                '51014': '3-hour pressure difference: +/- 1.4 mb - Increasing, then steady',
                '60720': 'Precipitation in the last 3 hours: 7 in. - 6 hours: 20 in.',
                '70016': 'Precipitation in the last 24 hours: 16 in.',
                'AO2': 'Automated with precipitation sensor'
            }),
            ('RMK 91234 TSB20 P0123 NOSPECI $', {
                '$': 'ASOS requires maintenance',
                '91234': 'Duration of sunlight: 1234 minutes',
                'NOSPECI': 'No SPECI reports taken',
                'P0123': 'Hourly precipitation: 1.23 in.',
                'TSB20': 'Thunderstorm began at :20'
            }),
        ):
            self.assertEqual(remarks.translate(rmk), out)
        
