"""
AIRMET SIGMET Report Tests
"""

# stdlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# library
import pytest
from shapely.geometry import LineString

# module
from avwx import structs
from avwx.current import airsigmet
from avwx.parsing import core
from avwx.static.core import CARDINAL_DEGREES, IN_UNITS
from avwx.structs import Code, Coord, Movement, Units

# tests
from tests.util import assert_code, assert_value, datetime_parser, round_coordinates


# Used for location filtering tests
COORD_REPORTS = [
    "N1000 W01000 - N1000 E01000 - S1000 E01000 - S1000 W01000",
    "N1000 W00000 - N1000 E02000 - S1000 E02000 - S1000 W00000",
    "N0000 W00000 - N0000 E02000 - S2000 E02000 - S2000 W00000",
    "N0000 W00100 - N0000 E01000 - S2000 E01000 - S2000 W01000",
]
_PRE = "WAUS43 KKCI 230245 CHIT WA 230245 TS VALID UNTIL 230900 NYC FIR "
COORD_REPORTS = [airsigmet.AirSigmet.from_report(_PRE + r) for r in COORD_REPORTS]


def test_repr():
    """Test class name in repr string"""
    assert repr(airsigmet.AirSigmet()) == "<avwx.AirSigmet>"


@pytest.mark.parametrize(
    "source,target",
    (
        ("1...2..3.. 4. 5.1 6.", "1 <elip> 2 <elip> 3 <elip> 4 <break> 5.1 6"),
        ("CIG BLW 010/VIS PCPN/BR/FG.", "CIG BLW 010 <vis> VIS PCPN/BR/FG"),
        (
            "THRU 15Z. FRZLVL...RANGING FROM",
            "THRU 15Z <break> FRZLVL <elip> RANGING FROM",
        ),
        ("AIRMET ICE...NV UT", "AIRMET ICE <elip> NV UT"),
    ),
)
def test_parse_prep(source: str, target: str):
    """Test report elements are replaced to aid parsing"""
    assert airsigmet._parse_prep(source) == target.split()


@pytest.mark.parametrize(
    "repr,type,country,number",
    (
        ("WSRH31", "sigmet", "RH", 31),
        ("WAUS01", "airmet", "US", 1),
    ),
)
def test_bulletin(repr: str, type: str, country: str, number: int):
    """Test Bulletin parsing"""
    bulletin = airsigmet._bulletin(repr)
    assert bulletin.repr == repr
    assert bulletin.type.value == type
    assert bulletin.country == country
    assert bulletin.number == number


@pytest.mark.parametrize(
    "wx,bulletin,issuer,time,correction",
    (
        ("WSCI35 ZGGG 210031 1 2", "WSCI35", "ZGGG", "210031", None),
        ("WAUS46 KKCI 230416 AAA 1 2", "WAUS46", "KKCI", "230416", "AAA"),
    ),
)
def test_header(
    wx: str, bulletin: str, issuer: str, time: str, correction: Optional[str]
):
    """Test report header element extraction"""
    ret_wx, *ret = airsigmet._header(wx.split())
    assert ret_wx == ["1", "2"]
    assert ret[0] == airsigmet._bulletin(bulletin)
    assert ret[1] == issuer
    assert ret[2] == time
    assert ret[3] == correction


@pytest.mark.parametrize(
    "wx,area,report_type,start_time,end_time,station",
    (
        (
            "SIGE CONVECTIVE SIGMET 74E VALID UNTIL 2255Z 1 2",
            "SIGE",
            "CONVECTIVE SIGMET 74E",
            None,
            "2255Z",
            None,
        ),
        (
            "LDZO SIGMET U01 VALID 050200/050600 LDZA- 1 2",
            "LDZO",
            "SIGMET U01",
            "050200",
            "050600",
            "LDZA",
        ),
        (
            "CHIT WA 230245 AIRMET TANGO FOR TURB AND LLWS VALID UNTIL 230900 1 2",
            "CHI",
            "AIRMET TANGO FOR TURB AND LLWS",
            None,
            "230900",
            None,
        ),
        (
            "SBAZ SIGMET 9 VALID 250700/251100 SBAZ - 1 2",
            "SBAZ",
            "SIGMET 9",
            "250700",
            "251100",
            "SBAZ",
        ),
    ),
)
def test_spacetime(
    wx: str,
    area: str,
    report_type: str,
    start_time: Optional[str],
    end_time: str,
    station: Optional[str],
):
    """Text place, type, and timestamp extraction"""
    ret_wx, *ret = airsigmet._spacetime(wx.split())
    assert ret_wx == ["1", "2"]
    assert ret[0] == area
    assert ret[1] == report_type
    assert ret[2] == start_time
    assert ret[3] == end_time
    assert ret[4] == station


