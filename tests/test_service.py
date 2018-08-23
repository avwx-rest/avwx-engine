"""
Michael duPont - michael@mdupont.com
tests/test_service.py
"""

# library
import unittest
# module
from avwx import exceptions, service

class TestService(unittest.TestCase):

    serv: service.Service

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serv = service.Service('metar')

    def test_init(self):
        """
        Tests that the Service class is initialized properly
        """
        for attr in ('url', 'rtype', 'make_err', '_extract', 'fetch'):
            self.assertTrue(hasattr(self.serv, attr))
        self.assertEqual(self.serv.rtype, 'metar')

    def test_service(self):
        """
        Tests that the base Service class has no URL and throws NotImplemented errors
        """
        self.assertIsNone(self.serv.url)
        with self.assertRaises(NotImplementedError):
            self.serv._extract(None)

    def test_make_err(self):
        """
        Tests that InvalidRequest exceptions are generated with the right message
        """
        key, msg = 'test_key', 'testing'
        err = self.serv.make_err(msg, key)
        err_str = f'Could not find {key} in {self.serv.__class__.__name__} response\n{msg}'
        self.assertIsInstance(err, exceptions.InvalidRequest)
        self.assertEqual(err.args, (err_str,))
        self.assertEqual(str(err), err_str)

    def test_fetch(self):
        """
        Tests fetch exception handling
        """
        for station in ('12K', 'MAYT'):
            with self.assertRaises(exceptions.BadStation):
                self.serv.fetch(station)
        # Should raise exception due to empty url
        with self.assertRaises(AttributeError):
            self.serv.fetch('KJFK')

class TestNOAA(TestService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serv = service.NOAA('metar')

    def test_service(self):
        """
        Tests that the NOAA class has a URL
        """
        self.assertIsInstance(self.serv.url, str)

    def test_fetch(self):
        """
        Tests that reports are fetched from NOAA ADDS
        """
        for station in ('12K', 'MAYT'):
            with self.assertRaises(exceptions.BadStation):
                self.serv.fetch(station)
        for station in ('KJFK', 'EGLL', 'PHNL'):
            report = self.serv.fetch(station)
            self.assertIsInstance(report, str)
            self.assertTrue(report.startswith(station))

class TestAMO(TestService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serv = service.AMO('metar')

    def test_service(self):
        """
        Tests that the AMO class has a URL
        """
        self.assertIsInstance(self.serv.url, str)

    def test_fetch(self):
        """
        Tests that reports are fetched from AMO for Korean stations
        """
        for station in ('12K', 'MAYT'):
            with self.assertRaises(exceptions.BadStation):
                self.serv.fetch(station)
        for station in ('RKSI', 'RKSS', 'RKNY'):
            report = self.serv.fetch(station)
            self.assertIsInstance(report, str)
            self.assertTrue(report.startswith(station))

class TestModule(unittest.TestCase):

    def test_get_service(self):
        """
        Tests that the correct service class is returned
        """
        for stations, serv in (
            (('KJFK', 'EGLL', 'PHNL'), service.NOAA),
            (('RKSI',), service.AMO),
        ):
            for station in stations:
                self.assertIsInstance(service.get_service(station)(station), serv)
