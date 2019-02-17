"""
Michael duPont - michael@mdupont.com
tests/test_metar.py
"""

# library
import json
import os
import unittest
from dataclasses import asdict
from datetime import datetime
from glob import glob
# module
from avwx import metar, structs, Metar

class TestMetar(unittest.TestCase):

    maxDiff = None

    def test_parse(self):
        """
        Tests returned structs from the parse function
        """
        report = 'KJFK 032151Z 16008KT 10SM FEW034 FEW130 BKN250 27/23 A3013 RMK AO2 SLP201'
        data, units = metar.parse(report[:4], report)
        self.assertIsInstance(data, structs.MetarData)
        self.assertIsInstance(units, structs.Units)
        self.assertEqual(data.raw, report)

    def test_metar_ete(self):
        """
        Performs an end-to-end test of all METAR JSON files
        """
        for path in glob(os.path.dirname(os.path.realpath(__file__))+'/metar/*.json'):
            ref = json.load(open(path))
            station = Metar(path.split('/')[-1][:4])
            self.assertIsNone(station.last_updated)
            self.assertTrue(station.update(ref['data']['raw']))
            self.assertIsInstance(station.last_updated, datetime)
            # Clear timestamp due to parse_date limitations
            station.data.time = None
            self.assertEqual(asdict(station.data), ref['data'])
            self.assertEqual(asdict(station.translations), ref['translations'])
            self.assertEqual(station.summary, ref['summary'])
            self.assertEqual(station.speech, ref['speech'])
            self.assertEqual(asdict(station.station_info), ref['station_info'])
