"""
Services for fetching reports
"""

from .base import Service
from .files import NOAA_GFS, NOAA_NBM
from .scrape import get_service, NOAA, NOAA_ADDS, AMO, MAC, AUBOM, OLBS
