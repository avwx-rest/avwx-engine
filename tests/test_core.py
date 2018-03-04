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
        """While not designed to catch all non-existant station idents,
        valid_station should catch non-ICAO strings and filter based on known prefixes
        """
        good_stations = ('KJFK', 'K123', 'EIGL', 'PHNL', 'MNAH')
        bad_stations = ('12K', 'MAYT')
        for station in good_stations:
            avwx.core.valid_station(station)
        for station in bad_stations:
            with self.assertRaises(avwx.exceptions.BadStation):
                avwx.core.valid_station(station)
