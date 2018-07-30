"""
Michael duPont - michael@mdupont.com
tests/test_translate.py
"""

# library
import unittest
# module
from avwx import static, structs, translate

class TestShared(unittest.TestCase):

    def test_visibility(self):
        """
        Tests visibility translation and conversion
        """
        for vis, unit, translation in (
            ('', 'm', ''),
            ('0000', 'm', '0km (0sm)'),
            ('2000', 'm', '2km (1.2sm)'),
            ('0900', 'm', '0.9km (0.6sm)'),
            ('P6', 'sm', 'Greater than 6sm ( >10km )'),
            ('M1/4', 'sm', 'Less than .25sm ( <0.4km )'),
            ('3/4', 'sm', '0.75sm (1.2km)'),
            ('3/2', 'sm', '1.5sm (2.4km)'),
            ('3', 'sm', '3sm (4.8km)'),

        ):
            self.assertEqual(translate.visibility(vis, unit), translation)

    def test_altimeter(self):
        """
        Tests altimeter translation and conversion
        """
        for alt, unit, translation in (
            ('', 'hPa', ''),
            ('1020', 'hPa', '1020 hPa (30.12 inHg)'),
            ('0999', 'hPa', '0999 hPa (29.5 inHg)'),
            ('Q1012', 'hPa', '1012 hPa (29.88 inHg)'),
            ('A3000', 'inHg', '30.00 inHg (1016 hPa)'),
            ('2992', 'inHg', '29.92 inHg (1013 hPa)'),
            ('3005', 'inHg', '30.05 inHg (1018 hPa)'),
        ):
            self.assertEqual(translate.altimeter(alt, unit), translation)

    def test_clouds(self):
        """
        Tests translating each cloud into a single string
        """
        self.assertEqual(translate.clouds([]), 'Sky clear')
        for clouds, translation in (
            ([['BKN',''],['FEW','020']], 'Few clouds at 2000ft'),
            ([['OVC','030'],['SCT','100']], 'Overcast layer at 3000ft, Scattered clouds at 10000ft'),
            ([['BKN','015','CB']], 'Broken layer at 1500ft (Cumulonimbus)'),
        ):
            self.assertEqual(translate.clouds(clouds), translation + ' - Reported AGL')

    def test_wxcode(self):
        """
        Tests expenading weather codes or ignoring them
        """
        for code, translation in (
            ('', ''),
            ('R03/03002V03', 'R03/03002V03'),
            ('+RATS', 'Heavy Rain Thunderstorm'),
            ('VCFC', 'Vicinity Funnel Cloud'),
            ('-GR', 'Light Hail'),
            ('FZFG', 'Freezing Fog'),
            ('BCBLSN', 'Patchy Blowing Snow'),
        ):
            self.assertEqual(translate.wxcode(code), translation)

    def test_other_list(self):
        """
        Tests translating a list of weather codes into a single string
        """
        for codes, translation in (
            ([], ''),
            (['VCFC', '+RA'], 'Vicinity Funnel Cloud, Heavy Rain'),
            (['-SN'], 'Light Snow'),
        ):
            self.assertEqual(translate.other_list(codes), translation)

    def test_shared(self):
        """
        Tests availibility of shared values between the METAR and TAF translations
        """
        units = structs.Units(**static.NA_UNITS)
        data = structs.SharedData('2992',[['OVC', '060']],'',['RA'],'','10',0,0,0)
        trans = translate.shared(data, units)
        self.assertIsInstance(trans, dict)
        for key in ('altimeter', 'clouds', 'other', 'visibility'):
            self.assertIn(key, trans)
            self.assertTrue(bool(trans[key]))

