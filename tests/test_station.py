"""
Station Data Tests
"""

# stdlib
from unittest import TestCase

# module
from avwx import exceptions, station


class TestStationFuncs(TestCase):
    """
    Tests station module functions
    """

    def test_uses_na_format(self):
        """
        METAR and TAF reports come in two flavors: North American and International
        
        uses_na_format should determine the format based on the station ident using prefixes
        """
        # NA idents
        for ident in ("KJFK", "PHNL", "TNCM", "MYNN"):
            self.assertTrue(station.uses_na_format(ident))
        # IN idents
        for ident in ("EGLL", "MNAH", "MUHA"):
            self.assertFalse(station.uses_na_format(ident))
        # Bad idents
        for ident in ("12K", "MAYT"):
            with self.assertRaises(exceptions.BadStation):
                station.uses_na_format(ident)

    def test_valid_station(self):
        """
        While not designed to catch all non-existant station idents,
        valid_station should catch non-ICAO strings and filter based on known prefixes
        """
        # Good idents
        for ident in ("KJFK", "K123", "EIGL", "PHNL", "MNAH"):
            station.valid_station(ident)
        # Bad idents
        for ident in ("12K", "MAYT"):
            with self.assertRaises(exceptions.BadStation):
                station.valid_station(ident)

    def test_nearest(self):
        """
        Tests returning nearest Stations to lat, lon
        """
        stn, dist = station.nearest(28.43, -81.31)
        self.assertIsInstance(stn, station.Station)
        self.assertEqual(stn.icao, "KMCO")
        self.assertIsInstance(dist, float)
        for *params, count in (
            (30, -82, 10, True, 0.1, 0),
            (30, -82, 10, False, 0.1, 2),
            (30, -82, 1000, True, 0.5, 4),
            (30, -82, 1000, False, 0.5, 24),
        ):
            stations = station.nearest(*params)
            self.assertEqual(len(stations), count)
            for stn, dist in stations:
                self.assertIsInstance(stn, station.Station)
                self.assertIsInstance(dist, float)


class TestStation(TestCase):
    """
    Tests the Station class
    """

    def test_from_icao(self):
        """
        Tests loading a Station by ICAO ident
        """
        for icao, name, city in (
            ("KJFK", "John F Kennedy International Airport", "New York"),
            ("kjfk", "John F Kennedy International Airport", "New York"),
            ("KLAX", "Los Angeles International Airport", "Los Angeles"),
            ("PHNL", "Daniel K Inouye International Airport", "Honolulu"),
            ("EGLL", "London Heathrow Airport", "London"),
        ):
            stn = station.Station.from_icao(icao)
            self.assertIsInstance(stn, station.Station)
            self.assertEqual(icao.upper(), stn.icao)
            self.assertEqual(name, stn.name)
            self.assertEqual(city, stn.city)
        for bad in ("1234", 1234, None, True, ""):
            with self.assertRaises(exceptions.BadStation):
                station.Station.from_icao(bad)

    def test_nearest(self):
        """
        Tests loading a Station nearest to a lat,lon coordinate pair
        """
        for lat, lon, icao in ((28.43, -81.31, "KMCO"), (28.43, -81, "KTIX")):
            stn, dist = station.Station.nearest(lat, lon)
            self.assertIsInstance(stn, station.Station)
            self.assertIsInstance(dist, float)
            self.assertEqual(stn.icao, icao)
        # Test with IATA req disabled
        stn, dist = station.Station.nearest(28.43, -81, False)
        self.assertIsInstance(stn, station.Station)
        self.assertIsInstance(dist, float)
        self.assertEqual(stn.icao, "FA18")

    def test_sends_reports(self):
        """
        Tests bool indicating likely reporting station
        """
        for icao in ("KJFK", "EGLL"):
            stn = station.Station.from_icao(icao)
            self.assertTrue(stn.sends_reports)
            self.assertIsNotNone(stn.iata)
        for icao in ("FA18",):
            stn = station.Station.from_icao(icao)
            self.assertFalse(stn.sends_reports)
            self.assertIsNone(stn.iata)