@pytest.mark.parametrize(
    "index,targets",
    (
        (1, ("1",)),
        (4, ("4", "8")),
        (2, ("a", "b", "2", "0")),
    ),
)
def test_first_index(index: int, targets: Tuple[str]):
    """Test util to find the first occurence of n strings"""
    source = [str(i) for i in range(10)]
    assert airsigmet._first_index(source, *targets) == index


@pytest.mark.parametrize(
    "wx,region,extra",
    (
        ("FL CSTL WTRS FROM 100SSW", "FL CSTL WTRS", "FROM 100SSW"),
        ("OH LE 50W", "OH LE", "50W"),
        ("OH LE FROM 50W", "OH LE", "FROM 50W"),
        ("ZGZU GUANGZHOU FIR SEV ICE", "ZGZU GUANGZHOU FIR", "SEV ICE"),
    ),
)
def test_region(wx: str, region: str, extra: str):
    """Test region extraction"""
    ret_wx, ret_region = airsigmet._region(wx.split())
    assert ret_wx == extra.split()
    assert ret_region == region


@pytest.mark.parametrize(
    "wx,start,end,extra",
    (
        (
            "OUTLOOK VALID 230555-230955 FROM 30SSW",
            core.make_timestamp("230555"),
            core.make_timestamp("230955"),
            "FROM 30SSW",
        ),
        (
            "THRU 15Z <break> OTLK VALID 0900-1500Z",
            core.make_timestamp("0900", True),
            core.make_timestamp("1500Z", True),
            "THRU 15Z <break>",
        ),
        (
            "VA CLD OBS AT 0110Z SFC/FL160",
            core.make_timestamp("0110Z", True),
            None,
            "VA CLD SFC/FL160",
        ),
    ),
)
def test_time(
    wx: str, start: structs.Timestamp, end: Optional[structs.Timestamp], extra: str
):
    """Test observation start and end time extraction"""
    ret_wx, ret_start, ret_end = airsigmet._time(wx.split())
    assert ret_wx == extra.split()
    assert ret_start == start
    assert ret_end == end


@pytest.mark.parametrize(
    "coord,value",
    (
        ("N1429", 14.29),
        ("S0250", -2.5),
        ("N2900", 29.0),
        ("W09053", -90.53),
        ("E01506", 15.06),
        ("E15000", 150.0),
    ),
)
def test_coord_value(coord: str, value: float):
    """Test string to float coordinate component"""
    assert airsigmet._coord_value(coord) == value


@pytest.mark.parametrize(
    "wx,coord,extra",
    (
        ("1 2 3", None, "1 2 3"),
        (
            "VA FUEGO PSN N1428 W09052 VA",
            Coord(14.28, -90.52, "N1428 W09052"),
            "VA FUEGO VA",
        ),
    ),
)
def test_position(wx: str, coord: Optional[Coord], extra: str):
    """Test position coordinate extraction"""
    ret_wx, ret_coord = airsigmet._position(wx.split())
    assert ret_wx == extra.split()
    assert ret_coord == coord


