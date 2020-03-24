"""
Creates files for end-to-end tests

python util/build_tests.py
"""

# stdlib
import datetime
import json
from dataclasses import asdict

# module
import avwx


def _default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


def make_metar_test(station: str) -> dict:
    """
    Builds METAR test file for station
    """
    m = avwx.Metar(station)
    m.update()
    # Clear timestamp due to parse_date limitations
    m.data.time = None
    return {
        "data": asdict(m.data),
        "translations": asdict(m.translations),
        "summary": m.summary,
        "speech": m.speech,
        "station": asdict(m.station),
    }


def make_taf_test(station: str, report: str = None) -> dict:
    """
    Builds TAF test file for station
    """
    t = avwx.Taf(station)
    t.update(report)
    data = asdict(t.data)
    # Clear timestamp due to parse_date limitations
    for key in ("time", "start_time", "end_time"):
        data[key] = None
    for i in range(len(data["forecast"])):
        for key in ("start_time", "end_time"):
            data["forecast"][i][key] = None
    return {
        "data": data,
        "translations": asdict(t.translations),
        "summary": t.summary,
        "speech": t.speech,
        "station": asdict(t.station),
    }


def make_pirep_test(station: str) -> [dict]:
    """
    Builds PIREP test file for station
    """
    p = avwx.Pireps(station)
    p.update()
    ret = []
    if not p.data:
        return
    for report in p.data:
        # Clear timestamp due to parse_date limitations
        report.time = None
        ret.append({"data": asdict(report)})
    return {"reports": ret, "station": asdict(p.station)}


def make_gfs_test(report: "Forecast", station: str) -> dict:
    """
    Builds GFS service test file for station
    """
    g = report(station)
    g.update()
    if not g.data:
        return
    return {"data": asdict(g.data), "station": asdict(g.station)}


def make_mav_test(station: str) -> dict:
    """
    Builds MAV test file for station
    """
    return make_gfs_test(avwx.Mav, station)


def make_mex_test(station: str) -> dict:
    """
    Builds MEX test file for station
    """
    return make_gfs_test(avwx.Mex, station)


if __name__ == "__main__":
    from pathlib import Path

    targets = {"current": ("metar", "taf", "pirep"), "forecast": ("mav", "mex")}

    for target, reports in targets.items():
        for report_type in reports:
            for station in ("KJFK", "KMCO", "PHNL", "EGLL"):
                data = locals()[f"make_{report_type}_test"](station)
                if data:
                    path = Path("tests", target, "data", report_type, station + ".json")
                    json.dump(
                        data, path.open("w"), indent=4, sort_keys=True, default=_default
                    )
