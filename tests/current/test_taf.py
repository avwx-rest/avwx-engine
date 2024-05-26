"""TAF Report Tests."""

# ruff: noqa: SLF001

# stdlib
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

# library
import pytest

# module
from avwx import static, structs
from avwx.current import taf
from avwx.parsing import core
from tests.util import get_data

DATA_DIR = Path(__file__).parent / "data"


TAF_FIELDS = (
    "altimeter",
    "clouds",
    "flight_rules",
    "other",
    "visibility",
    "wind_direction",
    "wind_gust",
    "wind_speed",
    "wx_codes",
    "icing",
    "probability",
    "raw",
    "sanitized",
    "turbulence",
    "wind_shear",
    "type",
    "transition_start",
    "start_time",
    "end_time",
    "wind_variable_direction",
)


def line_struct(fields: dict) -> structs.TafLineData:
    """Create TafLineData with null missing fields."""
    fields = {k: None for k in TAF_FIELDS} | fields
    return structs.TafLineData(**fields)


@pytest.mark.parametrize(
    ("text", "rmk"),
    [
        ("KJFK test", ""),
        ("KJFK test RMK test", "RMK test"),
        ("KJFK test FCST test", "FCST test"),
        ("KJFK test AUTOMATED test", "AUTOMATED test"),
    ],
)
def test_get_taf_remarks(text: str, rmk: str) -> None:
    """Test that remarks are removed from a TAF report."""
    report, remarks = taf.get_taf_remarks(text)
    assert report == "KJFK test"
    assert remarks == rmk


LINE_TEST_PATH = DATA_DIR / "sanitize_taf_line_cases.json"


@pytest.mark.parametrize("case", json.load(LINE_TEST_PATH.open()))
def test_sanitize_line(case: dict) -> None:
    """Test a function which fixes common new-line signifiers in TAF reports."""
    sans = structs.Sanitization()
    fixed = taf.sanitize_line(case["line"], sans)
    assert fixed == case["fixed"]
    assert sans.replaced == case["replaced"]
    assert sans.extra_spaces_needed == case["extra_spaces_needed"]


@pytest.mark.parametrize(
    "line",
    [
        {"type": "TEMPO"},
        {"probability": 30},
        {"probability": "PROBNA"},
        {"type": "FROM", "probability": 30},
    ],
)
def test_is_tempo_or_prob(line: dict) -> None:
    """Test a function which checks that an item signifies a new time period."""
    assert taf._is_tempo_or_prob(line_struct(line)) is True


@pytest.mark.parametrize("line", [{"type": "FROM"}, {"type": "FROM", "probability": None}])
def test_is_not_tempo_or_prob(line: dict) -> None:
    assert taf._is_tempo_or_prob(line_struct(line)) is False


@pytest.mark.parametrize(
    ("wx", "alt", "ice", "turb"),
    [
        (["1"], None, [], []),
        (["1", "512345", "612345"], None, ["612345"], ["512345"]),
        (["QNH1234", "1", "612345"], core.make_number("1234"), ["612345"], []),
    ],
)
def test_get_alt_ice_turb(wx: list[str], alt: core.Number | None, ice: list[str], turb: list[str]) -> None:
    """Test that report global altimeter, icing, and turbulence get removed."""
    assert taf.get_alt_ice_turb(wx) == (["1"], alt, ice, turb)


@pytest.mark.parametrize(
    "item",
    [
        *static.taf.TAF_NEWLINE,
        "PROB30",
        "PROB45",
        "PROBNA",
        "FM12345678",
    ],
)
def test_starts_new_line(item: str) -> None:
    """Test that certain items are identified as new line markers in TAFs."""
    assert taf.starts_new_line(item) is True


@pytest.mark.parametrize("item", ["KJFK", "12345Z", "2010/2020", "FEW060", "RMK"])
def test_doesnt_start_new_line(item: str) -> None:
    assert taf.starts_new_line(item) is False


@pytest.mark.parametrize(
    ("report", "num"),
    [
        ("KJFK test", 1),
        ("KJFK test FM12345678 test", 2),
        ("KJFK test TEMPO test", 2),
        ("KJFK test TEMPO test TEMPO test", 3),
        ("KJFK test PROB30 test TEMPO test", 3),
        ("KJFK test PROB30 TEMPO test TEMPO test", 3),
        (
            "KJFK test 2612/2712 test PROB40 2612/2618 test 2618/2706 test 2706/2709 test 2709/2712 test",
            6,
        ),
    ],
)
def test_split_taf(report: str, num: int) -> None:
    """Test that TAF reports are split into the correct time periods."""
    split = taf.split_taf(report)
    assert len(split) == num
    assert split[0] == "KJFK test"


