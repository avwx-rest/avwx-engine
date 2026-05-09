"""Tests speech parsing."""

# stdlib
from __future__ import annotations

# library
import pytest

# module
from avwx import structs
from avwx.current.base import get_wx_codes
from avwx.current.metar import parse_altimeter
from avwx.parsing import core, speech
from avwx.units import Measurement


@pytest.mark.parametrize(
    ("wind", "vardir", "direction_repr", "spoken"),
    [
        (("", "", ""), None, None, "unknown"),
        (
            ("360", "12", "20"),
            ["340", "020"],
            "360",
            "three six zero (variable three four zero to zero two zero) at 12 knots gusting to 20 knots",
        ),
        (("000", "00", ""), None, "000", "Calm"),
        (("VRB", "1", "12"), None, "VRB", "Variable at 1 knot gusting to 12 knots"),
        (
            ("270", "10", ""),
            ["240", "300"],
            "270",
            "two seven zero (variable two four zero to three zero zero) at 10 knots",
        ),
    ],
)
def test_wind(
    wind: tuple[str, str, str],
    vardir: list[str] | None,
    direction_repr: str | None,
    spoken: str,
) -> None:
    """Test converting wind data into a spoken string."""
    dir_str, spd_str, gust_str = wind
    direction = Measurement(float(dir_str), "degree") if dir_str and dir_str not in ("VRB", "000") else None
    spd = Measurement(float(spd_str), "kt") if spd_str else None
    gust = Measurement(float(gust_str), "kt") if gust_str else None
    vardir_m = [Measurement(float(v), "degree") for v in vardir] if vardir else None
    assert speech.wind(direction, spd, gust, vardir_m, direction_repr) == f"Winds {spoken}"


@pytest.mark.parametrize(
    ("magnitude", "unit", "spoken"),
    [
        (None, "degF", "unknown"),
        (20, "degF", "two zero degrees Fahrenheit"),
        (-20, "degF", "minus two zero degrees Fahrenheit"),
        (20, "degC", "two zero degrees Celsius"),
        (1, "degC", "one degree Celsius"),
    ],
)
def test_temperature(magnitude: float | None, unit: str, spoken: str) -> None:
    """Test converting a temperature into a spoken string."""
    temp = Measurement(magnitude, unit) if magnitude is not None else None
    assert speech.temperature("Temp", temp) == f"Temp {spoken}"


@pytest.mark.parametrize(
    ("magnitude", "unit", "vis_repr", "spoken"),
    [
        (None, "m", None, "unknown"),
        (0, "m", None, "zero kilometers"),
        (2000, "m", None, "two kilometers"),
        (900, "m", None, "point nine kilometers"),
        (6, "sm", "P6", "greater than six miles"),
        (0.25, "sm", "M1/4", "less than one quarter of a mile"),
        (0.75, "sm", "3/4", "three quarters of a mile"),
        (1.5, "sm", "3/2", "one and one half miles"),
        (3, "sm", None, "three miles"),
    ],
)
def test_visibility(magnitude: float | None, unit: str, vis_repr: str | None, spoken: str) -> None:
    """Test converting visibility distance into a spoken string."""
    vis = Measurement(magnitude, unit) if magnitude is not None else None
    assert speech.visibility(vis, vis_repr) == f"Visibility {spoken}"


@pytest.mark.parametrize(
    ("alt_str", "spoken"),
    [
        (None, "unknown"),
        ("1020", "one zero two zero"),
        ("0999", "zero nine nine nine"),
        ("1012", "one zero one two"),
        ("3000", "three zero point zero zero"),
        ("2992", "two nine point nine two"),
        ("3005", "three zero point zero five"),
    ],
)
def test_altimeter(alt_str: str | None, spoken: str) -> None:
    """Test converting altimeter reading into a spoken string."""
    alt = parse_altimeter(alt_str) if alt_str else None
    assert speech.altimeter(alt) == f"Altimeter {spoken}"


@pytest.mark.parametrize(
    ("codes", "spoken"),
    [
        ([], ""),
        (
            ["+RATS", "VCFC"],
            "Heavy Rain Thunderstorm. Funnel Cloud in the Vicinity",
        ),
        (
            ["-GR", "FZFG", "BCBLSN"],
            "Light Hail. Freezing Fog. Patchy Blowing Snow",
        ),
    ],
)
def test_wx_codes(codes: list[str], spoken: str) -> None:
    """Test converting WX codes into a spoken string."""
    wx_codes = get_wx_codes(codes)[1]
    assert speech.wx_codes(wx_codes) == spoken


