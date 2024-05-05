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


__all__ = (
    AMO,
    AUBOM,
    AVT,
    FAA_NOTAM,
    get_service,
    MAC,
    NAM,
    NOAA_GFS,
    NOAA_NBM,
    NOAA,
    OLBS,
    Service,
)