@pytest.mark.parametrize(
    ("wx", "data"),
    [
        (["1"], ["FROM", None, None, None]),
        (["INTER", "1"], ["INTER", None, None, None]),
        (["TEMPO", "0101/0103", "1"], ["TEMPO", "0101", "0103", None]),
        (["PROB30", "0101/0103", "1"], ["PROB30", "0101", "0103", None]),
        (["BECMG", "0101/0103", "1"], ["BECMG", "0103", None, "0101"]),
        (["FM120000", "1"], ["FROM", "1200", None, None]),
        (["FM1200/1206", "1"], ["FROM", "1200", "1206", None]),
        (["FM120000", "TL120600", "1"], ["FROM", "1200", "1206", None]),
        (["TEMPO", "112000", "1"], ["TEMPO", "1120", None, None]),
    ],
)
def test_get_type_and_times(wx: list[str], data: list[str | None]) -> None:
    """Test TAF line type, start time, and end time extraction."""
    assert taf.get_type_and_times(wx) == (["1"], *data)


def test_find_missing_taf_times() -> None:
    """Test that missing forecast times can be interpretted by preceding periods."""
    good_data: list[dict] = [
        {
            "type": "FROM",
            "transition_start": None,
            "start_time": "3021",
            "end_time": "3023",
        },
        {
            "type": "FROM",
            "transition_start": None,
            "start_time": "3023",
            "end_time": "0105",
        },
        {
            "type": "BECMG",
            "transition_start": "0105",
            "start_time": "0107",
            "end_time": "0108",
        },
        {
            "type": "FROM",
            "transition_start": None,
            "start_time": "0108",
            "end_time": "0114",
        },
    ]
    for line in good_data:
        for key in ("start_time", "end_time", "transition_start"):
            line[key] = core.make_timestamp(line[key])
    good_lines = [line_struct(line) for line in good_data]
    bad_lines: list[structs.TafLineData] = deepcopy(good_lines)
    bad_lines[0].start_time = None
    bad_lines[1].start_time = None
    bad_lines[1].end_time = None
    bad_lines[2].end_time = None  # This None implies normal parsing
    bad_lines[3].end_time = None
    start, end = good_lines[0].start_time, good_lines[-1].end_time
    assert taf.find_missing_taf_times(bad_lines, start, end) == good_lines


@pytest.mark.parametrize(
    "report",
    [
        "SYCJ 071100Z 0712/0812 12003KT 9999 BECMG 0711/ 12003KT 1000 TEMPO 0717/0720 12003KT 5000",
    ],
)
def test_missing_end_times(report: str) -> None:
    """Find missing times from a report string."""
    data, _, _ = taf.parse(report[:4], report)
    assert data is not None
    for line in data.forecast:
        assert isinstance(line.start_time, structs.Timestamp)
        assert isinstance(line.end_time, structs.Timestamp)


@pytest.mark.parametrize(
    ("wx", "temp_max", "temp_min"),
    [
        (["1"], None, None),
        (["1", "TX12/1316Z", "TNM03/1404Z"], "TX12/1316Z", "TNM03/1404Z"),
        (["1", "TM03/1404Z", "T12/1316Z"], "TX12/1316Z", "TNM03/1404Z"),
    ],
)
def test_get_temp_min_and_max(wx: list[str], temp_max: str | None, temp_min: str | None) -> None:
    """Test that temp max and min times are extracted and assigned properly."""
    assert taf.get_temp_min_and_max(wx) == (["1"], temp_max, temp_min)


def test_get_oceania_temp_and_alt() -> None:
    """Test that Oceania-specific elements are identified and removed."""
    items = ["1", "T", "2", "3", "ODD", "Q", "4", "C"]
    items, tlist, qlist = taf.get_oceania_temp_and_alt(items)
    assert items == ["1", "ODD", "C"]
    assert tlist == ["2", "3"]
    assert qlist == ["4"]


@pytest.mark.parametrize(
    ("wx", "shear"),
    [
        (["1", "2"], None),
        (["1", "2", "WS020/07040"], "WS020/07040"),
    ],
)
def test_get_wind_shear(wx: list[str], shear: str | None) -> None:
    """Test extracting wind shear."""
    assert taf.get_wind_shear(wx) == (["1", "2"], shear)


