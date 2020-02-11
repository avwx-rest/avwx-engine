"""
"""


# module
from avwx.forecast.base import Forecast


class GfxShort(Forecast):
    """
    """

    report_type = "mav"


class GfxLong(Forecast):
    """
    """

    report_type = "mex"
