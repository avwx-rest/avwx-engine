"""Core Tests."""

# ruff: noqa: FBT001

# stdlib
from __future__ import annotations

from datetime import UTC, datetime

# library
import pytest
import time_machine

# module
from avwx import static, structs
from avwx.parsing import core
from avwx.units import Measurement

# tests
from tests.util import assert_timestamp


@pytest.mark.parametrize(
    ("before", "after", "neighbors"),
    [
        ([1, 2, 3, 2, 1], [1, 2, 3], False),
        ([4, 4, 4, 4], [4], False),
        ([1, 5, 1, 1, 3, 5], [1, 5, 3], False),
        ([1, 2, 3, 2, 1], [1, 2, 3, 2, 1], True),
        ([4, 4, 4, 4], [4], True),
        ([1, 5, 1, 1, 3, 5], [1, 5, 1, 3, 5], True),
    ],
)
def test_dedupe(before: list[int], after: list[int], neighbors: bool) -> None:
    """Test list deduplication."""
    assert core.dedupe(before, only_neighbors=neighbors) == after


def test_is_unknown() -> None:
    """Test unknown value when a string value contains only backspace characters or empty."""
    for i in range(10):
        assert core.is_unknown("/" * i) is True


@pytest.mark.parametrize("value", ["abc", "/bc", "a/c", "ab/", "a//", "/b/", "//c"])
def test_is_not_unknown(value: str) -> None:
    """Test full or partially known values."""
    assert core.is_unknown(value) is False


def test_bad_unknown() -> None:
    with pytest.raises(TypeError):
        core.is_unknown(None)  # type: ignore


@pytest.mark.parametrize("ts", ["123456Z", "987654Z"])
def test_is_timestamp(ts: str) -> None:
    """Test determining if a string is a timestamp element."""
    assert core.is_timestamp(ts) is True


@pytest.mark.parametrize("ts", ["", "123456Z123", "1234", "1234Z"])
def test_is_not_timestamp(ts: str) -> None:
    assert core.is_timestamp(ts) is False


@pytest.mark.parametrize(
    ("fraction", "unpacked"),
    [
        ("", ""),
        ("1", "1"),
        ("1/2", "1/2"),
        ("3/2", "1 1/2"),
        ("10/3", "3 1/3"),
    ],
)
def test_unpack_fraction(fraction: str, unpacked: str) -> None:
    """Test unpacking a fraction where the numerator can be greater than the denominator."""
    assert core.unpack_fraction(fraction) == unpacked


@pytest.mark.parametrize(
    ("num", "stripped"),
    [
        ("", ""),
        ("5", "5"),
        ("010", "10"),
        ("M10", "M10"),
        ("M002", "M2"),
        ("-09.9", "-9.9"),
        ("000", "0"),
        ("M00", "0"),
    ],
)
def test_remove_leading_zeros(num: str, stripped: str) -> None:
    """Test removing leading zeros from a number."""
    assert core.remove_leading_zeros(num) == stripped


@pytest.mark.parametrize(
    ("num", "spoken"),
    [
        ("1", "one"),
        ("5", "five"),
        ("20", "two zero"),
        ("937", "nine three seven"),
        ("4.8", "four point eight"),
        ("29.92", "two nine point nine two"),
        ("1/2", "one half"),
        ("3 3/4", "three and three quarters"),
    ],
)
def test_spoken_number(num: str, spoken: str) -> None:
    """Test converting digits into spoken values."""
    assert core.spoken_number(num) == spoken


@pytest.mark.parametrize(
    ("num", "unit", "magnitude"),
    [
        ("1", "ft", 1.0),
        ("1.5", "ft", 1.5),
        ("060", "degree", 60.0),
        ("300", "hPa", 300.0),
        ("25000", "ft", 25000.0),
        ("M10", "degC", -10.0),
    ],
)
def test_make_measurement(num: str, unit: str, magnitude: float) -> None:
    """Test Measurement generation from a number string."""
    m, _ = core.make_measurement(num, unit)
    assert isinstance(m, Measurement)
    assert m.magnitude == magnitude
    assert m.unit == unit