@pytest.mark.parametrize(
    "wx,movement,unit,extra",
    (
        ("1 2 3", None, "kt", "1 2 3"),
        ("270226Z CNL MOV CNL", None, "kt", "270226Z CNL"),
        (
            "SFC/FL030 STNR WKN=",
            Movement("STNR", None, core.make_number("STNR")),
            "kt",
            "SFC/FL030 WKN=",
        ),
        (
            "FL060/300 MOV E 45KMH NC=",
            Movement(
                "MOV E 45KMH",
                core.make_number("E", literal=True, special=CARDINAL_DEGREES),
                core.make_number("45"),
            ),
            "kmh",
            "FL060/300 NC=",
        ),
        (
            "AREA TS MOV FROM 23040KT",
            Movement(
                "MOV FROM 23040KT", core.make_number("230"), core.make_number("40")
            ),
            "kt",
            "AREA TS",
        ),
        (
            "ABV FL040 MOV NW",
            Movement(
                "MOV NW",
                core.make_number("NW", literal=True, special=CARDINAL_DEGREES),
                None,
            ),
            "kt",
            "ABV FL040",
        ),
        (
            "TOP FL480 MOV W 05-10KT",
            Movement(
                "MOV W 05-10KT",
                core.make_number("W", literal=True, special=CARDINAL_DEGREES),
                core.make_number("10"),
            ),
            "kt",
            "TOP FL480",
        ),
        (
            "TOP FL390 MOV N/NE 08KT",
            Movement(
                "MOV N/NE 08KT",
                core.make_number("NNE", literal=True, special=CARDINAL_DEGREES),
                core.make_number("08"),
            ),
            "kt",
            "TOP FL390",
        ),
    ),
)
def test_movement(wx: str, movement: Optional[Movement], unit: str, extra: str):
    """Test weather movement extraction"""
    units = Units(**IN_UNITS)
    ret_wx, units, ret_movement = airsigmet._movement(wx.split(), units)
    assert ret_wx == extra.split()
    assert ret_movement == movement
    assert units.wind_speed == unit


@pytest.mark.parametrize(
    "report,bounds,start,extra",
    (
        (
            "FCST N OF N2050 AND S OF N2900 FL060/300",
            ["N OF N2050", "S OF N2900"],
            5,
            "FCST   AND   FL060/300",
        ),
        ("FCST N OF N33 TOP", ["N OF N33"], 5, "FCST   TOP"),
    ),
)
def test_bounds_from_latterals(report: str, bounds: List[str], start: int, extra: str):
    """Test extracting latteral bound strings from the report"""
    ret_report, ret_bounds, ret_start = airsigmet._bounds_from_latterals(report, -1)
    assert ret_report == extra
    assert ret_bounds == bounds
    assert ret_start == start


@pytest.mark.parametrize(
    "report,coords,start,extra",
    (
        (
            "LINE BTN N6916 W06724 - N6825 W06700 - N6753 W06524",
            ((69.16, -67.24), (68.25, -67.00), (67.53, -65.24)),
            9,
            "LINE BTN      ",
        ),
        (
            "WI N4523 E01356 <break> N6753 W06524",
            ((45.23, 13.56),),
            3,
            "WI   <break> N6753 W06524",
        ),
    ),
)
def test_coords_from_text(report: str, coords: Tuple[tuple], start: int, extra: str):
    """Test extracting coords from NESW string pairs in the report"""
    ret_report, ret_coords, ret_start = airsigmet._coords_from_text(report, -1)
    assert ret_report == extra
    assert ret_start == start
    for coord, (lat, lon) in zip(ret_coords, coords):
        assert coord.lat == lat
        assert coord.lon == lon


@pytest.mark.parametrize(
    "report,coords,start,extra",
    (
        (
            "1 FROM 30SSW BNA-40W MGM-30ENE LSU 1",
            ((35.67, -86.92), (32.22, -87.11), (4.74, 115.96)),
            7,
            "1 FROM     1",
        ),
        (
            "FROM 100SSW TLH-80W PIE-160WSW SRQ",
            ((28.85, -85.08), (27.9, -84.19), (26.35, -85.3)),
            5,
            "FROM    ",
        ),
    ),
)
def test_coords_from_navaids(report: str, coords: Tuple[tuple], start: int, extra: str):
    """Test extracting coords from relative navaidlocations in the report"""
    ret_report, ret_coords, ret_start = airsigmet._coords_from_navaids(report, -1)
    assert ret_report == extra
    assert ret_start == start
    for coord, (lat, lon) in zip(ret_coords, coords):
        assert round(coord.lat, 2) == lat
        assert round(coord.lon, 2) == lon


