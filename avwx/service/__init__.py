"""
.. include:: ../../docs/service.md
"""

from .base import Service
from .files import NOAA_GFS, NOAA_NBM
from .scrape import (
    get_service,
    NOAA,
    AMO,
    AVT,
    MAC,
    AUBOM,
    OLBS,
    NAM,
    FAA_NOTAM,
)
