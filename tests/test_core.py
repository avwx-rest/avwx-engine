"""
Michael duPont - michael@mdupont.com
tests/test_core.py
"""

# pylint: disable=E1101,C0103

# library
import unittest
# module
import avwx

class TestCore(unittest.TestCase):

    def test_valid_station(self):
        """"""
        good_stations = ('KJFK', 'K123', 'EIGL', 'PHNL', 'MNAH', 'MAYT')
        bad_stations = ('12K', 'MZRT')
