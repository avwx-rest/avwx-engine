"""
AIRMET SIGMET Report Tests
"""

# module
from avwx.current import airsigmet

# tests
from tests.util import BaseTest


class TestAirSigmet(BaseTest):
    """Tests AirSigmet class and parsing"""

    maxDiff = None

    def test_bulletin(self):
        for repr, type, country, number in (
            ("WSRH31", "sigmet", "RH", 31),
            ("WAUS01", "airmet", "US", 1),
        ):
            bulletin = airsigmet._bulletin(repr)
            self.assertEqual(bulletin.repr, repr)
            self.assertEqual(bulletin.type.value, type)
            self.assertEqual(bulletin.country, country)
            self.assertEqual(bulletin.number, number)
