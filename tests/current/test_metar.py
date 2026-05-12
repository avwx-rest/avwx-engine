"""METAR Report Tests."""

# stdlib
from __future__ import annotations

from datetime import datetime

# library
import pytest

# module
from avwx import structs
from avwx.current import metar
from avwx.units import Measurement

# tests
from tests.util import assert_value, get_data


def test_repr() -> None:
    """Test type and code in repr string."""
    assert repr(metar.Metar("KMCO")) == "<avwx.Metar code=KMCO>"


@pytest.mark.parametrize(
    ("raw", "wx", "rmk"),
    [
        ("1 2 3 A2992 RMK Hi", ["1", "2", "3", "A2992"], "RMK Hi"),
        ("1 2 3 A2992 Hi", ["1", "2", "3", "A2992"], "Hi"),
        ("1 2 Q0900 NOSIG", ["1", "2", "Q0900"], "NOSIG"),
        ("1 2 3 BLU+ Hello", ["1", "2", "3"], "BLU+ Hello"),
    ],
)
def test_get_remarks(raw: str, wx: list[str], rmk: str) -> None:
    """Remarks get removed first with the remaining components split into a list."""
    test_wx, test_rmk = metar.get_remarks(raw)
    assert wx == test_wx
    assert rmk == test_rmk


@pytest.mark.parametrize(
    ("wx", "temp", "dew"),
    [
        (["1", "2"], None, None),
        (["1", "2", "07/05"], 7, 5),
        (["07/05", "1", "2"], 7, 5),
        (["M05/M10", "1", "2"], -5, -10),
        (["///20", "1", "2"], None, 20),
        (["10///", "1", "2"], 10, None),
        (["/////", "1", "2"], None, None),
        (["XX/01", "1", "2"], None, 1),
    ],
)
def test_get_temp_and_dew(wx: list[str], temp: int | None, dew: int | None) -> None:
    """Test temperature and dewpoint extraction."""
    ret_wx, ret_temp, ret_dew, *_ = metar.get_temp_and_dew(wx)
    assert ret_wx == ["1", "2"]
    assert_value(ret_temp, temp)
    assert_value(ret_dew, dew)


def test_not_temp_or_dew() -> None:
    assert metar.get_temp_and_dew(["MX/01"]) == (["MX/01"], None, None, None, None)


@pytest.mark.parametrize(
    ("temp", "dew", "rmk", "humidity"),
    [
        (None, None, "", None),
        (12, 5, "", 0.62228),
        (12, 5, "RMK T01230054", 0.62732),
        (None, None, "RMK T00121123", 0.35818),
        (None, 12, "", None),
        (12, None, "", None),
        (12, None, "RMK T12341345", 0.35408),
    ],
)
def test_get_relative_humidity(temp: int | None, dew: int | None, rmk: str, humidity: float | None) -> None:
    """Test calculating relative humidity from available temperatures."""
    temp_meas = Measurement(temp, "degC") if temp is not None else None
    dew_meas = Measurement(dew, "degC") if dew is not None else None
    remarks_info = metar.remarks.parse(rmk)
    value = metar.get_relative_humidity(temp_meas, dew_meas, remarks_info)
    if value is not None:
        value = round(value, 5)
    assert humidity == value


@pytest.mark.parametrize(
    ("text", "magnitude"),
    [
        ("A2992", 29.92),
        ("2992", 29.92),
        ("A3000", 30.00),
        ("Q1000", 1000),
        ("Q.1000", 1000),
        ("Q0998", 998),
        ("Q1000/10", 1000),
        ("QNH3003INS", 30.03),
    ],
)
def test_parse_altimeter(text: str, magnitude: float) -> None:
    """Test that an altimeter is correctly parsed into a Measurement."""
    alt = metar.parse_altimeter(text)
    assert isinstance(alt, Measurement)
    assert alt.magnitude == magnitude


@pytest.mark.parametrize("text", [None, "12/10", "RMK", "ABCDE", "15KM", "10SM"])
def test_bad_altimeter(text: str | None) -> None:
    assert metar.parse_altimeter(text) is None