@pytest.mark.parametrize(
    "wx,coords,bounds,extra",
    (
        (
            "FCST N OF N2050 AND S OF N2900 FL060/300",
            [],
            ["N OF N2050", "S OF N2900"],
            "FCST FL060/300",
        ),
        (
            "LINE BTN N6916 W06724 - N6825 W06700 - N6753 W06524",
            ((69.16, -67.24), (68.25, -67.00), (67.53, -65.24)),
            [],
            "LINE BTN",
        ),
        (
            "OBS WI N4523 E01356 <break> N6753 W06524",
            ((45.23, 13.56),),
            [],
            "<break> N6753 W06524",
        ),
        (
            "1 FROM 30SSW BNA-40W MGM-30ENE LSU 1",
            ((35.67, -86.92), (32.22, -87.11), (4.74, 115.96)),
            [],
            "1 1",
        ),
        (
            "FROM 100SSW TLH-80W PIE-160WSW SRQ",
            ((28.85, -85.08), (27.9, -84.19), (26.35, -85.3)),
            [],
            "",
        ),
    ),
)
def test_bounds(wx: str, coords: Tuple[tuple], bounds: List[str], extra: str):
    """Test extracting all pre-break bounds and coordinates from the report"""
    ret_wx, ret_coords, ret_bounds = airsigmet._bounds(wx.split())
    assert ret_wx == extra.split()
    assert ret_bounds == bounds
    for coord, (lat, lon) in zip(ret_coords, coords):
        assert round(coord.lat, 2) == lat
        assert round(coord.lon, 2) == lon


@pytest.mark.parametrize(
    "wx,floor,ceiling,unit,extra",
    (
        ("1 FL060/300 2", 60, 300, "ft", "1 2"),
        ("0110Z SFC/FL160", 0, 160, "ft", "0110Z"),
        ("0110Z SFC/10000FT", 0, 10000, "ft", "0110Z"),
        ("1 TOPS TO FL310 <break> 2", None, 310, "ft", "1 <break> 2"),
        ("1 SFC/2000M 2", 0, 2000, "m", "1 2"),
        ("1 TOPS ABV FL450 2", None, 450, "ft", "1 2"),
        ("TURB BTN FL180 AND FL330", 180, 330, "ft", "TURB"),
        ("1 CIG BLW 010 2", None, 10, "ft", "1 2"),
        ("1 TOP BLW FL380 2", None, 380, "ft", "1 2"),
    ),
)
def test_altitudes(
    wx: str, floor: Optional[int], ceiling: Optional[int], unit: str, extra: str
):
    """Tests extracting floor and ceiling altitudes from report"""
    units = Units(**IN_UNITS)
    ret_wx, units, ret_floor, ret_ceiling = airsigmet._altitudes(wx.split(), units)
    assert ret_wx == extra.split()
    assert units.altitude == unit
    assert_value(ret_floor, floor)
    assert_value(ret_ceiling, ceiling)


@pytest.mark.parametrize(
    "wx,code,name,extra",
    (
        ("1 2 3 4", None, None, "1 2 3 4"),
        ("FIR SEV ICE FCST N", "SEV ICE", "Severe icing", "FIR FCST N"),
        ("W09052 VA CLD OBS AT", "VA CLD", "Volcanic cloud", "W09052 OBS AT"),
    ),
)
def test_weather_type(wx: str, code: Optional[str], name: Optional[str], extra: str):
    """Tests extracting weather type code from report"""
    ret_wx, weather = airsigmet._weather_type(wx.split())
    assert ret_wx == extra.split()
    assert_code(weather, code, name)


@pytest.mark.parametrize(
    "wx,code,name,extra",
    (
        ("1 2 3 4", None, None, "1 2 3 4"),
        ("1 2 3 NC", "NC", "No change", "1 2 3"),
        ("1 2 3 INTSF", "INTSF", "Intensifying", "1 2 3"),
        ("1 2 3 WKN", "WKN", "Weakening", "1 2 3"),
    ),
)
def test_intensity(wx: str, code: Optional[str], name: Optional[str], extra: str):
    """Tests extracting intensity code from report"""
    ret_wx, intensity = airsigmet._intensity(wx.split())
    assert ret_wx == extra.split()
    assert_code(intensity, code, name)


