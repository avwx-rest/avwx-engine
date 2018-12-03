"""
Michael duPont - michael@mdupont.com
tests/test_core.py
"""

# pylint: disable=E1101,C0103

# stdlib
from copy import deepcopy
from datetime import datetime, timedelta
# library
import unittest
# module
from avwx import core, exceptions, static, structs

class BaseTest(unittest.TestCase):

    def assert_number(self, num: structs.Number, repr: str, value: object = None, spoken: str = None):
        """
        Tests string conversion into a Number dataclass
        """
        if not repr:
            self.assertIsNone(num)
        else:
            self.assertIsInstance(num, structs.Number)
            self.assertEqual(num.repr, repr)
            self.assertEqual(num.value, value)
            if spoken:
                self.assertEqual(num.spoken, spoken)

class TestGlobal(BaseTest):

    def test_valid_station(self):
        """
        While not designed to catch all non-existant station idents,
        valid_station should catch non-ICAO strings and filter based on known prefixes
        """
        # Good stations
        for station in ('KJFK', 'K123', 'EIGL', 'PHNL', 'MNAH'):
            core.valid_station(station)
        # Bad stations
        for station in ('12K', 'MAYT'):
            with self.assertRaises(exceptions.BadStation):
                core.valid_station(station)

    def test_uses_na_format(self):
        """
        METAR and TAF reports come in two flavors: North American and International
        
        uses_na_format should determine the format based on the station ident using prefixes
        """
        # NA stations
        for station in ('KJFK', 'PHNL', 'TNCM', 'MYNN'):
            self.assertTrue(core.uses_na_format(station))
        # IN stations
        for station in ('EGLL', 'MNAH', 'MUHA'):
            self.assertFalse(core.uses_na_format(station))
        # Bad stations
        for station in ('12K', 'MAYT'):
            with self.assertRaises(exceptions.BadStation):
                core.uses_na_format(station)

    def test_is_unknown(self):
        """
        Tests unknown value when a string value contains only backspace characters or empty
        """
        # Unknown values
        for i in range(10):
            self.assertTrue(core.is_unknown('/' * i))
        # Full or partially known values
        for value in ('abc', '/bc', 'a/c', 'ab/', 'a//', '/b/', '//c'):
            self.assertFalse(core.is_unknown(value))
        # Bad type
        with self.assertRaises(TypeError):
            core.is_unknown(None)

    def test_unpack_fraction(self):
        """
        Tests unpacking a fraction where the numerator can be greater than the denominator
        """
        for fraction, unpacked in (
            ('', ''),
            ('1', '1'),
            ('1/2', '1/2'),
            ('3/2', '1 1/2'),
            ('10/3', '3 1/3'),
        ):
            self.assertEqual(core.unpack_fraction(fraction), unpacked)

    def test_remove_leading_zeros(self):
        """
        Tests removing leading zeros from a number
        """
        for num, stripped in (
            ('', ''),
            ('5', '5'),
            ('010', '10'),
            ('M10', 'M10'),
            ('M002', 'M2'),
            ('-09.9', '-9.9'),
            ('000', '0'),
            ('M00', '0'),
        ):
            self.assertEqual(core.remove_leading_zeros(num), stripped)

    def test_spoken_number(self):
        """
        Tests converting digits into spoken values
        """
        for num, spoken in (
            ('1', 'one'),
            ('5', 'five'),
            ('20', 'two zero'),
            ('937', 'nine three seven'),
            ('4.8', 'four point eight'),
            ('29.92', 'two nine point nine two'),
            ('1/2', 'one half'),
            ('3 3/4', 'three and three quarters'),
        ):
            self.assertEqual(core.spoken_number(num), spoken)

    def test_make_number(self):
        """
        Tests Number dataclass generation from a number string
        """
        self.assertIsNone(core.make_number(''))
        for num, value, spoken in (
            ('1', 1, 'one'),
            ('1.5', 1.5, 'one point five'),
            ('060', 60, 'six zero'),
            ('M10', -10, 'minus one zero'),
            ('P6SM', None, 'greater than six'),
            ('M1/4', None, 'less than one quarter'),
        ):
            number = core.make_number(num)
            self.assertEqual(number.repr, num)
            self.assertEqual(number.value, value)
            self.assertEqual(number.spoken, spoken)
        for num, value, spoken, nmr, dnm, norm in (
            ('1/4', 0.25, 'one quarter', 1, 4, '1/4'),
            ('5/2', 2.5, 'two and one half', 5, 2, '2 1/2'),
            ('3/4', 0.75, 'three quarters', 3, 4, '3/4'),
        ):
            number = core.make_number(num)
            self.assertEqual(number.value, value)
            self.assertEqual(number.spoken, spoken)
            self.assertEqual(number.numerator, nmr)
            self.assertEqual(number.denominator, dnm)
            self.assertEqual(number.normalized, norm)
        self.assertEqual(core.make_number('1234', 'A1234').repr, 'A1234')
        number = core.make_number('040', speak='040')
        self.assertEqual(number.value, 40)
        self.assertEqual(number.spoken, 'zero four zero')

    def test_find_first_in_list(self):
        """
        Tests a function which finds the first occurence in a string from a list

        This is used to find remarks and TAF time periods
        """
        for string, targets, index in (
            ('012345', ('5', '2', '3'), 2),
            ('This is weird', ('me', 'you', 'we'), 8),
            ('KJFK NOPE LOL RMK HAHAHA', static.METAR_RMK, 13)
        ):
            self.assertEqual(core.find_first_in_list(string, targets), index)

    def test_extra_space_exists(self):
        """
        Tests whether a space should exist between two elements
        """
        for strings in (
            ('10', 'SM'),
            ('1', '0SM'),
            ('12', '/10'),
            ('12/', '10'),
            ('12/1', '0'),
            ('OVC', '040'),
            ('Q', '1001'),
            ('A', '2992'),
            ('36010G20', 'KT'),
            ('VRB10', 'KT'),
            ('36010G20K', 'T'),
            ('VRB10K', 'T'),
            ('OVC022', 'CB'),
            ('FM', '122400'),
            ('TL', '123456Z'),
            ('TX', '10/20'),
            ('TN', '05/10')
        ):
            self.assertTrue(core.extra_space_exists(*strings))
        for strings in (
            ('OVC020', 'FEW'),
            ('BKN020', 'SCT040'),
            ('Q', '12/34'),
            ('OVC', '12/34'),
        ):
            self.assertFalse(core.extra_space_exists(*strings))

    def test_sanitize_report_list(self):
        """
        Tests a function which fixes common mistakes while the report is a list
        """
        for line, fixed in (
            ('KJFK AUTO 123456Z ////// KT 10SM 20/10', 'KJFK 123456Z 10SM 20/10'),
            ('METAR EGLL CALM RETS 6SPM CLR Q 1000', 'EGLL 00000KT TS P6SM Q1000'),
        ):
            line, fixed = line.split(), fixed.split()
            self.assertEqual(core.sanitize_report_list(line), (fixed, [], ''))
        # Test extracting runway visibility and wind shear
        line = 'EGLL 12345 KT R10/10 RETS WS020/07040KT 6SPM'.split()
        fixed = 'EGLL 12345KT TS P6SM'.split()
        self.assertEqual(core.sanitize_report_list(line), (fixed, ['R10/10'], 'WS020/07040'))

    def test_is_possible_temp(self):
        """
        Tests if an element could be a formatted temperature
        """
        for is_temp in ('10', '22', '333', 'M05', '5'):
            self.assertTrue(core.is_possible_temp(is_temp))
        for not_temp in ('A', '12.3', 'MNA', '-13'):
            self.assertFalse(core.is_possible_temp(not_temp))

    def test_get_temp_and_dew(self):
        """
        Tests temperature and dewpoint extraction
        """
        for wx, temp, dew in (
            (['1', '2'], (None,), (None,)),
            (['1', '2', '07/05'], ('07', 7), ('05', 5)),
            (['07/05', '1', '2'], ('07', 7), ('05', 5)),
            (['M05/M10', '1', '2'], ('M05', -5), ('M10', -10)),
            (['///20', '1', '2'], (None,), ('20', 20)),
            (['10///', '1', '2'], ('10', 10), (None,)),
            (['/////', '1', '2'], (None,), (None,)),
            (['XX/01', '1', '2'], (None,), ('01', 1)),
        ):
            retwx, ret_temp, ret_dew = core.get_temp_and_dew(wx)
            self.assertEqual(retwx, ['1', '2'])
            self.assert_number(ret_temp, *temp)
            self.assert_number(ret_dew, *dew)
        self.assertEqual(core.get_temp_and_dew(['MX/01']), (['MX/01'], None, None))

    def test_get_station_and_time(self):
        """
        Tests removal of station (first item) and potential timestamp
        """
        for wx, ret, station, time,  in (
            (['KJFK', '123456Z', '1'], ['1'], 'KJFK', '123456Z'),
            (['KJFK', '123456', '1'], ['1'], 'KJFK', '123456Z'),
            (['KJFK', '1234Z', '1'], ['1'], 'KJFK', '1234Z'),
            (['KJFK', '1234', '1'], ['1234', '1'], 'KJFK', ''),
            (['KJFK', '1'], ['1'], 'KJFK', '')
        ):
            self.assertEqual(core.get_station_and_time(wx), (ret, station, time))

    def test_get_wind(self):
        """
        Tests that the wind item gets removed and split into its components
        """
        #Both us knots as the default unit, so just test North American default
        for wx, unit, *wind, varv  in (
            (['1'], 'kt', (None,), (None,), (None,), []),
            (['12345(E)', 'G50', '1'], 'kt', ('123', 123), ('45', 45), ('50', 50), []),
            (['O1234G56', '1'], 'kt', ('012', 12), ('34', 34), ('56', 56), []),
            (['36010KTS', 'G20', '300V060', '1'], 'kt', ('360', 360), ('10', 10), ('20', 20), [('300', 300), ('060', 60)]),
            (['VRB10MPS', '1'], 'm/s', ('VRB',), ('10', 10), (None,), []),
            (['VRB20G30KMH', '1'], 'km/h', ('VRB',), ('20', 20), ('30', 30), [])
        ):
            units = structs.Units(**static.NA_UNITS)
            wx, *winds, var = core.get_wind(wx, units)
            self.assertEqual(wx, ['1'])
            for i in range(len(wind)):
                self.assert_number(winds[i], *wind[i])
            if varv:
                self.assertIsInstance(varv, list)
                for i in range(2):
                    self.assert_number(var[i], *varv[i])
            self.assertEqual(units.wind_speed, unit)

    def test_get_visibility(self):
        """
        Tests that the visibility item(s) gets removed and cleaned
        """
        for wx, unit, visibility in (
            (['1'], 'sm', (None,)),
            (['05SM', '1'], 'sm', ('5', 5)),
            (['10SM', '1'], 'sm', ('10', 10)),
            (['P6SM', '1'], 'sm', ('P6',)),
            (['M1/4SM', '1'], 'sm', ('M1/4',)),
            (['1/2SM', '1'], 'sm', ('1/2', 0.5)),
            (['2', '1/2SM', '1'], 'sm', ('5/2', 2.5)),
            (['1000', '1'], 'm', ('1000', 1000)),
            (['1000E', '1'], 'm', ('1000', 1000)),
            (['1000NDV', '1'], 'm', ('1000', 1000)),
            (['M1000', '1'], 'm', ('1000', 1000)),
            (['2KM', '1'], 'm', ('2000', 2000)),
        ):
            units = structs.Units(**static.NA_UNITS)
            wx, vis = core.get_visibility(wx, units)
            self.assertEqual(wx, ['1'])
            self.assert_number(vis, *visibility)
            self.assertEqual(units.visibility, unit)

    def test_get_digit_list(self):
        """
        Tests that digits are removed after an index but before a non-digit item
        """
        items = ['1', 'T', '2', '3', 'ODD', 'Q', '4', 'C']
        items, ret = core._get_digit_list(items, 1)
        self.assertEqual(items, ['1', 'ODD', 'Q', '4', 'C'])
        self.assertEqual(ret, ['2', '3'])
        items, ret = core._get_digit_list(items, 2)
        self.assertEqual(items, ['1', 'ODD','C'])
        self.assertEqual(ret, ['4'])

    def test_sanitize_cloud(self):
        """
        Tests the common cloud issues are fixed before parsing
        """
        for bad, good in (
            ('OVC', 'OVC'),
            ('010', '010'),
            ('SCT060', 'SCT060'),
            ('FEWO03', 'FEW003'),
            ('BKNC015', 'BKN015C'),
            ('FEW027///', 'FEW027///'),
        ):
            self.assertEqual(core.sanitize_cloud(bad), good)

    def test_split_cloud(self):
        """
        Tests that cloud strings and fixed and split into their two or three elements
        """
        for cloud, out in (
            ('SCT060', ['SCT', 60]),
            ('FEWO03', ['FEW', 3]),
            ('BKNC015', ['BKN', 15, 'C']),
            ('OVC120TS', ['OVC', 120, 'TS']),
            ('VV002', ['VV', 2]),
            ('SCT', ['SCT', None]),
            ('FEW027///', ['FEW', 27, None]),
        ):
            self.assertEqual(core.split_cloud(cloud), out)

    def test_make_cloud(self):
        """
        Tests helper function which returns a Cloud dataclass
        """
        for cloud, out in (
            ('SCT060', ['SCT', 60, None]),
            ('FEWO03', ['FEW', 3, None]),
            ('BKNC015', ['BKN', 15, 'C']),
            ('OVC120TS', ['OVC', 120, 'TS']),
            ('VV002', ['VV', 2, None]),
            ('SCT', ['SCT', None, None]),
            ('FEW027///', ['FEW', 27, None]),
            ('FEW//////', ['FEW', None, None]),
            ('FEW///TS', ['FEW', None, 'TS']),
        ):
            ret_cloud = core.make_cloud(cloud)
            self.assertIsInstance(ret_cloud, structs.Cloud)
            self.assertEqual(ret_cloud.repr, cloud)
            for i, key in enumerate(('type', 'altitude', 'modifier')):
                self.assertEqual(getattr(ret_cloud, key), out[i])

    def test_get_clouds(self):
        """
        Tests that clouds are removed, fixed, and split correctly
        """
        for wx, clouds in (
            (['1'], []),
            (['SCT060','1'], [['SCT',60,None]]),
            (['OVC100','1','VV010','SCTO50C'], [['VV',10,None],['SCT',50,'C'],['OVC',100,None]]),
            (['1','BKN020','SCT050'], [['BKN',20,None],['SCT',50,None]]),
        ):
            wx, ret_clouds = core.get_clouds(wx)
            self.assertEqual(wx, ['1'])
            for i, cloud in enumerate(ret_clouds):
                self.assertIsInstance(cloud, structs.Cloud)
                for j, key in enumerate(('type', 'altitude', 'modifier')):
                    self.assertEqual(getattr(cloud, key), clouds[i][j])

    def test_get_flight_rules(self):
        """
        Tests that the proper flight rule is calculated for a set visibility and ceiling

        Note: Only 'Broken', 'Overcast', and 'Vertical Visibility' are considdered ceilings
        """
        for vis, ceiling, rule in (
            (None, None, 'IFR'),
            ('10', None, 'VFR'),
            ('P6SM', ['OCV',50], 'VFR'),
            ('6', ['OVC',20], 'MVFR'),
            ('6', ['OVC',7], 'IFR'),
            ('2', ['OVC',20], 'IFR'),
            ('6', ['OVC',4], 'LIFR'),
            ('1/2', ['OVC',30], 'LIFR'),
            ('M1/4', ['OVC',30], 'LIFR'),
        ):
            vis = core.make_number(vis)
            if ceiling:
                ceiling = structs.Cloud(None, *ceiling)
            self.assertEqual(static.FLIGHT_RULES[core.get_flight_rules(vis, ceiling)], rule)

    def test_get_ceiling(self):
        """
        Tests that the ceiling is properly identified from a list of clouds
        """
        for clouds, ceiling in (
            ([], None),
            ([['FEW', 10], ['SCT', 10]], None),
            ([['OVC', None]], None),
            ([['VV', 5]], ['VV', 5]),
            ([['OVC', 20], ['BKN', 30]], ['OVC', 20]),
            ([['OVC', None], ['BKN', 30]], ['BKN', 30]),
            ([['FEW', 10], ['OVC', 20]], ['OVC', 20]),
        ):
            clouds = [structs.Cloud(None, *cloud) for cloud in clouds]
            if ceiling:
                ceiling = structs.Cloud(None, *ceiling)
            self.assertEqual(core.get_ceiling(clouds), ceiling)

    def test_parse_date(self):
        """
        Tests that report timestamp is parsed into a datetime object
        """
        today = datetime.utcnow()
        rts = today.strftime(r'%d%H%MZ')
        parsed = core.parse_date(rts)
        self.assertIsInstance(parsed, datetime)
        self.assertEqual(parsed.day, today.day)
        self.assertEqual(parsed.hour, today.hour)
        self.assertEqual(parsed.minute, today.minute)

    def test_make_timestamp(self):
        """
        Tests that a report timestamp is converted into a Timestamp dataclass
        """
        today = datetime.utcnow()
        rts = today.strftime(r'%d%HZ')
        date = core.make_timestamp(rts)
        self.assertIsInstance(date, structs.Timestamp)
        self.assertEqual(date.repr, rts)
        self.assertEqual(date.dt.day, today.day)
        self.assertEqual(date.dt.hour, today.hour)

