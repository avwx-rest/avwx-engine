"""Creates files for end-to-end tests."""

# ruff: noqa: INP001

# stdlib
from __future__ import annotations

import json
import secrets
import sys
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# module
from find_bad_stations import PROJECT_ROOT

import avwx
from tests.util import round_coordinates

TESTS_PATH = PROJECT_ROOT / "tests"


def _default(o: Any) -> str | None:
    return o.isoformat() if isinstance(o, date | datetime) else None


def save(data: dict, path: Path) -> None:
    """Save JSON data to path."""
    json.dump(data, path.open("w"), indent=4, sort_keys=True, default=_default)


def make_metar_test(station: str) -> dict:
    """Build METAR test file for station."""
    m = avwx.Metar(station)
    m.update()
    return {
        "data": asdict(m.data),
        "translations": asdict(m.translations),
        "summary": m.summary,
        "speech": m.speech,
    }


def make_taf_test(station: str) -> dict:
    """Build TAF test file for station."""
    t = avwx.Taf(station)
    t.update()
    return {
        "data": asdict(t.data),
        "translations": asdict(t.translations),
        "summary": t.summary,
        "speech": t.speech,
        "station": asdict(t.station),
    }


def make_pirep_test(station: str) -> dict | None:
    """Build PIREP test file for station."""
    p = avwx.Pireps(station)
    p.update()
    if not p.data:
        return None
    ret = [{"data": asdict(report)} for report in p.data]
    return {"reports": ret, "station": asdict(p.station)}


def make_notam_test(station: str) -> dict | None:
    """Build NOTAM test file for station."""
    n = avwx.Notams(station)
    n.update()
    ret = []
    if not n.data:
        return None
    for report in n.data:
        report.time = None
        ret.append({"data": asdict(report)})
    return {"reports": ret, "station": asdict(n.station)}


def make_forecast_test(report: avwx.forecast.base.Forecast, station: str) -> dict | None:
    """Build GFS service test file for station."""
    g = report(station)
    g.update()
    return {"data": asdict(g.data), "station": asdict(g.station)} if g.data else None


# def make_mav_test(station: str) -> dict | None:
#     """Build MAV test file for station."""
#     return make_forecast_test(avwx.Mav, station)


# def make_mex_test(station: str) -> dict | None:
#     """Build MEX test file for station."""
#     return make_forecast_test(avwx.Mex, station)


def make_nbh_test(station: str) -> dict | None:
    """Build NBH test file for station."""
    return make_forecast_test(avwx.Nbh, station)


def make_nbs_test(station: str) -> dict | None:
    """Build NBS test file for station."""
    return make_forecast_test(avwx.Nbs, station)


def make_nbe_test(station: str) -> dict | None:
    """Build NBE test file for station."""
    return make_forecast_test(avwx.Nbe, station)


def make_nbx_test(station: str) -> dict | None:
    """Build NBX test file for station."""
    return make_forecast_test(avwx.Nbx, station)


def make_airsigmet_tests() -> None:
    """Build IRMET/SIGMET test file."""
    a = avwx.AirSigManager()
    a.update()
    if a.reports is None:
        return
    reports = {}
    for _ in range(10):
        while True:
            report = secrets.choice(a.reports)
            key = report.raw[:20]
            if key not in reports:
                reports[key] = {
                    "created": datetime.now(tz=UTC).date(),
                    "data": round_coordinates(asdict(report.data)),
                }
                break
    path = TESTS_PATH / "current" / "data" / "airsigmet.json"
    save(list(reports.values()), path)


def main() -> None:
    """Create source files for end-to-end tests."""
    targets = {
        "current": ("metar", "taf", "pirep", "notam"),
        "forecast": ("nbh", "nbs", "nbe", "nbx"),
    }

    for target, reports in targets.items():
        for report_type in reports:
            for icao in ("KJFK", "KMCO", "PHNL", "EGLL"):
                if data := globals()[f"make_{report_type}_test"](icao):
                    data["icao"] = icao
                    data["created"] = datetime.now(tz=UTC).date()
                    path = TESTS_PATH.joinpath(target, "data", report_type, f"{icao}.json")
                    save(data, path)
    make_airsigmet_tests()


if __name__ == "__main__":
    main()