def test_make_measurement_none() -> None:
    m, _ = core.make_measurement("", "ft")
    assert m is None


def test_make_measurement_repr_override() -> None:
    m, repr_str = core.make_measurement("1234", "hPa", "A1234")
    assert m is not None
    assert repr_str == "A1234"
    assert m.magnitude == 1234.0


@pytest.mark.parametrize(
    ("string", "targets", "index"),
    [
        ("012345", ["5", "2", "3"], 2),
        ("This is weird", ["me", "you", "we"], 8),
        ("KJFK NOPE LOL RMK HAHAHA", static.metar.METAR_RMK, 13),
    ],
)
def test_find_first_in_list(string: str, targets: list[str], index: int) -> None:
    """Test a function which finds the first occurrence in a string from a list.

    This is used to find remarks and TAF time periods.
    """
    assert core.find_first_in_list(string, targets) == index


@pytest.mark.parametrize("temp", ["10", "22", "333", "M05", "5"])
def test_is_possible_temp(temp: str) -> None:
    """Test if an element could be a formatted temperature."""
    assert core.is_possible_temp(temp) is True


@pytest.mark.parametrize("temp", ["A", "12.3", "MNA", "-13"])
def test_is_not_possible_temp(temp: str) -> None:
    assert core.is_possible_temp(temp) is False


@pytest.mark.parametrize(
    ("wx", "ret", "station", "time"),
    [
        (["KJFK", "123456Z", "1"], ["1"], "KJFK", "123456Z"),
        (["KJFK", "123456", "1"], ["1"], "KJFK", "123456Z"),
        (["KJFK", "1234Z", "1"], ["1"], "KJFK", "1234Z"),
        (["KJFK", "1234", "1"], ["1234", "1"], "KJFK", None),
        (["KJFK", "1"], ["1"], "KJFK", None),
        (["KJFK"], [], "KJFK", None),
    ],
)
def test_get_station_and_time(wx: list[str], ret: list[str], station: str, time: str | None) -> None:
    """Test removal of station (first item) and potential timestamp."""
    assert core.get_station_and_time(wx) == (ret, station, time)


@pytest.mark.parametrize(
    ("wx", "unit", "wind", "varv"),
    [
        (["1"], "kt", ((None,), (None,), (None,)), []),
        (["12345", "G50", "1"], "kt", (("123", 123), ("45", 45), ("50", 50)), []),
        (["01234G56", "1"], "kt", (("012", 12), ("34", 34), ("56", 56)), []),
        (["G30KT", "1"], "kt", ((None,), (None,), ("30", 30)), []),
        (["10G18KT", "1"], "kt", ((None,), ("10", 10), ("18", 18)), []),
        (
            ["36010KTS", "G20", "300V060", "1"],
            "kt",
            (("360", 360), ("10", 10), ("20", 20)),
            [("300", 300), ("060", 60)],
        ),
        (["VRB10MPS", "1"], "m/s", (("VRB",), ("10", 10), (None,)), []),
        (["VRB20G30KMH", "1"], "km/h", (("VRB",), ("20", 20), ("30", 30)), []),
        (["03015G21MPH", "1"], "mi/h", (("030", 30), ("15", 15), ("21", 21)), []),
        (["16006GP99KT", "1"], "kt", (("160", 160), ("06", 6), ("P99", 99)), []),
    ],
)
def test_get_wind(wx: list[str], unit: str, wind: tuple[tuple], varv: list[tuple]) -> None:
    """Test that the wind item gets removed and split into its components."""
    wx, wind_dir, wind_spd, wind_gust, var, wind_unit, *_ = core.get_wind(wx)
    assert wx == ["1"]
    assert wind_unit == unit
    winds = (wind_dir, wind_spd, wind_gust)
    for parsed, ref in zip(winds, wind, strict=True):
        if ref[0] is None or ref[0] in ("VRB",):
            assert parsed is None
        else:
            assert parsed is not None
            assert parsed.magnitude == ref[1]
    if varv:
        for m, ref in zip(var, varv, strict=True):
            assert m.magnitude == ref[1]


