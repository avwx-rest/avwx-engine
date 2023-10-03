"""
METAR Report Tests
"""

# pylint: disable=invalid-name

# stdlib
from dataclasses import asdict
from datetime import datetime
from typing import List, Optional, Tuple

# library
import pytest

# module
from avwx import static, structs
from avwx.current import metar

# tests
from tests.util import assert_number, get_data


def test_repr():
    """Test type and code in repr string"""
    assert repr(metar.Metar("KMCO")) == "<avwx.Metar code=KMCO>"


@pytest.mark.parametrize(
    "raw,wx,rmk",
    (
        ("1 2 3 A2992 RMK Hi", ["1", "2", "3", "A2992"], "RMK Hi"),
        ("1 2 3 A2992 Hi", ["1", "2", "3", "A2992"], "Hi"),
        ("1 2 Q0900 NOSIG", ["1", "2", "Q0900"], "NOSIG"),
        ("1 2 3 BLU+ Hello", ["1", "2", "3"], "BLU+ Hello"),
    ),
)
def test_get_remarks(raw: str, wx: List[str], rmk: str):
    """Remarks get removed first with the remaining components split into a list"""
    test_wx, test_rmk = metar.get_remarks(raw)
    assert wx == test_wx
    assert rmk == test_rmk


@pytest.mark.parametrize(
    "wx,temp,dew",
    (
        (["1", "2"], (None,), (None,)),
        (["1", "2", "07/05"], ("07", 7), ("05", 5)),
        (["07/05", "1", "2"], ("07", 7), ("05", 5)),
        (["M05/M10", "1", "2"], ("M05", -5), ("M10", -10)),
        (["///20", "1", "2"], (None,), ("20", 20)),
        (["10///", "1", "2"], ("10", 10), (None,)),
        (["/////", "1", "2"], (None,), (None,)),
        (["XX/01", "1", "2"], (None,), ("01", 1)),
    ),
)
def test_get_temp_and_dew(wx: List[str], temp: tuple, dew: tuple):
    """Tests temperature and dewpoint extraction"""
    ret_wx, ret_temp, ret_dew = metar.get_temp_and_dew(wx)
    assert ret_wx == ["1", "2"]
    assert_number(ret_temp, *temp)
    assert_number(ret_dew, *dew)


def test_not_temp_or_dew():
    assert metar.get_temp_and_dew(["MX/01"]) == (["MX/01"], None, None)


@pytest.mark.parametrize(
    "temp,dew,rmk,humidity",
    (
        (None, None, "", None),
        (12, 5, "", 0.62228),
        (12, 5, "RMK T01230054", 0.62732),
        (None, None, "RMK T00121123", 0.35818),
        (None, 12, "", None),
        (12, None, "", None),
        (12, None, "RMK T12341345", 0.35408),
    ),
)
def test_get_relative_humidity(
    temp: Optional[int], dew: Optional[int], rmk: str, humidity: Optional[float]
):
    """Tests calculating relative humidity from available temperatures"""
    units = metar.Units.north_american()
    if temp is not None:
        temp = metar.Number("", temp, "")
    if dew is not None:
        dew = metar.Number("", dew, "")
    remarks_info = metar.remarks.parse(rmk)
    value = metar.get_relative_humidity(temp, dew, remarks_info, units)
    if value is not None:
        value = round(value, 5)
    assert humidity == value


@pytest.mark.parametrize(
    "text,alt",
    (
        ("A2992", (29.92, "two nine point nine two")),
        ("2992", (29.92, "two nine point nine two")),
        ("A3000", (30.00, "three zero point zero zero")),
        ("Q1000", (1000, "one zero zero zero")),
        ("Q.1000", (1000, "one zero zero zero")),
        ("Q0998", (998, "zero nine nine eight")),
        ("Q1000/10", (1000, "one zero zero zero")),
        ("QNH3003INS", (30.03, "three zero point zero three")),
    ),
)
def test_parse_altimeter(text: str, alt: Tuple[float, str]):
    """Tests that an atlimiter is correctly parsed into a Number"""
    assert_number(metar.parse_altimeter(text), text, *alt)


@pytest.mark.parametrize("text", (None, "12/10", "RMK", "ABCDE", "15KM", "10SM"))
def test_bad_altimeter(text: Optional[str]):
    assert metar.parse_altimeter(text) is None


@pytest.mark.parametrize(
    "version,wx,alt,unit",
    (
        ("NA", ["1"], (None,), "inHg"),
        ("NA", ["1", "A2992"], ("A2992", 29.92, "two nine point nine two"), "inHg"),
        (
            "NA",
            ["1", "A3000"],
            ("A3000", 30.00, "three zero point zero zero"),
            "inHg",
        ),
        ("NA", ["1", "2992"], ("2992", 29.92, "two nine point nine two"), "inHg"),
        (
            "NA",
            ["1", "A2992", "Q1000"],
            ("A2992", 29.92, "two nine point nine two"),
            "inHg",
        ),
        (
            "NA",
            ["1", "Q1000", "A2992"],
            ("A2992", 29.92, "two nine point nine two"),
            "inHg",
        ),
        ("NA", ["1", "Q1000"], ("Q1000", 1000, "one zero zero zero"), "hPa"),
        ("IN", ["1"], (None,), "hPa"),
        ("IN", ["1", "Q.1000"], ("Q.1000", 1000, "one zero zero zero"), "hPa"),
        ("IN", ["1", "Q1000/10"], ("Q1000/10", 1000, "one zero zero zero"), "hPa"),
        (
            "IN",
            ["1", "A2992", "Q1000"],
            ("Q1000", 1000, "one zero zero zero"),
            "hPa",
        ),
        (
            "IN",
            ["1", "Q1000", "A2992"],
            ("Q1000", 1000, "one zero zero zero"),
            "hPa",
        ),
        ("IN", ["1", "A2992"], ("A2992", 29.92, "two nine point nine two"), "inHg"),
        (
            "IN",
            ["1", "QNH3003INS"],
            ("QNH3003INS", 30.03, "three zero point zero three"),
            "inHg",
        ),
    ),
)
def test_get_altimeter(version: str, wx: List[str], alt: tuple, unit: str):
    """Tests that the correct alimeter item gets removed from the end of the wx list"""
    units = structs.Units(**getattr(static.core, f"{version}_UNITS"))
    ret, ret_alt = metar.get_altimeter(wx, units, version)
    assert ret == ["1"]
    assert_number(ret_alt, *alt)
    assert units.altimeter == unit


