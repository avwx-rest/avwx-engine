"""
Core Tests
"""

# pylint: disable=too-many-public-methods,invalid-name

# stdlib
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple, Union

# library
import pytest
import time_machine

# module
from avwx import static, structs
from avwx.parsing import core
from avwx.structs import Fraction, Number, Units

# tests
from tests.util import assert_number, assert_timestamp


@pytest.mark.parametrize(
    "before,after,neighbors",
    (
        ([1, 2, 3, 2, 1], [1, 2, 3], False),
        ([4, 4, 4, 4], [4], False),
        ([1, 5, 1, 1, 3, 5], [1, 5, 3], False),
        ([1, 2, 3, 2, 1], [1, 2, 3, 2, 1], True),
        ([4, 4, 4, 4], [4], True),
        ([1, 5, 1, 1, 3, 5], [1, 5, 1, 3, 5], True),
    ),
)
def test_dedupe(before: List[int], after: List[int], neighbors: bool):
    """Tests list deduplication"""
    assert core.dedupe(before, only_neighbors=neighbors) == after


def test_is_unknown():
    """Tests unknown value when a string value contains only backspace characters or empty"""
    for i in range(10):
        assert core.is_unknown("/" * i) is True


@pytest.mark.parametrize("value", ("abc", "/bc", "a/c", "ab/", "a//", "/b/", "//c"))
def test_is_not_unknown(value: str):
    """Tests full or partially known values"""
    assert core.is_unknown(value) is False


def test_bad_unknown():
    with pytest.raises(TypeError):
        core.is_unknown(None)


@pytest.mark.parametrize("ts", ("123456Z", "987654Z"))
def test_is_timestamp(ts: str):
    """Tests determining if a string is a timestamp element"""
    assert core.is_timestamp(ts) is True


@pytest.mark.parametrize("ts", ("", "123456Z123", "1234", "1234Z"))
def test_is_not_timestamp(ts: str):
    assert core.is_timestamp(ts) is False


@pytest.mark.parametrize(
    "fraction,unpacked",
    (
        ("", ""),
        ("1", "1"),
        ("1/2", "1/2"),
        ("3/2", "1 1/2"),
        ("10/3", "3 1/3"),
    ),
)
def test_unpack_fraction(fraction: str, unpacked: str):
    """Tests unpacking a fraction where the numerator can be greater than the denominator"""
    assert core.unpack_fraction(fraction) == unpacked


@pytest.mark.parametrize(
    "num,stripped",
    (
        ("", ""),
        ("5", "5"),
        ("010", "10"),
        ("M10", "M10"),
        ("M002", "M2"),
        ("-09.9", "-9.9"),
        ("000", "0"),
        ("M00", "0"),
    ),
)
def test_remove_leading_zeros(num: str, stripped: str):
    """Tests removing leading zeros from a number"""
    assert core.remove_leading_zeros(num) == stripped


@pytest.mark.parametrize(
    "num,spoken",
    (
        ("1", "one"),
        ("5", "five"),
        ("20", "two zero"),
        ("937", "nine three seven"),
        ("4.8", "four point eight"),
        ("29.92", "two nine point nine two"),
        ("1/2", "one half"),
        ("3 3/4", "three and three quarters"),
    ),
)
def test_spoken_number(num: str, spoken: str):
    """Tests converting digits into spoken values"""
    assert core.spoken_number(num) == spoken


@pytest.mark.parametrize(
    "num,value,spoken",
    (
        ("1", 1, "one"),
        ("1.5", 1.5, "one point five"),
        ("060", 60, "six zero"),
        ("300", 300, "three hundred"),
        ("25000", 25000, "two five thousand"),
        ("M10", -10, "minus one zero"),
        ("FL310", 310, "flight level three one zero"),
        ("ABV FL480", 480, "above flight level four eight zero"),
    ),
)
def test_make_number(num: str, value: Union[int, float, None], spoken: str):
    """Tests Number dataclass generation from a number string"""
    number = core.make_number(num)
    assert isinstance(number, Number)
    assert number.repr == num
    assert number.value == value
    assert number.spoken == spoken


