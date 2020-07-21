"""
Services for fetching reports
"""

from .base import Service
from .files import NOAA_NBM
from .scrape import get_service, NOAA, NOAA_ADDS, AMO, MAC, AUBOM, GFS_MOS
