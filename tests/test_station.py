"""
Station Data Tests
"""

# stdlib
import unittest

# module
from avwx import exceptions, station


class TestStationFunctions(unittest.TestCase):
    """Tests station module functions"""

    def test_station_list(self):
        """Test reporting filter for full station list"""
        reporting = station.station_list()
        full = station.station_list(False)
        self.assertTrue(len(full) > len(reporting))

    def test_uses_na_format(self):
        """METAR and TAF reports come in two flavors: North American and International

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
        """While not designed to catch all non-existant station idents,
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
        """Tests returning nearest Stations to lat, lon"""
        dist = station.nearest(28.43, -81.31)
        stn = dist.pop("station")
        self.assertIsInstance(stn, station.Station)
        self.assertEqual(stn.icao, "KMCO")
        for val in dist.values():
            self.assertIsInstance(val, float)
        for *params, count in (
            (30, -82, 10, True, True, 0.3, 1),
            (30, -82, 10, True, False, 0.3, 5),
            (30, -82, 10, False, False, 0.3, 7),
            (30, -82, 1000, True, True, 0.5, 5),
            (30, -82, 1000, False, False, 0.5, 37),
        ):
            stations = station.nearest(*params)
            self.assertGreaterEqual(len(stations), count)
            for dist in stations:
                stn = dist.pop("station")
                self.assertIsInstance(stn, station.Station)
                for val in dist.values():
                    self.assertIsInstance(val, float)

    def test_nearest_filter(self):
        """Tests filtering nearest stations"""
        for airport, reports, count in (
            (True, True, 6),
            (True, False, 16),
            (False, True, 6),
            (False, False, 30),
        ):
            stations = station.nearest(30, -80, 30, airport, reports, 1.5)
            self.assertEqual(len(stations), count)


