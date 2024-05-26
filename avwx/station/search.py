"""Station text-based search."""

# stdlib
from __future__ import annotations

from contextlib import suppress
from functools import lru_cache
from typing import TYPE_CHECKING

# module
from avwx.exceptions import MissingExtraModule
from avwx.load_utils import LazyCalc
from avwx.station.meta import STATIONS
from avwx.station.station import Station, station_filter

if TYPE_CHECKING:
    from collections.abc import Iterable

# Catch import error only if user attemps a text search
with suppress(ModuleNotFoundError):
    from rapidfuzz import fuzz, process, utils


TYPE_ORDER = [
    "large_airport",
    "medium_airport",
    "small_airport",
    "seaplane_base",
    "heliport",
    "balloonport",
    "weather_station",
]


def _format_search(airport: dict, keys: Iterable[str]) -> str | None:
    values = [airport.get(k) for k in keys]
    code = values[0] or values[2]
    if not code:
        return None
    values.insert(0, code)
    return " - ".join(k for k in values if k)


def _build_corpus() -> list[str]:
    keys = ("icao", "iata", "gps", "local", "city", "state", "name")
    return [text for s in STATIONS.values() if (text := _format_search(s, keys))]


_CORPUS = LazyCalc(_build_corpus)


def _sort_key(result: tuple[Station, int]) -> tuple[int, ...]:
    station, score = result
    try:
        type_order = TYPE_ORDER.index(station.type)
    except ValueError:
        type_order = 10
    return (score, 10 - type_order)


@lru_cache(maxsize=128)
def search(
    text: str,
    limit: int = 10,
    *,
    is_airport: bool = False,
    sends_reports: bool = True,
) -> list[Station]:
    """Text search for stations against codes, name, city, and state.

    Results may be shorter than limit value.
    """
    try:
        results = process.extract(
            text,
            _CORPUS.value,
            limit=limit * 20,
            scorer=fuzz.token_set_ratio,
            processor=utils.default_process,
        )
    except NameError as name_error:
        extra = "fuzz"
        raise MissingExtraModule(extra) from name_error
    results = [(Station.from_code(k[:4]), s) for k, s, _ in results]
    results.sort(key=_sort_key, reverse=True)
    results = [s for s, _ in results if station_filter(s, is_airport=is_airport, reporting=sends_reports)]
    return results[:limit] if len(results) > limit else results
