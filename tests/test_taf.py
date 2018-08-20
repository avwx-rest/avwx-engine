"""
Michael duPont - michael@mdupont.com
tests/test_taf.py
"""


# library
import json
import os
import unittest
from copy import deepcopy
from dataclasses import asdict
from glob import glob
# module
from avwx import core, taf, structs, Taf

class TestTaf(unittest.TestCase):

    def test_fetch(self):
        """
        Tests if the old fetch function returns a report from a Service object
        """
        for station in ('KJFK', 'PHNL', 'EGLL', 'RKSI'):
            report = taf.fetch(station)
            self.assertIsInstance(report, str)
            self.assertTrue(report.startswith(station) or report.startswith('AMD '+station))

    def test_parse(self):
        """
        Tests returned structs from the parse function
        """
        report = ('PHNL 042339Z 0500/0606 06018G25KT P6SM FEW030 SCT060 FM050600 06010KT '
                  'P6SM FEW025 SCT060 FM052000 06012G20KT P6SM FEW030 SCT060')
        data, units = taf.parse(report[:4], report)
        self.assertIsInstance(data, structs.TafData)
        self.assertIsInstance(units, structs.Units)
        self.assertEqual(data.raw, report)

    def test_prob_line(self):
        """
        Even though PROB__ is not in TAF_NEWLINE, it should still separate,
        add a new line, and include the prob value in line['Probability']
        """
        report = ("TAF AMD CYBC 271356Z 2714/2802 23015G25KT P6SM BKN090 "
                  "TEMPO 2714/2718 P6SM -SHRA BKN060 OVC090 "
                  "FM271800 22015G25KT P6SM OVC040 "
                  "TEMPO 2718/2724 6SM -SHRA "
                  "PROB30 2718/2724 VRB25G35KT 1SM +TSRA BR BKN020 OVC040CB "
                  "FM280000 23008KT P6SM BKN040 RMK FCST BASED ON AUTO OBS. NXT FCST BY 272000Z")
        taf = Taf('CYBC')
        taf.update(report)
        lines = taf.data.forecast
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[3].probability, None)
        self.assertEqual(lines[4].probability, core.make_number('30'))
        self.assertTrue(lines[4].raw.startswith('PROB30'))

    def test_wind_shear(self):
        """
        Wind shear should be recognized as its own element in addition to wind
        """
        report = ("TAF AMD CYOW 282059Z 2821/2918 09008KT WS015/20055KT P6SM BKN220 "
                  "BECMG 2821/2823 19015G25KT "
                  "FM290300 21013G23KT P6SM -SHRA BKN040 OVC100 "
                  "TEMPO 2903/2909 4SM BR OVC020 "
                  "FM290900 25012KT P6SM SCT030 "
                  "FM291300 32017G27KT P6SM OVC030 "
                  "TEMPO 2913/2918 P6SM -SHRA OVC020 RMK NXT FCST BY 290000Z")
        taf = Taf('CYBC')
        taf.update(report)
        lines = taf.data.forecast
        self.assertEqual(len(lines), 7)
        self.assertEqual(lines[0].wind_shear, 'WS015/20055')
        self.assertEqual(taf.translations.forecast[1].clouds, None)

    def test_prob_tempo(self):
        """
        Non-PROB types should take precident but still fill the probability value
        """
        report = ("EGLL 192253Z 2000/2106 28006KT 9999 BKN035 "
                  "PROB30 TEMPO 2004/2009 BKN012 "
                  "PROB30 TEMPO 2105/2106 8000 BKN006")
        taf = Taf('EGLL')
        taf.update(report)
        lines = taf.data.forecast
        for line in lines:
            self.assertIsInstance(line.start_time, structs.Timestamp)
            self.assertIsInstance(line.end_time, structs.Timestamp)
        for i in range(1, 3):
            self.assertEqual(lines[i].type, 'TEMPO')
            self.assertEqual(lines[i].probability.value, 30)
    maxDiff = None
    def test_taf_ete(self):
        """
        Performs an end-to-end test of all TAF JSON files
        """
        nodate = lambda s: s[s.find('-')+2:]
        for path in glob(os.path.dirname(os.path.realpath(__file__))+'/taf/*.json'):
            ref = json.load(open(path))
            station = Taf(path.split('/')[-1][:4])
            self.assertTrue(station.update(ref['data']['raw']))
            # Clear timestamp due to parse_date limitations
            nodt = deepcopy(station.data)
            for key in ('time', 'start_time', 'end_time'):
                setattr(nodt, key, None)
            for i in range(len(nodt.forecast)):
                for key in ('start_time', 'end_time'):
                    setattr(nodt.forecast[i], key, None)
            self.assertEqual(asdict(nodt), ref['data'])
            self.assertEqual(asdict(station.translations), ref['translations'])
            self.assertEqual(station.summary, ref['summary'])
            self.assertEqual(nodate(station.speech), nodate(ref['speech']))
            self.assertEqual(asdict(station.station_info), ref['station_info'])