def test_skc_flight_rules() -> None:
    """SKC should prevent temp_cloud lookback instead of missing clouds."""
    report = (
        "KLGB 201120Z 2012/2112 VRB03KT P6SM OVC016 "
        "FM201600 15006KT P6SM BKN021 "
        "FM201930 20008KT P6SM SKC "
        "FM210000 29008KT P6SM SKC "
        "FM210500 VRB03KT P6SM OVC015"
    )
    expected_flight_rules = ["MVFR", "MVFR", "VFR", "VFR", "MVFR"]
    data, *_ = taf.parse(report[:4], report)
    assert isinstance(data, structs.TafData)
    for period, flight_rules in zip(data.forecast, expected_flight_rules):
        assert period.flight_rules == flight_rules


def test_parse() -> None:
    """Test returned structs from the parse function."""
    report = (
        "PHNL 042339Z 0500/0606 06018G25KT P6SM FEW030 SCT060 FM050600 06010KT "
        "P6SM FEW025 SCT060 FM052000 06012G20KT P6SM FEW030 SCT060"
    )
    data, units, sans = taf.parse(report[:4], report)
    assert isinstance(data, structs.TafData)
    assert isinstance(units, structs.Units)
    assert isinstance(sans, structs.Sanitization)
    assert data.raw == report


def test_prob_line() -> None:
    """Even though PROB__ is not in TAF_NEWLINE, it should still separate,
    add a new line, and include the prob value in line.probability
    """
    report = (
        "TAF AMD CYBC 271356Z 2714/2802 23015G25KT P6SM BKN090 "
        "TEMPO 2714/2718 P6SM -SHRA BKN060 OVC090 "
        "FM271800 22015G25KT P6SM OVC040 "
        "TEMPO 2718/2724 6SM -SHRA "
        "PROB30 2718/2724 VRB25G35KT 1SM +TSRA BR BKN020 OVC040CB "
        "FM280000 23008KT P6SM BKN040 RMK FCST BASED ON AUTO OBS. NXT FCST BY 272000Z"
    )
    tafobj = taf.Taf("CYBC")
    assert tafobj.parse(report)
    assert tafobj.data is not None
    lines = tafobj.data.forecast
    assert len(lines) == 6
    assert lines[3].probability is None
    assert lines[4].probability == core.make_number("30")
    assert lines[4].raw.startswith("PROB30") is True


def assert_repr(time: structs.Timestamp | Any | None, repr: str) -> None:  # noqa: A002
    assert isinstance(time, structs.Timestamp)
    assert time.repr == repr


def test_prob_end() -> None:
    """PROB and TEMPO lines are discrete times and should not affect FROM times."""
    report = (
        "MMMX 242331Z 2500/2606 24005KT P6SM VC RA SCT020CB SCT080 BKN200 TX25/2521Z TN14/2513Z "
        "TEMPO 2500/2504 6SM TSRA BKN020CB "
        "FM250600 04010KT P6SM SCT020 BKN080 "
        "TEMPO 2512/2515 3SM HZ BKN015 "
        "FM251600 22005KT 4SM HZ BKN020 "
        "FM251800 22010KT 6SM HZ SCT020 BKN200 "
        "PROB40 2522/2602 P6SM TSRA BKN020CB"
    )
    tafobj = taf.Taf("CYBC")
    assert tafobj.parse(report)
    assert tafobj.data is not None
    lines = tafobj.data.forecast
    assert_repr(lines[0].start_time, "2500")
    assert_repr(lines[0].end_time, "2506")
    assert_repr(lines[1].start_time, "2500")
    assert_repr(lines[1].end_time, "2504")
    assert_repr(lines[-2].start_time, "2518")
    assert_repr(lines[-2].end_time, "2606")
    assert_repr(lines[-1].start_time, "2522")
    assert_repr(lines[-1].end_time, "2602")


@pytest.mark.parametrize(
    ("report", "fixed"),
    [
        (
            "KNGU TAF COR 2315/2415 18011KT 9999 VCTS",
            "TAF COR KNGU 2315/2415 18011KT 9999 VCTS",
        ),
        ("1 2 COR AMD TAF 3 4", "TAF AMD COR 1 2 3 4"),
        ("TAF 1 2", "TAF 1 2"),
        ("TAF AMD COR", "TAF AMD COR"),
        ("1 COR 2 TAF 3", "TAF COR 1 2 3"),
        ("1 2 3 4 5 6 7 8", "1 2 3 4 5 6 7 8"),
        ("1 2 TAF 3 4 5 6 7 8 COR 9", "TAF 1 2 3 4 5 6 7 8 COR 9"),
        ("", ""),
    ],
)
def test_bad_header(report: str, fixed: str) -> None:
    """Should fix the header order for key elements ignoring copies later on."""
    assert taf.fix_report_header(report) == fixed


