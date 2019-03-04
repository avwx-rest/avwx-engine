"""
Michael duPont - michael@mdupont.com
tests/test_pirep.py
"""

# library
import unittest
# module
from avwx import pirep, structs

class TestPirep(unittest.TestCase):

    def test_cloud_tops(self):
        """
        Tests converting clouds with tops
        """
        for cloud, out in (
            ('OVC100-TOP110', ['OVC', 100, 110]),
            ('OVC065-TOPUNKN', ['OVC', 65, None]),
            ('OVCUNKN-TOP150', ['OVC', None, 150]),
            ('SCT-BKN050-TOP100', ['SCT-BKN', 50, 100]),
            ('BKN-OVCUNKN-TOP060', ['BKN-OVC', None, 60]),
            ('BKN120-TOP150', ['BKN', 120, 150]),
            ('OVC-TOP085', ['OVC', None, 85]),
        ):
            parsed = pirep._clouds(cloud)[0]
            self.assertIsInstance(parsed, structs.Cloud)
            self.assertEqual(parsed.repr, cloud)
            for i, key in enumerate(('type', 'base', 'top')):
                self.assertEqual(getattr(parsed, key), out[i])