@pytest.mark.parametrize(
    ("version", "wx", "alt_magnitude", "alt_unit"),
    [
        ("NA", ["1"], None, None),
        ("NA", ["1", "A2992"], 29.92, "inHg"),
        ("NA", ["1", "A3000"], 30.00, "inHg"),
        ("NA", ["1", "2992"], 29.92, "inHg"),
        ("NA", ["1", "A2992", "Q1000"], 29.92, "inHg"),
        ("NA", ["1", "Q1000", "A2992"], 29.92, "inHg"),
        ("NA", ["1", "Q1000"], 1000, "hPa"),
        ("IN", ["1"], None, None),
        ("IN", ["1", "Q.1000"], 1000, "hPa"),
        ("IN", ["1", "Q1000/10"], 1000, "hPa"),
        ("IN", ["1", "A2992", "Q1000"], 1000, "hPa"),
        ("IN", ["1", "Q1000", "A2992"], 1000, "hPa"),
        ("IN", ["1", "A2992"], 29.92, "inHg"),
        ("IN", ["1", "QNH3003INS"], 30.03, "inHg"),
    ],
)
def test_get_altimeter(version: str, wx: list[str], alt_magnitude: float | None, alt_unit: str | None) -> None:
    """Test that the correct altimeter item gets removed from the end of the wx list."""
    ret, ret_alt, _ = metar.get_altimeter(wx, version)
    assert ret == ["1"]
    if alt_magnitude is None:
        assert ret_alt is None
    else:
        assert isinstance(ret_alt, Measurement)
        assert ret_alt.magnitude == alt_magnitude
        assert ret_alt.unit == alt_unit


@pytest.mark.parametrize(
    ("value", "runway", "vis_magnitude", "var_magnitudes", "trend"),
    [
        ("R35L/1000", "35L", 1000, None, None),
        ("R06/M0500", "06", 500, None, None),
        ("R33/////", "33", None, None, None),
        ("R29/A2000", "29", 2000, None, None),
        (
            "R09C/P6000D",
            "09C",
            6000,
            None,
            structs.Code(repr="D", value="decreasing"),
        ),
        (
            "R36/1600V3000U",
            "36",
            None,
            (1600, 3000),
            structs.Code(repr="U", value="increasing"),
        ),
        (
            "R16/5000VP6000FT/U",
            "16",
            None,
            (5000, 6000),
            structs.Code(repr="U", value="increasing"),
        ),
        (
            "R16/1400FT/N",
            "16",
            1400,
            None,
            structs.Code(repr="N", value="no change"),
        ),
    ],
)
def test_parse_runway_visibility(
    value: str,
    runway: str,
    vis_magnitude: int | None,
    var_magnitudes: tuple | None,
    trend: structs.Code | None,
) -> None:
    """Test parsing runway visibility range values."""
    rvr = metar.parse_runway_visibility(value)
    assert rvr.runway == runway
    assert_value(rvr.visibility, vis_magnitude)
    if var_magnitudes:
        for measurement, expected in zip(rvr.variable_visibility, var_magnitudes, strict=True):
            assert_value(measurement, expected)
    assert rvr.trend == trend


@pytest.mark.parametrize(
    ("wx", "count"),
    [
        (["1", "2"], 0),
        (["1", "2", "R10/10"], 1),
        (["1", "2", "R02/05", "R34/04"], 2),
    ],
)
def test_get_runway_visibility(wx: list[str], count: int) -> None:
    """Test extracting runway visibility."""
    items, rvr, _ = metar.get_runway_visibility(wx)
    assert items == ["1", "2"]
    assert len(rvr) == count


def test_sanitize() -> None:
    """Test report sanitization."""
    report = "METAR AUTO KJFK 032151ZVRB08KT FEW034BKN250 ? C A V O K RMK TEST"
    clean = "KJFK 032151Z VRB08KT FEW034 BKN250 CAVOK RMK TEST"
    remarks = "RMK TEST"
    data = ["KJFK", "032151Z", "VRB08KT", "FEW034", "BKN250", "CAVOK"]
    sans = structs.Sanitization(["METAR", "AUTO", "?"], {"C A V O K": "CAVOK"}, extra_spaces_needed=True)
    ret_clean, ret_remarks, ret_data, ret_sans = metar.sanitize(report)
    assert clean == ret_clean
    assert remarks == ret_remarks
    assert data == ret_data
    assert sans == ret_sans


def test_parse() -> None:
    """Test returned structs from the parse function."""
    report = "KJFK 032151Z 16008KT 10SM FEW034 FEW130 BKN250 27/23 A3013 RMK AO2 SLP201"
    data, metar_repr, sans = metar.parse(report[:4], report)
    assert isinstance(data, structs.MetarData)
    assert isinstance(metar_repr, structs.MetarRepr)
    assert isinstance(sans, structs.Sanitization)
    assert metar_repr.raw == report


def test_parse_awos() -> None:
    """Test an AWOS weather report. Only used for advisory."""
    report = "3J0 140347Z AUTO 05003KT 07/02 RMK ADVISORY A01  $"
    data, metar_repr, sans = metar.parse("KJFK", report, use_na=True)
    assert isinstance(data, structs.MetarData)
    assert isinstance(metar_repr, structs.MetarRepr)
    assert isinstance(sans, structs.Sanitization)
    assert metar_repr.raw == report


@pytest.mark.parametrize(("ref", "icao", "issued"), get_data(__file__, "metar"))
def test_metar_ete(ref: dict, icao: str, issued: datetime) -> None:
    """Perform an end-to-end test of all METAR JSON files."""
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
    assert isinstance(station.data, structs.MetarData)
