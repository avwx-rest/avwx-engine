"""
"""

from avwx.base import AVWXBase
from avwx.service import GFS_MOS


class Forecast(AVWXBase):
    """
    """

    report_type: str

    def __init__(self, icao: str):
        super().__init__(icao)
        self.service = GFS_MOS(self.report_type)