@pytest.mark.parametrize(
    "num,value,spoken",
    (
        ("P6SM", None, "greater than six"),
        ("M1/4", None, "less than one quarter"),
    ),
)
def test_make_number_gt_lt(num: str, value: Union[int, float, None], spoken: str):
    """Tests Number dataclass generation when using P/M for greater/less than"""
    number = core.make_number(num, m_minus=False)
    assert isinstance(number, Number)
    assert number.repr == num
    assert number.value == value
    assert number.spoken == spoken


def test_make_non_number():
    assert core.make_number("") is None


def test_make_number_repr_override():
    assert core.make_number("1234", "A1234").repr == "A1234"


@pytest.mark.parametrize(
    "num,value,spoken,nmr,dnm,norm",
    (
        ("1/4", 0.25, "one quarter", 1, 4, "1/4"),
        ("5/2", 2.5, "two and one half", 5, 2, "2 1/2"),
        ("2-1/2", 2.5, "two and one half", 5, 2, "2 1/2"),
        ("3/4", 0.75, "three quarters", 3, 4, "3/4"),
        ("5/4", 1.25, "one and one quarter", 5, 4, "1 1/4"),
        ("11/4", 1.25, "one and one quarter", 5, 4, "1 1/4"),
    ),
)
def test_make_number_fractions(
    num: str, value: float, spoken: str, nmr: int, dnm: int, norm: str
):
    """Tests Fraction dataclass generation from a number string"""
    number = core.make_number(num)
    assert isinstance(number, Fraction)
    assert number.value == value
    assert number.spoken == spoken
    assert number.numerator == nmr
    assert number.denominator == dnm
    assert number.normalized == norm


def test_make_number_speech():
    """Tests Number generation speech overrides"""
    number = core.make_number("040", speak="040")
    assert number.value == 40
    assert number.spoken == "zero four zero"
    number = core.make_number("100", literal=True)
    assert number.value == 100
    assert number.spoken == "one zero zero"


@pytest.mark.parametrize(
    "string,targets,index",
    (
        ("012345", ("5", "2", "3"), 2),
        ("This is weird", ("me", "you", "we"), 8),
        ("KJFK NOPE LOL RMK HAHAHA", static.metar.METAR_RMK, 13),
    ),
)
def test_find_first_in_list(string: str, targets: Tuple[str], index: int):
    """Tests a function which finds the first occurrence in a string from a list

    This is used to find remarks and TAF time periods
    """
    assert core.find_first_in_list(string, targets) == index


@pytest.mark.parametrize("temp", ("10", "22", "333", "M05", "5"))
def test_is_possible_temp(temp: str):
    """Tests if an element could be a formatted temperature"""
    assert core.is_possible_temp(temp) is True


@pytest.mark.parametrize("temp", ("A", "12.3", "MNA", "-13"))
def test_is_not_possible_temp(temp: str):
    assert core.is_possible_temp(temp) is False


@pytest.mark.parametrize(
    "wx,ret,station,time",
    (
        (["KJFK", "123456Z", "1"], ["1"], "KJFK", "123456Z"),
        (["KJFK", "123456", "1"], ["1"], "KJFK", "123456Z"),
        (["KJFK", "1234Z", "1"], ["1"], "KJFK", "1234Z"),
        (["KJFK", "1234", "1"], ["1234", "1"], "KJFK", None),
        (["KJFK", "1"], ["1"], "KJFK", None),
        (["KJFK"], [], "KJFK", None),
    ),
)
def test_get_station_and_time(
    wx: List[str], ret: List[str], station: str, time: Optional[str]
):
    """Tests removal of station (first item) and potential timestamp"""
    assert core.get_station_and_time(wx) == (ret, station, time)


