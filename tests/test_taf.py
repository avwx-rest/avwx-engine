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
        self.assertEqual(lines[4]['Probability'], '30')
        self.assertTrue(lines[4]['Raw-Line'].startswith('PROB30'))

    def test_wind_shear(self):
        """"""
        report = ("TAF AMD CYOW 282059Z 2821/2918 09008KT WS015/20055KT P6SM BKN220 "
                  "BECMG 2821/2823 19015G25KT "
                  "FM290300 21013G23KT P6SM -SHRA BKN040 OVC100 "
                  "TEMPO 2903/2909 4SM BR OVC020 "
                  "FM290900 25012KT P6SM SCT030 "
                  "FM291300 32017G27KT P6SM OVC030 "
                  "TEMPO 2913/2918 P6SM -SHRA OVC020 RMK NXT FCST BY 290000Z")
        taf = avwx.Taf('CYBC')
        taf.update(report)
        lines = taf.data['Forecast']
        self.assertEqual(len(lines), 7)
        self.assertEqual(lines[0]['Wind-Shear'], 'WS015/20055')
