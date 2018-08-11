"""
Michael duPont - michael@mdupont.com
tests/test_speech.py
"""

# library
import unittest
# module
from avwx import core, speech, static, structs

class TestSpeech(unittest.TestCase):

    def test_wind(self):
        """
        Tests converting wind data into a spoken string
        """
        for *wind, vardir, spoken in (
            ('', '', '', None, 'unknown'),
            ('360', '12', '20', ['340', '020'], 'three six zero (variable three four zero to zero two zero) at 12kt gusting to 20kt'),
            ('000', '00', '', None, 'Calm'),
            ('VRB', '5', '12', None, 'Variable at 5kt gusting to 12kt'),
            ('270', '10', '', ['240', '300'], 'two seven zero (variable two four zero to three zero zero) at 10kt'),
        ):
            wind = [core.make_number(i) for i in wind]
            if vardir:
                vardir = [core.make_number(i) for i in vardir]
            self.assertEqual(speech.wind(*wind, vardir), 'Winds ' + spoken)

    def test_temperature(self):
        """
        Tests converting a temperature into a spoken string
        """
        for temp, unit, spoken in (
            ('', 'F', 'unknown'),
            ('20', 'F', 'two zero degrees Fahrenheit'),
            ('M20', 'F', 'minus two zero degrees Fahrenheit'),
            ('20', 'C', 'two zero degrees Celsius'),
            ('1', 'C', 'one degree Celsius'),
        ):
            self.assertEqual(speech.temperature('Temp', core.make_number(temp), unit), 'Temp ' + spoken)

    def test_visibility(self):
        """
        Tests converting visibility distance into a spoken string
        """
        for vis, unit, spoken in (
            ('', 'm', 'unknown'),
            ('0000', 'm', 'zero kilometers'),
            ('2000', 'm', 'two kilometers'),
            ('0900', 'm', 'point nine kilometers'),
            ('P6', 'sm', 'greater than six miles'),
            ('M1/4', 'sm', 'less than one quarter of a mile'),
            ('3/4', 'sm', 'three quarters of a mile'),
            ('3/2', 'sm', 'one and one half miles'),
            ('3', 'sm', 'three miles'),
        ):
            self.assertEqual(speech.visibility(core.make_number(vis), unit), 'Visibility ' + spoken)

    def test_altimeter(self):
        """
        Tests converting altimeter reading into a spoken string
        """
        for alt, unit, spoken in (
            ('', 'hPa', 'unknown'),
            ('1020', 'hPa', 'one zero two zero'),
            ('0999', 'hPa', 'zero nine nine nine'),
            ('1012', 'hPa', 'one zero one two'),
            ('3000', 'inHg', 'three zero point zero zero'),
            ('2992', 'inHg', 'two nine point nine two'),
            ('3005', 'inHg', 'three zero point zero five'),
        ):
            self.assertEqual(speech.altimeter(core.make_number(alt), unit), 'Altimeter ' + spoken)

    def test_other(self):
        """
        Tests converting wxcodes into a spoken string
        """
        for code, spoken in (
            ([], ''),
            (['R03/03002V03'], 'R03/03002V03'),
            (['+RATS', 'VCFC'], 'Heavy Rain Thunderstorm. Funnel Cloud in the Vicinity'),
            (['-GR', 'FZFG', 'BCBLSN'], 'Light Hail. Freezing Fog. Patchy Blowing Snow'),
        ):
            self.assertEqual(speech.other(code), spoken)

    def test_metar(self):
        """
        Tests converting METAR data into into a single spoken string
        """
        units = structs.Units(**static.NA_UNITS)
        data = {
            'altimeter': core.make_number('2992'),
            'clouds': [core.make_cloud('BKN015CB')],
            'dewpoint': core.make_number('M01'),
            'other': ['+RA'],
            'temperature': core.make_number('03'),
            'visibility': core.make_number('3'),
            'wind_direction': core.make_number('360'),
            'wind_gust': core.make_number('20'),
            'wind_speed': core.make_number('12'),
            'wind_variable_direction': [
                core.make_number('340'),
                core.make_number('020')
            ]
        }
        data.update({k: '' for k in (
            'raw', 'remarks', 'station', 'time', 'flight_rules',
            'remarks_info', 'runway_visibility', 'sanitized'
        )})
        data = structs.MetarData(**data)
        spoken = ('Winds three six zero (variable three four zero to zero two zero) '
                  'at 12kt gusting to 20kt. Visibility three miles. '
                  'Temperature three degrees Celsius. Dew point minus one degree Celsius. '
                  'Altimeter two nine point nine two. Heavy Rain. '
                  'Broken layer at 1500ft (Cumulonimbus)')
        ret = speech.metar(data, units)
        self.assertIsInstance(ret, str)
        self.assertEqual(ret, spoken)