class TestMetar(BaseTest):

    def test_get_remarks(self):
        """
        Remarks get removed first with the remaining components split into a list
        """
        for raw, wx, rmk in (
            ('1 2 3 A2992 RMK Hi', ['1', '2', '3', 'A2992'], 'RMK Hi'),
            ('1 2 3 A2992 Hi', ['1', '2', '3', 'A2992'], 'Hi'),
            ('1 2 Q0900 NOSIG', ['1', '2', 'Q0900'], 'NOSIG'),
            ('1 2 3 BLU+ Hello', ['1', '2', '3'], 'BLU+ Hello')
        ):
            testwx, testrmk = core.get_remarks(raw)
            self.assertEqual(wx, testwx)
            self.assertEqual(rmk, testrmk)

    def test_sanitize_report_string(self):
        """
        Tests a function which fixes common mistakes while the report is a string
        """
        line = 'KJFK 36010 ? TSFEW004SCT012FEW///CBBKN080 C A V O K A2992'
        fixed = 'KJFK 36010   TS FEW004 SCT012 FEW///CB BKN080 CAVOK A2992'
        self.assertEqual(core.sanitize_report_string(line), fixed)

    def test_get_altimeter(self):
        """
        Tests that the correct alimeter item gets removed from the end of the wx list
        """
        # North American default
        units = structs.Units(**static.NA_UNITS)
        for wx, alt  in (
            (['1', '2'], (None,)),
            (['1', '2', 'A2992'], ('2992', 29.92)),
            (['1', '2', '2992'], ('2992', 29.92)),
            (['1', '2', 'A2992', 'Q1000'], ('2992', 29.92)),
            (['1', '2', 'Q1000', 'A2992'], ('2992', 29.92)),
            (['1', '2', 'Q1000'], ('1000', 1000)),
        ):
            self.assertEqual(units.altimeter, 'inHg')
            retwx, ret_alt = core.get_altimeter(wx, units)
            self.assertEqual(retwx, ['1', '2'])
            self.assert_number(ret_alt, *alt)
        # The last one should have changed the unit
        self.assertEqual(units.altimeter, 'hPa')
        # International
        units = structs.Units(**static.IN_UNITS)
        for wx, alt in (
            (['1', '2'], (None,)),
            (['1', '2', 'Q.1000'], ('1000', 1000)),
            (['1', '2', 'Q1000/10'], ('1000', 1000)),
            (['1', '2', 'A2992', 'Q1000'], ('1000', 1000)),
            (['1', '2', 'Q1000', 'A2992'], ('1000', 1000)),
            (['1', '2', 'A2992'], ('2992', 29.92)),
        ):
            self.assertEqual(units.altimeter, 'hPa')
            retwx, ret_alt = core.get_altimeter(wx, units, 'IN')
            self.assertEqual(retwx, ['1', '2'])
            self.assert_number(ret_alt, *alt)
        # The last one should have changed the unit
        self.assertEqual(units.altimeter, 'inHg')