@pytest.mark.parametrize(
    "report,clean",
    (
        ("WAUS43 KKCI  1 \n 2 3 NC=", "WAUS43 KKCI 1 2 3 NC"),
        ("TOP FL520 MO V NNW 05KT NC", "TOP FL520 MOV NNW 05KT NC"),
        ("FL450 MOV NE05KT INTSF=", "FL450 MOV NE 05KT INTSF"),
    ),
)
def test_sanitize(report: str, clean: str):
    """Tests report sanitization"""
    assert airsigmet.sanitize(report) == clean


def test_parse():
    """Tests returned structs from the parse function"""
    report = (
        "WAUS43 KKCI 230245 CHIT WA 230245 AIRMET TANGO FOR TURB AND LLWS "
        "VALID UNTIL 230900 AIRMET TURB...ND SD NE MN IA WI LM LS MI LH "
        "FROM 70N SAW TO SSM TO YVV TO 50SE GRB TO 20SW DLL TO ONL TO BFF "
        "TO 70SW RAP TO 50W DIK TO BIS TO 50SE BJI TO 70N SAW MOD TURB "
        "BTN FL180 AND FL330. CONDS CONTG BYD 09Z THRU 15Z"
    )
    data, units = airsigmet.parse(report)
    assert isinstance(data, structs.AirSigmetData)
    assert isinstance(units, structs.Units)
    assert data.raw == report


@pytest.mark.parametrize(
    "lat,lon,results",
    (
        (5, 5, (True, True, False, False)),
        (5, -15, (False, False, False, False)),
        (5, 15, (False, True, False, False)),
        (5, -5, (True, False, False, False)),
        (0, 0, (True, False, False, False)),
    ),
)
def test_contains(lat: int, lon: int, results: tuple):
    """Tests if report contains a coordinate"""
    coord = Coord(lat, lon)
    for report, result in zip(COORD_REPORTS, results):
        assert report.contains(coord) == result


@pytest.mark.parametrize(
    "coords,results",
    (
        (((20, 20), (0, 0), (-20, -20)), (True, True, True, True)),
        (((20, 20), (10, 0), (-20, -20)), (True, True, False, False)),
        (((-20, 20), (-10, -10), (-20, -20)), (True, False, True, True)),
        (((-20, 20), (-15, -15), (-20, -20)), (False, False, True, True)),
    ),
)
def test_intersects(coords: tuple, results: tuple):
    """Testsif report intersects a path"""
    path = LineString(coords)
    for report, result in zip(COORD_REPORTS, results):
        assert report.intersects(path) == result


AIRSIG_PATH = Path(__file__).parent / "data" / "airsigmet.json"


@pytest.mark.parametrize(
    "ref", json.load(AIRSIG_PATH.open(), object_hook=datetime_parser)
)
def test_airsigmet_ete(ref: dict):
    """Performs an end-to-end test of reports in the AIRSIGMET JSON file"""
    created = ref.pop("created").date()
    airsig = airsigmet.AirSigmet()
    assert airsig.last_updated is None
    assert airsig.issued is None
    assert airsig.parse(ref["data"]["raw"], issued=created) is True
    assert isinstance(airsig.last_updated, datetime)
    assert airsig.issued == created
    assert round_coordinates(asdict(airsig.data)) == ref["data"]


# Tests AirSigManager filtering


@pytest.mark.parametrize(
    "lat,lon,count",
    (
        (5, 5, 2),
        (5, -15, 0),
        (5, 15, 1),
        (5, -5, 1),
        (0, 0, 1),
    ),
)
def test_contains(lat: int, lon: int, count: int):
    """Tests filtering reports that contain a coordinate"""
    manager = airsigmet.AirSigManager()
    manager.reports = COORD_REPORTS
    coord = Coord(lat, lon)
    assert len(manager.contains(coord)) == count


@pytest.mark.parametrize(
    "coords,count",
    (
        (((20, 20), (0, 0), (-20, -20)), 4),
        (((20, 20), (10, 0), (-20, -20)), 2),
        (((-20, 20), (-10, -10), (-20, -20)), 3),
        (((-20, 20), (-15, -15), (-20, -20)), 2),
    ),
)
def test_along(coords: tuple, count: int):
    """Tests filtering reports the fall along a flight path"""
    manager = airsigmet.AirSigManager()
    manager.reports = COORD_REPORTS
    path = [Coord(c[0], c[1]) for c in coords]
    assert len(manager.along(path)) == count
