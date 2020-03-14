"""
"""

# stdlib
import unittest

# module
from avwx import current
from avwx.structs import Code


class BaseTest(unittest.TestCase):
    def test_wxcode(self):
        """
        Tests expanding weather codes or ignoring them
        """
        for code, value in (("", ""), ("R03/03002V03", "R03/03002V03")):
            self.assertEqual(current.base.wx_code(code), value)
        for code, value in (
            ("+RATS", "Heavy Rain Thunderstorm"),
            ("VCFC", "Vicinity Funnel Cloud"),
            ("-GR", "Light Hail"),
            ("FZFG", "Freezing Fog"),
            ("BCBLSN", "Patchy Blowing Snow"),
        ):
            obj = Code(code, value)
            self.assertEqual(current.base.wx_code(code), obj)