def test_metar() -> None:
    """Test converting METAR data into into a single spoken string."""
    metar_data = structs.MetarData(
        altimeter=parse_altimeter("2992"),
        clouds=[core.make_cloud("BKN015CB")[0]],
        dewpoint=Measurement(-1, "degC"),
        flight_rules=structs.FlightRules.VFR,
        other=[],
        relative_humidity=None,
        remarks=None,
        remarks_info=None,
        runway_visibility=[],
        sanitized="",
        station=None,
        temperature=Measurement(3, "degC"),
        time=None,
        visibility=Measurement(3, "sm"),
        wind_direction=Measurement(360, "degree"),
        wind_gust=Measurement(20, "kt"),
        wind_speed=Measurement(12, "kt"),
        wind_variable_direction=[Measurement(340, "degree"), Measurement(20, "degree")],
        wx_codes=get_wx_codes(["+RA"])[1],
    )
    metar_repr = structs.MetarRepr(
        altimeter=None,
        clouds=["BKN015CB"],
        dewpoint=None,
        other=[],
        raw="",
        remarks=None,
        runway_visibility=[],
        sanitized="",
        station=None,
        temperature=None,
        time=None,
        visibility=None,
        wind_direction="360",
        wind_gust=None,
        wind_speed=None,
        wind_variable_direction=[],
        wx_codes=[],
    )
    spoken = (
        "Winds three six zero (variable three four zero to zero two zero) "
        "at 12 knots gusting to 20 knots. Visibility three miles. "
        "Broken layer at 1500ft (Cumulonimbus). Heavy Rain. "
        "Temperature three degrees Celsius. Dew point minus one degree Celsius. "
        "Altimeter two nine point nine two"
    )
    ret = speech.metar(metar_data, metar_repr)
    assert isinstance(ret, str)
    assert ret == spoken


@pytest.mark.parametrize(
    ("type", "start", "end", "prob", "spoken"),
    [
        (None, None, None, None, ""),
        ("FROM", "2808", "2815", None, "From 8 to 15 zulu,"),
        ("FROM", "2822", "2903", None, "From 22 to 3 zulu,"),
        ("BECMG", "3010", None, None, "At 10 zulu becoming"),
        (
            "PROB",
            "1303",
            "1305",
            30.0,
            r"From 3 to 5 zulu, there's a 30% chance for",
        ),
        (
            "INTER",
            "1303",
            "1305",
            45.0,
            r"From 3 to 5 zulu, there's a 45% chance for intermittent",
        ),
        ("INTER", "2423", "2500", None, "From 23 to midnight zulu, intermittent"),
        ("TEMPO", "0102", "0103", None, "From 2 to 3 zulu, temporary"),
    ],
)
def test_type_and_times(
    type: str | None,  # noqa: A002
    start: str | None,
    end: str | None,
    prob: float | None,
    spoken: str,
) -> None:
    """Test line start from type, time, and probability values."""
    start_ts, end_ts = core.make_timestamp(start), core.make_timestamp(end)
    ret = speech.type_and_times(type, start_ts, end_ts, prob)
    assert isinstance(ret, str)
    assert ret == spoken


@pytest.mark.parametrize(
    ("shear", "spoken"),
    [
        ("", "Wind shear unknown"),
        ("WS020/07040KT", "Wind shear 2000ft from zero seven zero at 40 knots"),
        ("WS100/20020KT", "Wind shear 10000ft from two zero zero at 20 knots"),
    ],
)
def test_wind_shear(shear: str, spoken: str) -> None:
    """Test converting wind shear code into a spoken string."""
    assert speech.wind_shear(shear) == spoken


