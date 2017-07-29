"""
Michael duPont - michael@mdupont.com
tests/test_taf.py
"""

# pylint: disable=E1101,C0103

# library
import unittest
# module
import avwx

class TestTaf(unittest.TestCase):

    def test_prob_line(self):
        """Even though PROB__ is not in TAF_NEWLINE, it should still separate,
        add a new line, and include the prob value in line['Probability']
        """
        report = ("TAF AMD CYBC 271356Z 2714/2802 23015G25KT P6SM BKN090 "
                  "TEMPO 2714/2718 P6SM -SHRA BKN060 OVC090 "
                  "FM271800 22015G25KT P6SM OVC040 "
                  "TEMPO 2718/2724 6SM -SHRA "
                  "PROB30 2718/2724 VRB25G35KT 1SM +TSRA BR BKN020 OVC040CB "
                  "FM280000 23008KT P6SM BKN040 RMK FCST BASED ON AUTO OBS. NXT FCST BY 272000Z")
        taf = avwx.Taf('CYBC')
        taf.update(report)
        lines = taf.data['Forecast']
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[3]['Probability'], '')
        self.assertEqual(lines[4]['Probability'], 'PROB30')
        self.assertTrue(lines[4]['Raw-Line'].startswith('PROB30'))