class TestStation(unittest.TestCase):
    """Tests the Station class"""

    def test_storage_code(self):
        """Tests ID code selection"""
        stn = station.Station.from_icao("KJFK")
        stn.icao = "ICAO"
        stn.iata = "IATA"
        stn.gps = "GPS"
        stn.local = "LOCAL"
        self.assertEqual(stn.storage_code, "ICAO")
        stn.icao = None
        self.assertEqual(stn.storage_code, "IATA")
        stn.iata = None
        self.assertEqual(stn.storage_code, "GPS")
        stn.gps = None
        self.assertEqual(stn.storage_code, "LOCAL")
        stn.local = None
        with self.assertRaises(exceptions.BadStation):
            stn.storage_code

    def test_from_icao(self):
        """Tests loading a Station by ICAO ident"""
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
        for bad in ("1234", 1234, None, True, "", "KX07", "TX35"):
            with self.assertRaises(exceptions.BadStation):
                station.Station.from_icao(bad)

    def test_from_iata(self):
        """Tests loading a Station by IATA code"""
        for iata, icao in (
            ("JFK", "KJFK"),
            ("jfk", "KJFK"),
            ("LAX", "KLAX"),
            ("HNL", "PHNL"),
            ("LHR", "EGLL"),
        ):
            stn = station.Station.from_iata(iata)
            self.assertIsInstance(stn, station.Station)
            self.assertEqual(iata.upper(), stn.iata)
            self.assertEqual(icao, stn.icao)
        for bad in ("1234", 1234, None, True, "", "KMCO", "X35"):
            with self.assertRaises(exceptions.BadStation):
                station.Station.from_iata(bad)

    def test_from_gps(self):
        """Tests loading a Station by GPS code"""
        for gps, icao, name in (
            ("KJFK", "KJFK", "John F Kennedy International Airport"),
            ("kjfk", "KJFK", "John F Kennedy International Airport"),
            ("EGLL", "EGLL", "London Heathrow Airport"),
            ("KX07", None, "Lake Wales Municipal Airport"),
        ):
            stn = station.Station.from_gps(gps)
            self.assertIsInstance(stn, station.Station)
            self.assertEqual(gps.upper(), stn.gps)
            self.assertEqual(icao, stn.icao)
            self.assertEqual(name, stn.name)
        for bad in ("1234", 1234, None, True, "", "KX35"):
            with self.assertRaises(exceptions.BadStation):
                station.Station.from_gps(bad)

    def test_from_code(self):
        """Tests loading a Station by any code"""
        for code, icao, name in (
            ("KJFK", "KJFK", "John F Kennedy International Airport"),
            ("kjfk", "KJFK", "John F Kennedy International Airport"),
            ("EGLL", "EGLL", "London Heathrow Airport"),
            ("LHR", "EGLL", "London Heathrow Airport"),
            ("LAX", "KLAX", "Los Angeles International Airport"),
            ("HNL", "PHNL", "Daniel K Inouye International Airport"),
            ("KX07", None, "Lake Wales Municipal Airport"),
        ):
            stn = station.Station.from_code(code)
            self.assertIsInstance(stn, station.Station)
            self.assertEqual(icao, stn.icao)
            self.assertEqual(name, stn.name)
        for bad in ("1234", 1234, None, True, ""):
            with self.assertRaises(exceptions.BadStation):
                station.Station.from_code(bad)

    def test_nearest(self):
        """Tests loading a Station nearest to a lat,lon coordinate pair"""
        for lat, lon, icao in ((28.43, -81.31, "KMCO"), (28.43, -81, "KTIX")):
            stn, dist = station.Station.nearest(lat, lon, is_airport=True)
            self.assertIsInstance(stn, station.Station)
            self.assertEqual(stn.icao, icao)
            for val in dist.values():
                self.assertIsInstance(val, float)
        # Test with IATA req disabled
        stn, dist = station.Station.nearest(28.43, -81, False, False)
        self.assertIsInstance(stn, station.Station)
        self.assertEqual(stn.lookup_code, "FA18")
        for val in dist.values():
            self.assertIsInstance(val, float)

    def test_nearby(self):
        """Tests finding nearby airports to the current one"""
        for code, near in (
            (
                "KMCO",
                "KORL",
            ),
            ("KJFK", "KLGA"),
            ("PHKO", "PHSF"),
        ):
            target = station.Station.from_code(code)
            nearby = target.nearby()
            self.assertIsInstance(nearby, list)
            self.assertEqual(len(nearby), 10)
            nearest = nearby[0]
            self.assertIsInstance(nearest[0], station.Station)
            self.assertIsInstance(nearest[1], dict)
            self.assertEqual(nearest[0].lookup_code, near)

    def test_sends_reports(self):
        """Tests bool indicating likely reporting station"""
        for code in ("KJFK", "EGLL"):
            stn = station.Station.from_code(code)
            self.assertTrue(stn.sends_reports)
            self.assertIsNotNone(stn.iata)
        for code in ("FA18",):
            stn = station.Station.from_code(code)
            self.assertFalse(stn.sends_reports)
            self.assertIsNone(stn.iata)


class TestStationSearch(unittest.TestCase):
    """Tests the Station class"""

    def test_exact_icao(self):
        """Tests searching for a Station by exact ICAO ident"""
        for icao in ("KMCO", "KJFK", "PHNL", "EGLC"):
            results = station.search(icao)
            self.assertEqual(len(results), 10)
            self.assertEqual(results[0].icao, icao)

    def test_combined_terms(self):
        """Tests search using multiple search terms"""
        for text, icao in (
            ("kona hi", "PHKO"),
            ("danville powell field", "KDVK"),
            ("lexington ky", "KLEX"),
            ("orlando", "KMCO"),
            ("london city", "EGLC"),
        ):
            results = station.search(text)
            self.assertEqual(len(results), 10)
            self.assertEqual(results[0].lookup_code, icao)

    def test_search_filter(self):
        """Tests search result filtering"""
        for airport in station.search("orlando", is_airport=True):
            self.assertTrue("airport" in airport.type)
        for airport in station.search("orlando", sends_reports=True):
            self.assertTrue(airport.reporting)