def test_taf_line() -> None:
    """Test converting TAF line data into into a single spoken string."""
    line_data = structs.TafLineData(
        altimeter=parse_altimeter("2992"),
        clouds=[core.make_cloud("BKN015CB")[0]],
        end_time=core.make_timestamp("1206"),
        flight_rules=structs.FlightRules.VFR,
        icing=["611005"],
        other=[],
        probability=None,
        raw="",
        sanitized="",
        start_time=core.make_timestamp("1202"),
        transition_start=None,
        turbulence=["540553"],
        type="FROM",
        visibility=Measurement(3, "sm"),
        wind_direction=Measurement(360, "degree"),
        wind_gust=Measurement(20, "kt"),
        wind_shear="WS020/07040KT",
        wind_speed=Measurement(12, "kt"),
        wind_variable_direction=[Measurement(320, "degree"), Measurement(370, "degree")],
        wx_codes=get_wx_codes(["+RA"])[1],
    )
    line_repr = structs.TafLineRepr(
        altimeter=None,
        clouds=["BKN015CB"],
        end_time="1206",
        icing=["611005"],
        other=[],
        probability=None,
        raw="",
        sanitized="",
        start_time="1202",
        turbulence=["540553"],
        type="FROM",
        visibility=None,
        wind_direction="360",
        wind_gust=None,
        wind_shear="WS020/07040KT",
        wind_speed=None,
        wind_variable_direction=None,
        wx_codes=[],
    )
    spoken = (
        "From 2 to 6 zulu, Winds three six zero (variable three two zero to three seven zero) at 12 knots gusting to 20 knots. "
        "Wind shear 2000ft from zero seven zero at 40 knots. Visibility three miles. "
        "Altimeter two nine point nine two. Heavy Rain. "
        "Broken layer at 1500ft (Cumulonimbus). "
        "Occasional moderate turbulence in clouds from 5500ft to 8500ft. "
        "Light icing from 10000ft to 15000ft"
    )
    ret = speech.taf_line(line_data, line_repr)
    assert isinstance(ret, str)
    assert ret == spoken


def test_taf() -> None:
    """Test converting a TafData report into a single spoken string."""
    line1 = structs.TafLineData(
        altimeter=None,
        clouds=[],
        end_time=core.make_timestamp("0414Z"),
        flight_rules=structs.FlightRules.VFR,
        icing=[],
        other=[],
        probability=None,
        raw="",
        sanitized="",
        start_time=core.make_timestamp("0410Z"),
        transition_start=None,
        turbulence=[],
        type="FROM",
        visibility=Measurement(3, "sm"),
        wind_direction=Measurement(360, "degree"),
        wind_gust=Measurement(20, "kt"),
        wind_shear=None,
        wind_speed=Measurement(12, "kt"),
        wind_variable_direction=None,
        wx_codes=[],
    )
    line1_repr = structs.TafLineRepr(
        altimeter=None,
        clouds=[],
        end_time="0414Z",
        icing=[],
        other=[],
        probability=None,
        raw="",
        sanitized="",
        start_time="0410Z",
        turbulence=[],
        type="FROM",
        visibility=None,
        wind_direction="360",
        wind_gust=None,
        wind_shear=None,
        wind_speed=None,
        wind_variable_direction=None,
        wx_codes=[],
    )
    line2 = structs.TafLineData(
        altimeter=None,
        clouds=[],
        end_time=core.make_timestamp("0414Z"),
        flight_rules=structs.FlightRules.VFR,
        icing=[],
        other=[],
        probability=45.0,
        raw="",
        sanitized="",
        start_time=core.make_timestamp("0412Z"),
        transition_start=None,
        turbulence=[],
        type="PROB",
        visibility=Measurement(0.25, "sm"),
        wind_direction=None,
        wind_gust=None,
        wind_shear=None,
        wind_speed=None,
        wind_variable_direction=None,
        wx_codes=[],
    )
    line2_repr = structs.TafLineRepr(
        altimeter=None,
        clouds=[],
        end_time="0414Z",
        icing=[],
        other=[],
        probability="PROB45",
        raw="",
        sanitized="",
        start_time="0412Z",
        turbulence=[],
        type="PROB",
        visibility="M1/4",
        wind_direction=None,
        wind_gust=None,
        wind_shear=None,
        wind_speed=None,
        wind_variable_direction=None,
        wx_codes=[],
    )
    taf_data = structs.TafData(
        raw="",
        sanitized="",
        remarks=None,
        station=None,
        time=None,
        forecast=[line1, line2],
        start_time=core.make_timestamp("0410Z"),
        end_time=core.make_timestamp("0414Z"),
        is_amended=False,
        is_correction=False,
    )
    taf_repr = structs.TafRepr(
        raw="",
        sanitized="",
        remarks=None,
        station=None,
        time=None,
        forecast=[line1_repr, line2_repr],
    )
    ret = speech.taf(taf_data, taf_repr)
    assert taf_data.start_time is not None
    assert taf_data.start_time.dt is not None
    spoken = (
        f"Starting on {taf_data.start_time.dt.strftime('%B')} 4th - From 10 to 14 zulu, "
        "Winds three six zero at 12 knots gusting to 20 knots. Visibility three miles. "
        r"From 12 to 14 zulu, there's a 45% chance for Visibility "
        "less than one quarter of a mile"
    )
    assert isinstance(ret, str)
    assert ret == spoken
