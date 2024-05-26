"""PIREP Report Tests."""

# ruff: noqa: SLF001

# stdlib
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

# library
import pytest

# module
from avwx import structs
from avwx.current import pirep
from avwx.structs import Code
from tests.util import assert_number, assert_value, get_data


@pytest.mark.parametrize(
    ("root", "station", "report_type"),
    [
        ("JAX UA", "JAX", "UA"),
        ("DMW UUA", "DMW", "UUA"),
        ("UA", None, "UA"),
        ("MCO", "MCO", None),
    ],
)
def test_root(root: str, station: str | None, report_type: str | None) -> None:
    """Test station and type identification."""
    ret_station, ret_report_type = pirep._root(root)
    assert ret_station == station
    assert ret_report_type == report_type


@pytest.mark.parametrize(
    ("loc", "station", "direction", "distance"),
    [
        ("MLB", "MLB", None, None),
        ("MKK360002", "MKK", 360, 2),
        ("KLGA220015", "KLGA", 220, 15),
        ("10 WGON", "GON", 270, 10),
        ("GON 270010", "GON", 270, 10),
        ("10 EAST", None, 90, 10),
        ("15 SW LRP", "LRP", 225, 15),
        ("3 MILES WEST OF MYF", "MYF", 270, 3),
        ("6 MILES EAST KAGC", "KAGC", 90, 6),
    ],
)
def test_location(loc: str, station: str | None, direction: int | None, distance: int | None) -> None:
    """Test location unpacking."""
    ret_loc = pirep._location(loc)
    assert isinstance(ret_loc, structs.Location)
    assert ret_loc.repr == loc
    assert ret_loc.station == station
    assert_value(ret_loc.direction, direction)
    assert_value(ret_loc.distance, distance)


@pytest.mark.parametrize("time", ["1930", "0000", "2359", "0515"])
def test_time(time: str) -> None:
    """Test time parsing."""
    ret_time = pirep._time(time)
    assert isinstance(ret_time, structs.Timestamp)
    assert ret_time.repr == time
    assert ret_time.dt is not None
    assert ret_time.dt.hour == int(time[:2])
    assert ret_time.dt.minute == int(time[2:])
    assert ret_time.dt.second == 0


def test_not_time() -> None:
    assert pirep._time(None) is None


@pytest.mark.parametrize(("alt", "num"), [("2000", 2000), ("9999", 9999), ("0500", 500)])
def test_altitude(alt: str, num: int) -> None:
    """Test converting altitude to Number."""
    ret_alt = pirep._altitude(alt)
    assert isinstance(ret_alt, structs.Number)
    assert ret_alt.repr == alt
    assert ret_alt.value == num


def test_other_altitude() -> None:
    assert isinstance(pirep._altitude("test"), str)
    assert pirep._altitude("") is None


@pytest.mark.parametrize(
    ("code", "name"),
    [
        ("B752", "Boeing 757-200"),
        ("PC12", "Pilatus PC-12"),
        ("C172", "Cessna 172"),
    ],
)
def test_aircraft(code: str, name: str) -> None:
    """Test converting aircraft code into Aircraft."""
    aircraft = pirep._aircraft(code)
    assert isinstance(aircraft, structs.Aircraft)
    assert aircraft.code == code
    assert aircraft.type == name


def test_unknown_aircraft() -> None:
    code = "not a code"
    assert pirep._aircraft(code) == code


@pytest.mark.parametrize(
    ("cloud", "data"),
    [
        ("OVC100-TOP110", ["OVC", 100, 110]),
        ("OVC065-TOPUNKN", ["OVC", 65, None]),
        ("OVCUNKN-TOP150", ["OVC", None, 150]),
        ("SCT-BKN050-TOP100", ["SCT-BKN", 50, 100]),
        ("BKN-OVCUNKN-TOP060", ["BKN-OVC", None, 60]),
        ("BKN120-TOP150", ["BKN", 120, 150]),
        ("OVC-TOP085", ["OVC", None, 85]),
        ("BASES SCT030 TOPS SCT058", ["SCT", 30, 58]),
        ("TOPS 8000FT BASES 5000FT", [None, 50, 80]),
        ("BKN030-TOP045", ["BKN", 30, 45]),
        ("BASE027-TOPUNKN", [None, 27, None]),
        ("BASES020-TOPS074", [None, 20, 74]),
        ("BASES SCT022 TOPS SCT030-035", ["SCT", 22, 35]),
    ],
)
def test_cloud_tops(cloud: str, data: list) -> None:
    """Test converting clouds with tops."""
    parsed = pirep._clouds(cloud)[0]
    assert isinstance(parsed, structs.Cloud)
    assert parsed.repr == cloud
    for i, key in enumerate(("type", "base", "top")):
        assert getattr(parsed, key) == data[i]


@pytest.mark.parametrize(
    ("num", "value"),
    [
        ("01", 1),
        ("M01", -1),
        ("E", 90),
        ("1/4", 0.25),
        ("28C", 28),
    ],
)
def test_number(num: str, value: int) -> None:
    """Test converting value into a Number."""
    assert_number(pirep._number(num), num, value)


