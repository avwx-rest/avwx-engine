"""
Station text-based search
"""

# stdlib
from functools import lru_cache
from typing import Iterable, List, Tuple

# library
from rapidfuzz import fuzz, process  # type: ignore

# module
from avwx.load_utils import LazyCalc
from avwx.station.meta import STATIONS
from avwx.station.station import Station, station_filter


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
    return " - ".join(k for k in values if k)


def _build_corpus() -> List[str]:
    keys = ("icao", "iata", "city", "state", "name")
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
    results = process.extract(
        text, _CORPUS.value, limit=limit * 20, scorer=fuzz.token_set_ratio
    )
    results = [(Station.from_icao(k[:4]), s) for k, s, _ in results]
    results.sort(key=_sort_key, reverse=True)
    results = [s for s, _ in results if station_filter(s, is_airport, sends_reports)]
    return results[:limit] if len(results) > limit else results
