"""
Services for fetching reports
"""

from .base import Service
from .files import NOAA_GFS, NOAA_NBM
from .scrape import (
    get_service,
    NOAA,
    NOAA_ADDS,
    AMO,
    AVT,
    MAC,
    AUBOM,
    OLBS,
    NAM,
    FAA_NOTAM,
)