class TestMetar(unittest.TestCase):

    def test_cardinal_direction(self):
        """
        Tests that a direction int returns the correct cardinal direction string
        """
        # 12 - 360+
        keys = (12, 34, 57, 79)
        for i, cardinal in enumerate([
            'NNE','NE','ENE','E','ESE','SE','SSE','S',
            'SSW','SW','WSW','W','WNW','NW','NNW','N'
        ]):
            lower = keys[i%4]+90*(i//4)
            upper = keys[0]+90*((i//4)+1)-1 if i%4==3 else keys[(i%4)+1]+90*(i//4)-1
            for direction in range(lower, upper+1):
                print(direction, cardinal)
                self.assertEqual(translate.get_cardinal_direction(direction), cardinal)
        # -0 - 11
        for direction in range(-10, 12):
            self.assertEqual(translate.get_cardinal_direction(direction), 'N')            

    def test_wind(self):
        """
        Tests that wind values are translating into a single string
        """
        for *wind, translation in (
            ('', '', '', None, ''),
            ('360', '12', '20', ['340', '020'], 'N-360 (variable 340 to 020) at 12kt gusting to 20kt'),
            ('000', '00', '', None, 'Calm'),
            ('VRB', '5', '12', None, 'Variable at 5kt gusting to 12kt'),
            ('270', '10', '', ['240', '300'], 'W-270 (variable 240 to 300) at 10kt'),
        ):
            self.assertEqual(translate.wind(*wind), translation)

    def test_temperature(self):
        """
        Tests temperature translation and conversion
        """
        for temp, unit, translation in (
            ('20', 'F', '20°F (-7°C)'),
            ('M20', 'F', '-20°F (-29°C)'),
            ('20', 'C', '20°C (68°F)'),
            ('M20', 'C', '-20°C (-4°F)'),
            ('', 'F', ''),
        ):
            self.assertEqual(translate.temperature(temp, unit), translation)

    def test_metar(self):
        """
        Tests end-to-end METAR translation
        """
        units = structs.Units(**static.NA_UNITS)
        data = {
            'altimeter': '2992',
            'clouds': [['BKN','015','CB']],
            'dewpoint': 'M01',
            'other': ['+RA'],
            'temperature': '03',
            'visibility': '3',
            'wind_direction': '360',
            'wind_gust': '20',
            'wind_speed': '12',
            'wind_variable_direction': ['340', '020']
        }
        data.update({k: '' for k in (
            'raw', 'remarks', 'station', 'time', 'flight_rules',
            'remarks_info', 'runway_visibility', 'sanitized'
        )})
        data = structs.MetarData(**data)
        trans = structs.MetarTrans(
            altimeter='29.92 inHg (1013 hPa)',
            clouds='Broken layer at 1500ft (Cumulonimbus) - Reported AGL',
            dewpoint='-1°C (30°F)',
            other='Heavy Rain',
            remarks={},
            temperature='3°C (37°F)',
            visibility='3sm (4.8km)',
            wind='N-360 (variable 340 to 020) at 12kt gusting to 20kt'
        )
        translated = translate.metar(data, units)
        self.assertIsInstance(translated, structs.MetarTrans)
        self.assertEqual(translated, trans)

class TestTaf(unittest.TestCase):

    def test_wind_shear(self):
        """
        Tests wind shear unpacking and translation
        """
        for shear, translation in (
            ('', ''),
            ('WS020/07040KT', 'Wind shear 2000ft from 070 at 40kt'),
            ('WS100/20020KT', 'Wind shear 10000ft from 200 at 20kt')
        ):
            self.assertEqual(translate.wind_shear(shear), translation)

    def test_turb_ice(self):
        """
        Tests turbulance and icing translations
        """
        for turbice, translation in (
            ([], ''),
            (['540553'], 'Occasional moderate turbulence in clouds from 5500ft to 8500ft'),
            (['611005'], 'Light icing from 10000ft to 15000ft'),
            (['610023', '610062'], 'Light icing from 200ft to 3200ft, Light icing from 600ft to 2600ft'),
        ):
            self.assertEqual(translate.turb_ice(turbice), translation)

    def test_min_max_temp(self):
        """
        Tests temperature time translation and conversion
        """
        for temp, translation in (
            ('', ''),
            ('TX20/1518Z', 'Maximum temperature of 20°C (68°F) at 15-18:00Z'),
            ('TXM02/04', 'Maximum temperature of -2°C (28°F) at 04:00Z'),
            ('TN00/00', 'Minimum temperature of 0°C (32°F) at 00:00Z'),
        ):
            self.assertEqual(translate.min_max_temp(temp), translation)

    def test_taf(self):
        """
        Tests end-to-end TAF translation
        """
        units = structs.Units(**static.NA_UNITS)
        line_data = {
            'altimeter': '2992',
            'clouds': [['BKN','015','CB']],
            'icing': ['611005'],
            'other': ['+RA'],
            'turbulance': ['540553'],
            'visibility': '3',
            'wind_direction': '360',
            'wind_gust': '20',
            'wind_shear': 'WS020/07040KT',
            'wind_speed': '12'
        }
        line_data.update({k: '' for k in (
            'raw', 'end_time', 'start_time', 'probability',
            'type', 'flight_rules', 'sanitized'
        )})
        data = {
            'max_temp': 'TX20/1518Z',
            'min_temp': 'TN00/00',
            'remarks': ''
        }
        data.update({k: '' for k in ('raw', 'station', 'time', 'start_time', 'end_time')})
        data = structs.TafData(forecast=[structs.TafLineData(**line_data)], **data)
        line_trans = structs.TafLineTrans(
            altimeter='29.92 inHg (1013 hPa)',
            clouds='Broken layer at 1500ft (Cumulonimbus) - Reported AGL',
            icing='Light icing from 10000ft to 15000ft',
            other='Heavy Rain',
            turbulance='Occasional moderate turbulence in clouds from 5500ft to 8500ft',
            visibility='3sm (4.8km)',
            wind_shear='Wind shear 2000ft from 070 at 40kt',
            wind='N-360 at 12kt gusting to 20kt'
        )
        trans = structs.TafTrans(
            forecast=[line_trans],
            max_temp='Maximum temperature of 20°C (68°F) at 15-18:00Z',
            min_temp='Minimum temperature of 0°C (32°F) at 00:00Z',
            remarks={}
        )
        translated = translate.taf(data, units)
        self.assertIsInstance(translated, structs.TafTrans)
        for line in translated.forecast:
            self.assertIsInstance(line, structs.TafLineTrans)
        self.assertEqual(translated, trans)
