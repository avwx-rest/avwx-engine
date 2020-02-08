"""
"""

from datetime import datetime

from avwx.service import Service
from avwx.station import Station
from avwx.structs import ReportData, Units


class AVWXBase:
    """
    """

    #: UTC Datetime object when the report was last updated
    last_updated: datetime = None

    #: Provide basic station info if given at init
    station_info: Station = None

    #: The original report string. Fetched on update()
    raw: str = None

    #: ReportData dataclass of parsed data values and units. Parsed on update()
    data: ReportData = None

    #: Units inferred from the station location and report contents
    units: Units = None

    #: Service object used to fetch the report string
    service: Service