@pytest.mark.parametrize(
    "value,runway,vis,var,trend",
    (
        ("R35L/1000", "35L", ("1000", 1000, "one thousand"), None, None),
        ("R06/M0500", "06", ("M0500", None, "less than five hundred"), None, None),
        ("R33/////", "33", None, None, None),
        (
            "R29/A2000",
            "29",
            ("A2000", None, "greater than two thousand"),
            None,
            None,
        ),
        (
            "R09C/P6000D",
            "09C",
            ("P6000", None, "greater than six thousand"),
            None,
            structs.Code("D", "decreasing"),
        ),
        (
            "R36/1600V3000U",
            "36",
            None,
            (("1600", 1600, "one six hundred"), ("3000", 3000, "three thousand")),
            structs.Code("U", "increasing"),
        ),
        (
            "R16/5000VP6000FT/U",
            "16",
            None,
            (
                ("5000", 5000, "five thousand"),
                ("P6000", None, "greater than six thousand"),
            ),
            structs.Code("U", "increasing"),
        ),
        (
            "R16/1400FT/N",
            "16",
            ("1400", 1400, "one four hundred"),
            None,
            structs.Code("N", "no change"),
        ),
    ),
)
def test_parse_runway_visibility(
    value: str,
    runway: str,
    vis: tuple,
    var: Optional[tuple],
    trend: Optional[structs.Code],
):
    """Tests parsing runway visibility range values"""
    rvr = metar.parse_runway_visibility(value)
    assert rvr.runway == runway
    if vis is None:
        assert rvr.visibility is None
    else:
        assert_number(rvr.visibility, *vis)
    if var:
        for original, items in zip(rvr.variable_visibility, var):
            assert_number(original, *items)
    assert rvr.trend == trend


@pytest.mark.parametrize(
    "wx,count",
    (
        (["1", "2"], 0),
        (["1", "2", "R10/10"], 1),
        (["1", "2", "R02/05", "R34/04"], 2),
    ),
)
def test_get_runway_visibility(wx: List[str], count: int):
    """Tests extracting runway visibility"""
    items, rvr = metar.get_runway_visibility(wx)
    assert items == ["1", "2"]
    assert len(rvr) == count


def test_sanitize():
    """Tests report sanitization"""
    report = "METAR AUTO KJFK 032151ZVRB08KT FEW034BKN250 ? C A V O K RMK TEST"
    clean = "KJFK 032151Z VRB08KT FEW034 BKN250 CAVOK RMK TEST"
    remarks = "RMK TEST"
    data = ["KJFK", "032151Z", "VRB08KT", "FEW034", "BKN250", "CAVOK"]
    sans = structs.Sanitization(
        ["METAR", "AUTO", "?"], {"C A V O K": "CAVOK"}, extra_spaces_needed=True
    )
    ret_clean, ret_remarks, ret_data, ret_sans = metar.sanitize(report)
    assert clean == ret_clean
    assert remarks == ret_remarks
    assert data == ret_data
    assert sans == ret_sans


def test_parse():
    """Tests returned structs from the parse function"""
    report = "KJFK 032151Z 16008KT 10SM FEW034 FEW130 BKN250 27/23 A3013 RMK AO2 SLP201"
    data, units, sans = metar.parse(report[:4], report)
    assert isinstance(data, structs.MetarData)
    assert isinstance(units, structs.Units)
    assert isinstance(sans, structs.Sanitization)
    assert data.raw == report


def test_parse_awos():
    """Tests an AWOS weather report. Only used for advisory"""
    report = "3J0 140347Z AUTO 05003KT 07/02 RMK ADVISORY A01  $"
    data, units, sans = metar.parse("KJFK", report, use_na=True)
    assert isinstance(data, structs.MetarData)
    assert isinstance(units, structs.Units)
    assert isinstance(sans, structs.Sanitization)
    assert data.raw == report
    assert units.altimeter == "inHg"


@pytest.mark.parametrize("ref,icao,issued", get_data(__file__, "metar"))
def test_metar_ete(ref: dict, icao: str, issued: datetime):
    """Performs an end-to-end test of all METAR JSON files"""
    station = metar.Metar(icao)
    raw = ref["data"]["raw"]
    assert station.sanitize(raw) == ref["data"]["sanitized"]
    assert station.last_updated is None
    assert station.issued is None
    assert station.sanitization is None
    assert station.parse(raw, issued=issued) is True
    assert isinstance(station.last_updated, datetime)
    assert station.issued == issued
    assert isinstance(station.sanitization, structs.Sanitization)
    assert asdict(station.data) == ref["data"]
    assert asdict(station.translations) == ref["translations"]
    assert station.summary == ref["summary"]
    assert station.speech == ref["speech"]