@pytest.mark.parametrize(
    "wx,unit,wind,varv",
    (
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
        (["16006GP99KT", "1"], "kt", (("160", 160), ("06", 6), ("P99", None)), []),
    ),
)
def test_get_wind(wx: List[str], unit: str, wind: Tuple[tuple], varv: List[tuple]):
    """Tests that the wind item gets removed and split into its components"""
    # Both use knots as the default unit, so just test North American default
    units = structs.Units.north_american()
    wx, *winds, var = core.get_wind(wx, units)
    assert wx == ["1"]
    for parsed, ref in zip(winds, wind):
        assert_number(parsed, *ref)
    if varv:
        assert isinstance(varv, list)
        for i in range(2):
            assert_number(var[i], *varv[i])
    assert units.wind_speed == unit


@pytest.mark.parametrize(
    "wx,unit,visibility",
    (
        (["1"], "sm", (None,)),
        (["05SM", "1"], "sm", ("5", 5)),
        (["10SM", "1"], "sm", ("10", 10)),
        (["P6SM", "1"], "sm", ("P6",)),
        (["M1/2SM", "1"], "sm", ("M1/2",)),
        (["M1/4SM", "1"], "sm", ("M1/4",)),
        (["1/2SM", "1"], "sm", ("1/2", 0.5)),
        (["2", "1/2SM", "1"], "sm", ("5/2", 2.5)),
        (["1000", "1"], "m", ("1000", 1000)),
        (["1000E", "1"], "m", ("1000", 1000)),
        (["1000NDV", "1"], "m", ("1000", 1000)),
        (["M1000", "1"], "m", ("1000", 1000)),
        (["2KM", "1"], "m", ("2000", 2000)),
        (["15KM", "1"], "m", ("15000", 15000)),
    ),
)
def test_get_visibility(wx: List[str], unit: str, visibility: tuple):
    """Tests that the visibility item(s) gets removed and cleaned"""
    units = structs.Units.north_american()
    wx, vis = core.get_visibility(wx, units)
    assert wx == ["1"]
    assert units.visibility == unit
    assert_number(vis, *visibility)


def test_get_digit_list():
    """Tests that digits are removed after an index but before a non-digit item"""
    items = ["1", "T", "2", "3", "ODD", "Q", "4", "C"]
    items, ret = core.get_digit_list(items, 1)
    assert items == ["1", "ODD", "Q", "4", "C"]
    assert ret == ["2", "3"]
    items, ret = core.get_digit_list(items, 2)
    assert items == ["1", "ODD", "C"]
    assert ret == ["4"]


@pytest.mark.parametrize(
    "bad,good",
    (
        ("OVC", "OVC"),
        ("010", "010"),
        ("SCT060", "SCT060"),
        ("FEWO03", "FEW003"),
        ("BKNC015", "BKN015C"),
        ("FEW027///", "FEW027///"),
        ("UNKN021-TOP023", "UNKN021-TOP023"),
    ),
)
def test_sanitize_cloud(bad: str, good: str):
    """Tests the common cloud issues are fixed before parsing"""
    assert core.sanitize_cloud(bad) == good


@pytest.mark.parametrize(
    "cloud,out",
    (
        ("SCT060", ["SCT", 60, None, None]),
        ("FEWO03", ["FEW", 3, None, None]),
        ("BKNC015", ["BKN", 15, None, "C"]),
        ("OVC120TS", ["OVC", 120, None, "TS"]),
        ("VV002", ["VV", 2, None, None]),
        ("SCT", ["SCT", None, None, None]),
        ("FEW027///", ["FEW", 27, None, None]),
        ("FEW//////", ["FEW", None, None, None]),
        ("FEW///TS", ["FEW", None, None, "TS"]),
        ("OVC100-TOP110", ["OVC", 100, 110, None]),
        ("OVC065-TOPUNKN", ["OVC", 65, None, None]),
        ("SCT-BKN050-TOP100", ["SCT-BKN", 50, 100, None]),
    ),
)
def test_make_cloud(cloud: str, out: List[Any]):
    """Tests helper function which returns a Cloud dataclass"""
    ret_cloud = core.make_cloud(cloud)
    assert isinstance(ret_cloud, structs.Cloud)
    assert ret_cloud.repr == cloud
    for i, key in enumerate(("type", "base", "top", "modifier")):
        assert getattr(ret_cloud, key) == out[i]