@pytest.mark.parametrize(
    ("wx", "unit", "magnitude"),
    [
        (["1"], "sm", None),
        (["05SM", "1"], "sm", 5.0),
        (["10SM", "1"], "sm", 10.0),
        (["P6SM", "1"], "sm", 6.0),
        (["M1/4SM", "1"], "sm", 0.25),
        (["1/2SM", "1"], "sm", 0.5),
        (["2", "1/2SM", "1"], "sm", 2.5),
        (["1000", "1"], "m", 1000.0),
        (["1000E", "1"], "m", 1000.0),
        (["1000NDV", "1"], "m", 1000.0),
        (["M1000", "1"], "m", 1000.0),
        (["2KM", "1"], "m", 2000.0),
        (["15KM", "1"], "m", 15000.0),
    ],
)
def test_get_visibility(wx: list[str], unit: str, magnitude: float | None) -> None:
    """Test that the visibility item(s) gets removed and cleaned."""
    wx, vis, _raw, vis_unit = core.get_visibility(wx)
    assert wx == ["1"]
    assert vis_unit == unit
    if magnitude is None:
        assert vis is None
    else:
        assert vis is not None
        assert vis.magnitude == magnitude


def test_get_digit_list() -> None:
    """Test that digits are removed after an index but before a non-digit item."""
    items = ["1", "T", "2", "3", "ODD", "Q", "4", "C"]
    items, ret = core.get_digit_list(items, 1)
    assert items == ["1", "ODD", "Q", "4", "C"]
    assert ret == ["2", "3"]
    items, ret = core.get_digit_list(items, 2)
    assert items == ["1", "ODD", "C"]
    assert ret == ["4"]


@pytest.mark.parametrize(
    ("bad", "good"),
    [
        ("OVC", "OVC"),
        ("010", "010"),
        ("SCT060", "SCT060"),
        ("FEWO03", "FEW003"),
        ("BKNC015", "BKN015C"),
        ("FEW027///", "FEW027///"),
        ("UNKN021-TOP023", "UNKN021-TOP023"),
    ],
)
def test_sanitize_cloud(bad: str, good: str) -> None:
    """Test the common cloud issues are fixed before parsing."""
    assert core.sanitize_cloud(bad) == good


@pytest.mark.parametrize(
    ("cloud", "cloud_type", "base_ft", "top_ft", "modifier"),
    [
        ("SCT060", "SCT", 6000, None, None),
        ("FEWO03", "FEW", 300, None, None),
        ("BKNC015", "BKN", 1500, None, "C"),
        ("OVC120TS", "OVC", 12000, None, "TS"),
        ("VV002", "VV", 200, None, None),
        ("SCT", "SCT", None, None, None),
        ("FEW027///", "FEW", 2700, None, None),
        ("FEW//////", "FEW", None, None, None),
        ("FEW///TS", "FEW", None, None, "TS"),
        ("OVC100-TOP110", "OVC", 10000, 11000, None),
        ("OVC065-TOPUNKN", "OVC", 6500, None, None),
        ("SCT-BKN050-TOP100", "SCT-BKN", 5000, 10000, None),
    ],
)
def test_make_cloud(cloud: str, cloud_type: str, base_ft: int | None, top_ft: int | None, modifier: str | None) -> None:
    """Test helper function which returns a Cloud dataclass."""
    ret_cloud, _ = core.make_cloud(cloud)
    assert isinstance(ret_cloud, structs.Cloud)
    assert ret_cloud.type == cloud_type
    assert ret_cloud.modifier == modifier
    if base_ft is None:
        assert ret_cloud.base is None
    else:
        assert ret_cloud.base is not None
        assert ret_cloud.base.magnitude == base_ft
    if top_ft is None:
        assert ret_cloud.top is None
    else:
        assert ret_cloud.top is not None
        assert ret_cloud.top.magnitude == top_ft


