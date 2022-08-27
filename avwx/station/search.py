"""
Station text-based search
"""

# stdlib
from contextlib import suppress
from functools import lru_cache
from typing import Iterable, List, Tuple

# module
from avwx.load_utils import LazyCalc
from avwx.station.meta import STATIONS
from avwx.station.station import Station, station_filter


# Catch import error only if user attemps a text search
with suppress(ModuleNotFoundError):
    from rapidfuzz import fuzz, process


TYPE_ORDER = [
    "large_airport",
    "medium_airport",
    "small_airport",
    "seaplane_base",
    "heliport",
    "balloonport",
    "weather_station",
]


def _format_search(airport: dict, keys: Iterable[str]) -> str:
    values = [airport.get(k) for k in keys]
    code = values[0] or values[2]
    values.insert(0, code)
    return " - ".join(k for k in values if k)


def _build_corpus() -> List[str]:
    keys = ("icao", "iata", "gps", "city", "state", "name")
    return [_format_search(s, keys) for s in STATIONS.values()]


_CORPUS = LazyCalc(_build_corpus)


def _sort_key(result: Tuple[Station, int]) -> Tuple[int, ...]:
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
    is_airport: bool = False,
    sends_reports: bool = True,
) -> List[Station]:
    """Text search for stations against codes, name, city, and state

    Results may be shorter than limit value
    """
    try:
        results = process.extract(
            text, _CORPUS.value, limit=limit * 20, scorer=fuzz.token_set_ratio
        )
    except NameError as name_error:
        raise ModuleNotFoundError(
            'rapidfuzz must be installed to use text search. Run "pip install avwx-engine[fuzz]" to enable this'
        ) from name_error
    results = [(Station.from_code(k[:4]), s) for k, s, _ in results]
    results.sort(key=_sort_key, reverse=True)
    results = [s for s, _ in results if station_filter(s, is_airport, sends_reports)]
    return results[:limit] if len(results) > limit else results