@pytest.mark.parametrize(
    "wx,clouds",
    (
        (["1"], []),
        (["SCT060", "1"], [["SCT", 60, None]]),
        (
            ["OVC100", "1", "VV010", "SCTO50C"],
            [["VV", 10, None], ["SCT", 50, "C"], ["OVC", 100, None]],
        ),
        (["1", "BKN020", "SCT050"], [["BKN", 20, None], ["SCT", 50, None]]),
    ),
)
def test_get_clouds(wx: List[str], clouds: List[list]):
    """Tests that clouds are removed, fixed, and split correctly"""
    wx, ret_clouds = core.get_clouds(wx)
    assert wx == ["1"]
    for i, cloud in enumerate(ret_clouds):
        assert isinstance(cloud, structs.Cloud)
        for j, key in enumerate(("type", "base", "modifier")):
            assert getattr(cloud, key) == clouds[i][j]


@pytest.mark.parametrize(
    "vis,ceiling,rule",
    (
        (None, None, "IFR"),
        ("10", None, "VFR"),
        ("P6SM", ["OCV", 50], "VFR"),
        ("6", ["OVC", 20], "MVFR"),
        ("6", ["OVC", 7], "IFR"),
        ("2", ["OVC", 20], "IFR"),
        ("6", ["OVC", 4], "LIFR"),
        ("1/2", ["OVC", 30], "LIFR"),
        ("M1/4", ["OVC", 30], "LIFR"),
    ),
)
def test_get_flight_rules(vis: Optional[str], ceiling: Optional[tuple], rule: str):
    """Tests that the proper flight rule is calculated for a set visibility and ceiling

    Note: Only 'Broken', 'Overcast', and 'Vertical Visibility' are considered ceilings
    """
    vis = core.make_number(vis, m_minus=False)
    if ceiling:
        ceiling = structs.Cloud(None, *ceiling)
    assert static.core.FLIGHT_RULES[core.get_flight_rules(vis, ceiling)] == rule


@pytest.mark.parametrize(
    "clouds,ceiling",
    (
        ([], None),
        ([["FEW", 10], ["SCT", 10]], None),
        ([["OVC", None]], None),
        ([["VV", 5]], ["VV", 5]),
        ([["OVC", 20], ["BKN", 30]], ["OVC", 20]),
        ([["OVC", None], ["BKN", 30]], ["BKN", 30]),
        ([["FEW", 10], ["OVC", 20]], ["OVC", 20]),
    ),
)
def test_get_ceiling(clouds: List[list], ceiling: list):
    """Tests that the ceiling is properly identified from a list of clouds"""
    clouds = [structs.Cloud(None, *cloud) for cloud in clouds]
    if ceiling:
        ceiling = structs.Cloud(None, *ceiling)
    assert core.get_ceiling(clouds) == ceiling


@pytest.mark.parametrize(
    "altitude", ("SFC/FL030", "FL020/030", "6000FT/FL020", "300FT")
)
def test_is_altitude(altitude: str):
    """Tests if an element is an altitude"""
    assert core.is_altitude(altitude) is True


@pytest.mark.parametrize("value", ("", "50SE", "KFFT"))
def test_is_not_altitude(value: str):
    assert core.is_altitude(value) is False