@pytest.mark.parametrize("bad", ["", "LGT RIME"])
def test_not_number(bad: str) -> None:
    assert pirep._number(bad) is None


@pytest.mark.parametrize(
    ("turb", "severity", "floor", "ceiling"),
    [
        ("MOD CHOP", "MOD CHOP", None, None),
        ("LGT-MOD CAT 160-260", "LGT-MOD CAT", 160, 260),
        ("LGT-MOD 180-280", "LGT-MOD", 180, 280),
        ("LGT", "LGT", None, None),
        ("CONT LGT CHOP BLO 250", "CONT LGT CHOP", None, 250),
        ("LGT-NEG-MOD BLO 090-075", "LGT-NEG-MOD", 75, 90),
    ],
)
def test_turbulence(turb: str, severity: str, floor: int | None, ceiling: int | None) -> None:
    """Test converting turbulence string to Turbulence."""
    ret_turb = pirep._turbulence(turb)
    assert isinstance(ret_turb, structs.Turbulence)
    assert ret_turb.severity == severity
    assert_value(ret_turb.floor, floor)
    assert_value(ret_turb.ceiling, ceiling)


@pytest.mark.parametrize(
    ("ice", "severity", "itype", "floor", "ceiling"),
    [
        ("MOD RIME", "MOD", "RIME", None, None),
        ("LGT RIME 025", "LGT", "RIME", 25, 25),
        ("LIGHT MIXED", "LIGHT", "MIXED", None, None),
        ("NEG", "NEG", None, None, None),
        ("TRACE RIME 070-090", "TRACE", "RIME", 70, 90),
        ("LGT RIME 220-260", "LGT", "RIME", 220, 260),
    ],
)
def test_icing(
    ice: str,
    severity: str,
    itype: str | None,
    floor: int | None,
    ceiling: int | None,
) -> None:
    """Test converting icing string to Icing."""
    ret_ice = pirep._icing(ice)
    assert isinstance(ret_ice, structs.Icing)
    assert ret_ice.severity == severity
    assert ret_ice.type == itype
    assert_value(ret_ice.floor, floor)
    assert_value(ret_ice.ceiling, ceiling)


@pytest.mark.parametrize("rmk", ["Test", "12345", "IT WAS MOSTLY SMOOTH"])
def test_remarks(rmk: str) -> None:
    """Test remarks pass through."""
    ret_rmk = pirep._remarks(rmk)
    assert isinstance(ret_rmk, str)
    assert ret_rmk, rmk


@pytest.mark.parametrize(
    ("text", "wx", "vis", "remain"),
    [
        ("VCFC", [("VCFC", "Vicinity Funnel Cloud")], None, []),
        (
            "+RATS -GR 4",
            [("+RATS", "Heavy Rain Thunderstorm"), ("-GR", "Light Hail")],
            None,
            ["4"],
        ),
        ("FV1000 VCFC", [("VCFC", "Vicinity Funnel Cloud")], 1000, []),
    ],
)
def test_wx(text: str, wx: list[tuple[str, str]], vis: int | None, remain: list[str]) -> None:
    """Test wx split and visibility ident."""
    wx_codes, flight_visibility, other = pirep._wx(text)
    assert isinstance(wx_codes, list)
    assert other == remain
    for item, code in zip(wx, wx_codes):
        assert Code(item[0], item[1]) == code
    assert_value(flight_visibility, vis)


# Test Pirep class and parsing


@pytest.mark.parametrize(
    "report",
    [
        "EWR UA /OV SBJ090/010/TM 2108/FL060/TP B738/TB MOD",
        "SMQ UA /OV BWZ/TM 0050/FL280/TP A320/TB MOD",
    ],
)
def test_parse(report: str) -> None:
    """Test returned structs from the parse function."""
    data, sans = pirep.parse(report)
    assert isinstance(data, structs.PirepData)
    assert isinstance(sans, structs.Sanitization)
    assert data.raw == report


@pytest.mark.parametrize(
    ("line", "fixed"),
    [
        ("DAB UA /SK BKN030 TOP045", "DAB UA /SK BKN030-TOP045"),
        ("DAB UA /SK BASES OVC 049 TOPS 055", "DAB UA /SK BASES OVC049 TOPS 055"),
    ],
)
def test_sanitize(line: str, fixed: str) -> None:
    """Test report sanitization."""
    ret_fixed, sans = pirep.sanitize(line)
    assert ret_fixed == fixed
    assert sans.errors_found is True


@pytest.mark.parametrize(("ref", "icao", "issued"), get_data(__file__, "pirep"))
def test_pirep_ete(ref: dict, icao: str, issued: datetime) -> None:
    """Perform an end-to-end test of all PIREP JSON files."""
    station = pirep.Pireps(icao)
    assert station.last_updated is None
    assert station.issued is None
    reports = [report["data"]["raw"] for report in ref["reports"]]
    assert station.parse(reports, issued=issued) is True
    assert isinstance(station.last_updated, datetime)
    assert station.issued == issued
    for parsed, report in zip(station.data, ref["reports"]):
        assert asdict(parsed) == report["data"]
