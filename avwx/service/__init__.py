""".. include:: ../../docs/service.md"""

from avwx.service.base import Service
from avwx.service.files import NoaaGfs, NoaaNbm
from avwx.service.scrape import (
    Amo,
    Aubom,
    Avt,
    # FaaNotam,
    Mac,
    MetNo,
    Nam,
    NavCanada,
    Noaa,
    Olbs,
    get_service,
)

__all__ = (
    "get_service",
    "Amo",
    "Aubom",
    "Avt",
    "Mac",
    "MetNo",
    "Nam",
    "NavCanada",
    "Noaa",
    "NoaaGfs",
    "NoaaNbm",
    "Olbs",
    "Service",
    # "FaaNotam",
)