@pytest.mark.parametrize(
    "text,force,value,unit,speak",
    (
        ("FL030", False, 30, "ft", "flight level three zero"),
        ("030", False, 30, "ft", "three zero"),
        ("030", True, 30, "ft", "flight level three zero"),
        ("6000FT", False, 6000, "ft", "six thousand"),
        ("10000FT", False, 10000, "ft", "one zero thousand"),
        ("2000M", False, 2000, "m", "two thousand"),
        ("ABV FL450", False, 450, "ft", "above flight level four five zero"),
    ),
)
def test_make_altitude(text: str, force: bool, value: int, unit: str, speak: str):
    """Tests converting altitude text into Number"""
    units = Units.international()
    altitude, units = core.make_altitude(text, units, force_fl=force)
    assert altitude.repr == text
    assert units.altitude == unit
    assert altitude.value == value
    assert altitude.spoken == speak


def test_parse_date():
    """Tests that report timestamp is parsed into a datetime object"""
    today = datetime.now(tz=timezone.utc)
    rts = today.strftime(r"%d%H%MZ")
    parsed = core.parse_date(rts)
    assert isinstance(parsed, datetime)
    assert parsed.day == today.day
    assert parsed.hour == today.hour
    assert parsed.minute == today.minute


@time_machine.travel("2020-06-22 12:00")
def test_midnight_rollover():
    """Tests that hour > 23 gets rolled into the next day"""
    parsed = core.parse_date("2224")
    assert isinstance(parsed, datetime)
    assert parsed.day == 23
    assert parsed.hour == 0
    assert parsed.minute == 0


@pytest.mark.parametrize(
    "dt,fmt,target",
    (
        (datetime.now(tz=timezone.utc), r"%d%HZ", False),
        (datetime.now(tz=timezone.utc), r"%d%H%MZ", False),
        (datetime(2010, 2, 2, 2, 2, tzinfo=timezone.utc), r"%d%HZ", True),
        (datetime(2010, 2, 2, 2, 2, tzinfo=timezone.utc), r"%d%H%MZ", True),
    ),
)
def test_make_timestamp(dt: datetime, fmt: str, target: bool):
    """Tests that a report timestamp is converted into a Timestamp dataclass"""
    dt_repr = dt.strftime(fmt)
    target = dt.date() if target else None
    dt = dt.replace(second=0, microsecond=0)
    if "%M" not in fmt:
        dt = dt.replace(minute=0)
    ts = core.make_timestamp(dt_repr, target_date=target)
    assert_timestamp(ts, dt_repr, dt)


@pytest.mark.parametrize(
    "temperature,dewpoint,humidity",
    (
        (10, 5, 0.7107),
        (27, 24, 0.83662),
        (15, 0, 0.35868),
        (10, 10, 1.0),
    ),
)
def test_relative_humidity(temperature: int, dewpoint: int, humidity: float):
    """Tests calculating relative humidity from temperatrue and dewpoint"""
    value = core.relative_humidity(temperature, dewpoint)
    assert round(value, 5) == humidity


@pytest.mark.parametrize(
    "pressure,altitude,pressure_altitude",
    (
        (29.92, 0, 0),
        (30.12, 6400, 6200),
        (30.28, 12000, 11640),
        (29.78, 1200, 1340),
        (30.09, 0, -170),
    ),
)
def test_pressure_altitude(pressure: float, altitude: int, pressure_altitude: int):
    """Tests calculating pressure altitude in feet"""
    value = core.pressure_altitude(pressure, altitude)
    assert value == pressure_altitude


@pytest.mark.parametrize(
    "pressure,temperature,altitude,density",
    (
        (29.92, 15, 0, 0),
        (30.12, 10, 6400, 7136),
        (30.28, -10, 12000, 11520),
        (29.78, 18, 1200, 1988),
        (30.09, 31, 0, 1750),
        (30.02, 0, 0, -1900),
    ),
)
def test_density_altitude(
    pressure: float, temperature: int, altitude: int, density: int
):
    """Tests calculating density altitude in feet"""
    units = Units.north_american()
    value = core.density_altitude(pressure, temperature, altitude, units)
    assert value == density