def test_wind_shear() -> None:
    """Wind shear should be recognized as its own element in addition to wind."""
    report = (
        "TAF AMD CYOW 282059Z 2821/2918 09008KT WS015/20055KT P6SM BKN220 "
        "BECMG 2821/2823 19015G25KT "
        "FM290300 21013G23KT P6SM -SHRA BKN040 OVC100 "
        "TEMPO 2903/2909 4SM BR OVC020 "
        "FM290900 25012KT P6SM SCT030 "
        "FM291300 32017G27KT P6SM OVC030 "
        "TEMPO 2913/2918 P6SM -SHRA OVC020 RMK NXT FCST BY 290000Z"
    )
    tafobj = taf.Taf("CYOW")
    assert tafobj.parse(report)
    assert tafobj.data is not None
    lines = tafobj.data.forecast
    assert len(lines) == 7
    assert lines[0].wind_shear == "WS015/20055"
    assert tafobj.translations is not None
    assert tafobj.translations.forecast[1].clouds == ""


def test_space_in_forcast_times() -> None:
    """Forecast time can occasionally use a space rather than a slash."""
    report = (
        "TAF VIGR 041530Z 0500/0512 04005KT 6000 SCT025 BKN090 "
        "0501 0503 05010KT 4000 -RA/BR SCT015 SCT025 BKN090 "
        "TEMPO 0507 0511 05010G20KT 2000 RASH/TS SCT025 FEWCB035 SCT090"
    )
    tafobj = taf.Taf("VIGR")
    assert tafobj.parse(report)
    assert tafobj.data is not None
    lines = tafobj.data.forecast
    assert len(lines) == 2
    assert lines[0].start_time == core.make_timestamp("0500")
    assert lines[0].end_time == core.make_timestamp("0512")
    assert lines[1].start_time == core.make_timestamp("0507")
    assert lines[1].end_time == core.make_timestamp("0511")


def test_wind_variable_direction() -> None:
    """Variable wind direction should be recognized when present."""
    report = (
        "MNPC 301530Z 3018/3118 16006KT 100V200 5000 RA/TSRA FEW014CB BKN016TCU "
        "BECMG 3100/3102 VRB04KT 6000 -RA/HZ BKN016"
    )
    tafobj = taf.Taf.from_report(report)
    assert tafobj is not None
    assert tafobj.data is not None
    lines = tafobj.data.forecast
    assert len(lines) == 2
    wind_direction = lines[0].wind_variable_direction
    assert wind_direction is not None
    assert len(wind_direction) == 2


def test_prob_tempo() -> None:
    """Non-PROB types should take precident but still fill the probability value."""
    report = (
        "EGLL 192253Z 2000/2106 28006KT 9999 BKN035 "
        "PROB30 TEMPO 2004/2009 BKN012 "
        "PROB30 TEMPO 2105/2106 8000 BKN006"
    )
    tafobj = taf.Taf("EGLL")
    assert tafobj.parse(report)
    assert tafobj.data is not None
    lines = tafobj.data.forecast
    assert len(lines) == 3
    for line in lines:
        assert isinstance(line.start_time, structs.Timestamp)
        assert isinstance(line.end_time, structs.Timestamp)
    for line in lines[1:4]:
        assert line.type == "TEMPO"
        assert isinstance(line.probability, structs.Number)
        assert line.probability.value == 30


@pytest.mark.parametrize(("ref", "icao", "issued"), get_data(__file__, "taf"))
def test_taf_ete(ref: dict, icao: str, issued: datetime) -> None:
    """Perform an end-to-end test of all TAF JSON files."""
    station = taf.Taf(icao)
    assert station.last_updated is None
    assert station.issued is None
    assert station.sanitization is None
    assert station.parse(ref["data"]["raw"], issued=issued) is True
    assert isinstance(station.last_updated, datetime)
    assert station.issued == issued
    assert isinstance(station.sanitization, structs.Sanitization)
    assert asdict(station.data) == ref["data"]
    assert asdict(station.translations) == ref["translations"]
    assert station.summary == ref["summary"]
    assert station.speech == ref["speech"]


def test_rule_inherit() -> None:
    """Test if TAF forecast periods selectively inherit features to calculate flight rules."""
    report = (
        "CYKF 020738Z 0208/0220 34005KT P6SM FEW015 BKN070 "
        "FM020900 VRB03KT P6SM FEW070 SCT120 "
        "BECMG 0214/0216 12006KT "
        "FM021800 14008KT P6SM BKN025 OVC090"
    )
    expected_rules = ("VFR", "VFR", "VFR", "MVFR")
    tafobj = taf.Taf.from_report(report)
    assert isinstance(tafobj, taf.Taf)
    assert tafobj.data is not None
    for i, line in enumerate(tafobj.data.forecast):
        assert line.flight_rules == expected_rules[i]