class TestTaf(unittest.TestCase):

    def test_get_taf_remarks(self):
        """
        Tests that remarks are removed from a TAF report
        """
        for txt, rmk in (
            ('KJFK test', ''),
            ('KJFK test RMK test', 'RMK test'),
            ('KJFK test FCST test', 'FCST test'),
            ('KJFK test AUTOMATED test', 'AUTOMATED test'),
        ):
            report, remarks = core.get_taf_remarks(txt)
            self.assertEqual(report, 'KJFK test')
            self.assertEqual(remarks, rmk)

    def test_sanitize_line(self):
        """
        Tests a function which fixes common new-line signifiers in TAF reports
        """
        for line in ('1 BEC 1', '1 BE CMG1', '1 BEMG 1'):
            self.assertEqual(core.sanitize_line(line), '1 BECMG 1')
        for line in ('1 TEMP0 1', '1 TEMP 1', '1 TEMO1', '1 T EMPO1'):
            self.assertEqual(core.sanitize_line(line), '1 TEMPO 1')
        self.assertEqual(core.sanitize_line('1 2 3 4 5'), '1 2 3 4 5')

    def test_is_tempo_or_prob(self):
        """
        Tests a function which checks that an item signifies a new time period
        """
        for line in (
            {'type': 'TEMPO'},
            {'probability': 30},
            {'probability': 'PROBNA'},
            {'type': 'FROM', 'probability': 30},
        ):
            self.assertTrue(core._is_tempo_or_prob(line))
        for line in (
            {'type': 'FROM'},
            {'type': 'FROM', 'probability': None},
        ):
            self.assertFalse(core._is_tempo_or_prob(line))

    def test_get_taf_alt_ice_turb(self):
        """
        Tests that report global altimeter, icing, and turbulance get removed
        """
        for wx, *data  in (
            (['1'], '', [], []),
            (['1', '512345', '612345'], '', ['612345'], ['512345']),
            (['QNH1234', '1', '612345'], '1234', ['612345'], [])
        ):
            self.assertEqual(core.get_taf_alt_ice_turb(wx), (['1'], *data))

    def test_starts_new_line(self):
        """
        Tests that certain items are identified as new line markers in TAFs
        """
        for item in [*static.TAF_NEWLINE, 'PROB30', 'PROB45', 'PROBNA', 'FM12345678']:
            self.assertTrue(core.starts_new_line(item))
        for item in ('KJFK', '12345Z', '2010/2020', 'FEW060', 'RMK'):
            self.assertFalse(core.starts_new_line(item))

    def test_split_taf(self):
        """
        Tests that TAF reports are split into the correct time periods
        """
        for report, num in (
            ('KJFK test', 1),
            ('KJFK test FM12345678 test', 2),
            ('KJFK test TEMPO test', 2),
            ('KJFK test TEMPO test TEMPO test', 3),
            ('KJFK test PROB30 test TEMPO test', 3),
            ('KJFK test PROB30 TEMPO test TEMPO test', 3),
        ):
            split = core.split_taf(report)
            self.assertEqual(len(split), num)
            self.assertEqual(split[0], 'KJFK test')

    def test_get_type_and_times(self):
        """
        Tests TAF line type, start time, and end time extraction
        """
        for wx, *data  in (
            (['1'], 'FROM', '', ''),
            (['INTER', '1'], 'INTER', '', ''),
            (['TEMPO', '0101/0103', '1'], 'TEMPO', '0101', '0103'),
            (['PROB30', '0101/0103', '1'], 'PROB30', '0101', '0103'),
            (['FM120000', '1'], 'FROM', '1200', ''),
            (['FM1200/1206', '1'], 'FROM', '1200', '1206'),
            (['FM120000', 'TL120600', '1'], 'FROM', '1200', '1206')
        ):
            self.assertEqual(core.get_type_and_times(wx), (['1'], *data))

    def test_find_missing_taf_times(self):
        """
        Tests that missing forecast times can be interpretted by 
        """
        good_lines = [
            {'type': 'FROM', 'start_time': '3021', 'end_time': '3023'},
            {'type': 'FROM', 'start_time': '3023', 'end_time': '0105'},
            {'type': 'FROM', 'start_time': '0105', 'end_time': '0108'},
            {'type': 'FROM', 'start_time': '0108', 'end_time': '0114'}
        ]
        for line in good_lines:
            for key in ('start_time', 'end_time'):
                line[key] = core.make_timestamp(line[key])
        bad_lines = deepcopy(good_lines)
        bad_lines[0]['start_time'] = None
        bad_lines[1]['start_time'] = None
        bad_lines[2]['end_time'] = None
        bad_lines[3]['end_time'] = None
        start, end = good_lines[0]['start_time'], good_lines[-1]['end_time']
        self.assertEqual(core.find_missing_taf_times(bad_lines, start, end), good_lines)

    def test_get_temp_min_and_max(self):
        """
        Tests that temp max and min times are extracted and assigned properly
        """
        for wx, *temps  in (
            (['1'], '', ''),
            (['1', 'TX12/1316Z', 'TNM03/1404Z'], 'TX12/1316Z', 'TNM03/1404Z'),
            (['1', 'TM03/1404Z', 'T12/1316Z'], 'TX12/1316Z', 'TNM03/1404Z'),
        ):
            self.assertEqual(core.get_temp_min_and_max(wx), (['1'], *temps))

    def test_get_oceania_temp_and_alt(self):
        """
        Tests that Oceania-specific elements are identified and removed
        """
        items = ['1', 'T', '2', '3', 'ODD', 'Q', '4', 'C']
        items, tlist, qlist = core.get_oceania_temp_and_alt(items)
        self.assertEqual(items, ['1', 'ODD','C'])
        self.assertEqual(tlist, ['2', '3'])
        self.assertEqual(qlist, ['4'])

    # def test_get_taf_flight_rules(self):
    #     """
    #     """
    #     pass
