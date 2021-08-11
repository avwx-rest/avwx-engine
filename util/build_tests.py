"""
Creates files for end-to-end tests

python util/build_tests.py
"""

# stdlib
import json
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

# module
import avwx


TESTS_PATH = Path(__file__).parent.parent / "tests"


def _default(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()


def make_metar_test(station: str) -> dict:
    """Builds METAR test file for station"""
    m = avwx.Metar(station)
    m.update()
    return {
        "data": asdict(m.data),
        "translations": asdict(m.translations),
        "summary": m.summary,
        "speech": m.speech,
    }


def make_taf_test(station: str) -> dict:
    """Builds TAF test file for station"""
    t = avwx.Taf(station)
    t.update()
    return {
        "data": asdict(t.data),
        "translations": asdict(t.translations),
        "summary": t.summary,
        "speech": t.speech,
        "station": asdict(t.station),
    }


def make_pirep_test(station: str) -> Optional[dict]:
    """Builds PIREP test file for station"""
    p = avwx.Pireps(station)
    p.update()
    ret = []
    if not p.data:
        return None
    for report in p.data:
        ret.append({"data": asdict(report)})
    return {"reports": ret, "station": asdict(p.station)}


def make_forecast_test(
    report: avwx.forecast.base.Forecast, station: str
) -> Optional[dict]:
    """Builds GFS service test file for station"""
    g = report(station)
    g.update()
    if not g.data:
        return None
    return {"data": asdict(g.data), "station": asdict(g.station)}


def make_mav_test(station: str) -> Optional[dict]:
    """Builds MAV test file for station"""
    return make_forecast_test(avwx.Mav, station)


def make_mex_test(station: str) -> Optional[dict]:
    """Builds MEX test file for station"""
    return make_forecast_test(avwx.Mex, station)


def make_nbh_test(station: str) -> Optional[dict]:
    """Builds NBH test file for station"""
    return make_forecast_test(avwx.Nbh, station)


def make_nbs_test(station: str) -> Optional[dict]:
    """Builds NBS test file for station"""
    return make_forecast_test(avwx.Nbs, station)


def make_nbe_test(station: str) -> Optional[dict]:
    """Builds NBE test file for station"""
    return make_forecast_test(avwx.Nbe, station)


def main():
    """Creates source files for end-to-end tests"""
    targets = {
        "current": ("metar", "taf", "pirep"),
        "forecast": ("mav", "mex", "nbh", "nbs", "nbe"),
    }

    for target, reports in targets.items():
        for report_type in reports:
            for icao in ("KJFK", "KMCO", "PHNL", "EGLL"):
                data = globals()[f"make_{report_type}_test"](icao)
                if data:
                    data["icao"] = icao
                    data["created"] = datetime.now(tz=timezone.utc).date()
                    path = TESTS_PATH.joinpath(
                        target, "data", report_type, icao + ".json"
                    )
                    json.dump(
                        data, path.open("w"), indent=4, sort_keys=True, default=_default
                    )


if __name__ == "__main__":
    main()