@pytest.mark.parametrize(
    ("wx", "clouds"),
    [
        (["1"], []),
        (["SCT060", "1"], [["SCT", 6000, None]]),
        (
            ["OVC100", "1", "VV010", "SCTO50C"],
            [["VV", 1000, None], ["SCT", 5000, "C"], ["OVC", 10000, None]],
        ),
        (["1", "BKN020", "SCT050"], [["BKN", 2000, None], ["SCT", 5000, None]]),
    ],
)
def test_get_clouds(wx: list[str], clouds: list[list]) -> None:
    """Test that clouds are removed, fixed, and split correctly."""
    wx, ret_clouds, _ = core.get_clouds(wx)
    assert wx == ["1"]
    for i, cloud in enumerate(ret_clouds):
        assert isinstance(cloud, structs.Cloud)
        assert cloud.type == clouds[i][0]
        if clouds[i][1] is None:
            assert cloud.base is None
        else:
            assert cloud.base is not None
            assert cloud.base.magnitude == clouds[i][1]
        assert cloud.modifier == clouds[i][2]


@pytest.mark.parametrize(
    ("vis_magnitude", "vis_unit", "vis_repr", "ceiling", "rule"),
    [
        (None, None, None, None, "IFR"),
        (10.0, "sm", None, None, "VFR"),
        (6.0, "sm", "P6SM", None, "VFR"),
        (6.0, "sm", None, ("OVC", 2000), "MVFR"),
        (6.0, "sm", None, ("OVC", 700), "IFR"),
        (2.0, "sm", None, ("OVC", 2000), "IFR"),
        (6.0, "sm", None, ("OVC", 400), "LIFR"),
        (0.5, "sm", None, ("OVC", 3000), "LIFR"),
        (0.25, "sm", "M1/4SM", ("OVC", 3000), "LIFR"),
    ],
)
def test_get_flight_rules(
    vis_magnitude: float | None,
    vis_unit: str | None,
    vis_repr: str | None,
    ceiling: tuple | None,
    rule: str,
) -> None:
    """Test that the proper flight rule is calculated for a set visibility and ceiling."""
    visibility = Measurement(vis_magnitude, vis_unit) if vis_magnitude is not None and vis_unit is not None else None
    cloud = structs.Cloud(type=ceiling[0], base=Measurement(ceiling[1], "ft")) if ceiling else None
    assert static.core.FLIGHT_RULES[core.get_flight_rules(visibility, vis_repr, cloud)] == rule


@pytest.mark.parametrize(
    ("clouds", "ceiling"),
    [
        ([], None),
        ([("FEW", 1000), ("SCT", 1000)], None),
        ([("OVC", None)], None),
        ([("VV", 500)], ("VV", 500)),
        ([("OVC", 2000), ("BKN", 3000)], ("OVC", 2000)),
        ([("OVC", None), ("BKN", 3000)], ("BKN", 3000)),
        ([("FEW", 1000), ("OVC", 2000)], ("OVC", 2000)),
    ],
)
def test_get_ceiling(clouds: list[tuple], ceiling: tuple | None) -> None:
    """Test that the ceiling is properly identified from a list of clouds."""
    cloud_objs = [
        structs.Cloud(type=c[0], base=Measurement(c[1], "ft") if c[1] is not None else None)
        for c in clouds
    ]
    ceiling_obj = structs.Cloud(type=ceiling[0], base=Measurement(ceiling[1], "ft")) if ceiling else None
    assert core.get_ceiling(cloud_objs) == ceiling_obj


@pytest.mark.parametrize("altitude", ["SFC/FL030", "FL020/030", "6000FT/FL020", "300FT"])
def test_is_altitude(altitude: str) -> None:
    """Test if an element is an altitude."""
    assert core.is_altitude(altitude) is True


@pytest.mark.parametrize("value", ["", "50SE", "KFFT"])
def test_is_not_altitude(value: str) -> None:
    assert core.is_altitude(value) is False


@pytest.mark.parametrize(
    ("text", "magnitude", "unit"),
    [
        ("FL030", 30, "ft"),
        ("030", 30, "ft"),
        ("6000FT", 6000, "ft"),
        ("10000FT", 10000, "ft"),
        ("2000M", 2000, "m"),
    ],
)
def test_make_altitude(text: str, magnitude: int, unit: str) -> None:
    """Test converting altitude text into Measurement."""
    altitude, alt_unit = core.make_altitude(text)
    assert altitude is not None
    assert altitude.magnitude == magnitude
    assert alt_unit == unit


def test_parse_date() -> None:
    """Test that report timestamp is parsed into a datetime object."""
    today = datetime.now(tz=UTC)
    rts = today.strftime(r"%d%H%MZ")
    parsed = core.parse_date(rts)
    assert isinstance(parsed, datetime)
    assert parsed.day == today.day
    assert parsed.hour == today.hour
    assert parsed.minute == today.minute


@time_machine.travel("2020-06-22 12:00")
def test_midnight_rollover() -> None:
    """Test that hour > 23 gets rolled into the next day."""
    parsed = core.parse_date("2224")
    assert isinstance(parsed, datetime)
    assert parsed.day == 23
    assert parsed.hour == 0
    assert parsed.minute == 0


@pytest.mark.parametrize(
    ("dt", "fmt", "target"),
    [
        (datetime.now(tz=UTC), r"%d%HZ", False),
        (datetime.now(tz=UTC), r"%d%H%MZ", False),
        (datetime(2010, 2, 2, 2, 2, tzinfo=UTC), r"%d%HZ", True),
        (datetime(2010, 2, 2, 2, 2, tzinfo=UTC), r"%d%H%MZ", True),
    ],
)
def test_make_timestamp(dt: datetime, fmt: str, target: bool) -> None:
    """Test that a report timestamp is converted into a Timestamp dataclass."""
    dt_repr = dt.strftime(fmt)
    target_date = dt.date() if target else None
    dt = dt.replace(second=0, microsecond=0)
    if "%M" not in fmt:
        dt = dt.replace(minute=0)
    ts = core.make_timestamp(dt_repr, target_date=target_date)
    assert_timestamp(ts, dt_repr, dt)


@pytest.mark.parametrize(
    ("temperature", "dewpoint", "humidity"),
    [
        (10, 5, 0.7107),
        (27, 24, 0.83662),
        (15, 0, 0.35868),
        (10, 10, 1.0),
    ],
)
def test_relative_humidity(temperature: int, dewpoint: int, humidity: float) -> None:
    """Test calculating relative humidity from temperatrue and dewpoint."""
    value = core.relative_humidity(temperature, dewpoint)
    assert round(value, 5) == humidity


@pytest.mark.parametrize(
    ("pressure", "altitude", "pressure_altitude"),
    [
        (29.92, 0, 0),
        (30.12, 6400, 6200),
        (30.28, 12000, 11640),
        (29.78, 1200, 1340),
        (30.09, 0, -170),
    ],
)
def test_pressure_altitude(pressure: float, altitude: int, pressure_altitude: int) -> None:
    """Test calculating pressure altitude in feet."""
    value = core.pressure_altitude(Measurement(pressure, "inHg"), altitude)
    assert value.magnitude == pressure_altitude


@pytest.mark.parametrize(
    ("pressure", "temperature", "altitude", "density"),
    [
        (29.92, 15, 0, 0),
        (30.12, 10, 6400, 7136),
        (30.28, -10, 12000, 11520),
        (29.78, 18, 1200, 1988),
        (30.09, 31, 0, 1750),
        (30.02, 0, 0, -1900),
    ],
)
def test_density_altitude(pressure: float, temperature: int, altitude: int, density: int) -> None:
    """Test calculating density altitude in feet."""
    value = core.density_altitude(Measurement(pressure, "inHg"), Measurement(temperature, "degC"), altitude)
    assert value.magnitude == density
