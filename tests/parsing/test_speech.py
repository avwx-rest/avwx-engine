"""
Tests speech parsing
"""

# pylint: disable=redefined-builtin

# stdlib
from typing import List, Optional, Tuple

# library
import pytest

# module
from avwx import static, structs
from avwx.current.base import get_wx_codes
from avwx.current.metar import parse_altimeter
from avwx.parsing import core, speech


@pytest.mark.parametrize(
    "wind,vardir,spoken",
    (
        (("", "", ""), None, "unknown"),
        (
            ("360", "12", "20"),
            ["340", "020"],
            "three six zero (variable three four zero to zero two zero) at 12 knots gusting to 20 knots",
        ),
        (("000", "00", ""), None, "Calm"),
        (("VRB", "1", "12"), None, "Variable at 1 knot gusting to 12 knots"),
        (
            ("270", "10", ""),
            ["240", "300"],
            "two seven zero (variable two four zero to three zero zero) at 10 knots",
        ),
    ),
)
def test_wind(wind: Tuple[str, str, str], vardir: Optional[List[str]], spoken: str):
    """Tests converting wind data into a spoken string"""
    wind = [core.make_number(v, literal=(not i)) for i, v in enumerate(wind)]
    if vardir:
        vardir = [core.make_number(i, speak=i, literal=True) for i in vardir]
    assert speech.wind(*wind, vardir) == f"Winds {spoken}"


@pytest.mark.parametrize(
    "temp,unit,spoken",
    (
        ("", "F", "unknown"),
        ("20", "F", "two zero degrees Fahrenheit"),
        ("M20", "F", "minus two zero degrees Fahrenheit"),
        ("20", "C", "two zero degrees Celsius"),
        ("1", "C", "one degree Celsius"),
    ),
)
def test_temperature(temp: str, unit: str, spoken: str):
    """Tests converting a temperature into a spoken string"""
    assert speech.temperature("Temp", core.make_number(temp), unit) == f"Temp {spoken}"


@pytest.mark.parametrize(
    "vis,unit,spoken",
    (
        ("", "m", "unknown"),
        ("0000", "m", "zero kilometers"),
        ("2000", "m", "two kilometers"),
        ("0900", "m", "point nine kilometers"),
        ("P6", "sm", "greater than six miles"),
        ("M1/4", "sm", "less than one quarter of a mile"),
        ("3/4", "sm", "three quarters of a mile"),
        ("3/2", "sm", "one and one half miles"),
        ("3", "sm", "three miles"),
    ),
)
def test_visibility(vis: str, unit: str, spoken: str):
    """Tests converting visibility distance into a spoken string"""
    assert (
        speech.visibility(core.make_number(vis, m_minus=False), unit)
        == f"Visibility {spoken}"
    )


@pytest.mark.parametrize(
    "alt,unit,spoken",
    (
        ("", "hPa", "unknown"),
        ("1020", "hPa", "one zero two zero"),
        ("0999", "hPa", "zero nine nine nine"),
        ("1012", "hPa", "one zero one two"),
        ("3000", "inHg", "three zero point zero zero"),
        ("2992", "inHg", "two nine point nine two"),
        ("3005", "inHg", "three zero point zero five"),
    ),
)
def test_altimeter(alt: str, unit: str, spoken: str):
    """Tests converting altimeter reading into a spoken string"""
    assert speech.altimeter(parse_altimeter(alt), unit) == f"Altimeter {spoken}"


@pytest.mark.parametrize(
    "codes,spoken",
    (
        ([], ""),
        (
            ["+RATS", "VCFC"],
            "Heavy Rain Thunderstorm. Funnel Cloud in the Vicinity",
        ),
        (
            ["-GR", "FZFG", "BCBLSN"],
            "Light Hail. Freezing Fog. Patchy Blowing Snow",
        ),
    ),
)
def test_wx_codes(codes: List[str], spoken: str):
    """Tests converting WX codes into a spoken string"""
    codes = get_wx_codes(codes)[1]
    assert speech.wx_codes(codes) == spoken


def test_metar():  # sourcery skip: dict-assign-update-to-union
    """Tests converting METAR data into into a single spoken string"""
    units = structs.Units.north_american()
    empty_fields = (
        "raw",
        "remarks",
        "station",
        "time",
        "flight_rules",
        "remarks_info",
        "runway_visibility",
        "sanitized",
    )
    data = {
        "altimeter": parse_altimeter("2992"),
        "clouds": [core.make_cloud("BKN015CB")],
        "dewpoint": core.make_number("M01"),
        "other": [],
        "relative_humidity": None,
        "temperature": core.make_number("03"),
        "visibility": core.make_number("3"),
        "wind_direction": core.make_number("360"),
        "wind_gust": core.make_number("20"),
        "wind_speed": core.make_number("12"),
        "wind_variable_direction": [
            core.make_number("340"),
            core.make_number("020", speak="020"),
        ],
        "wx_codes": get_wx_codes(["+RA"])[1],
    }
    data.update({k: None for k in empty_fields})
    data = structs.MetarData(**data)
    spoken = (
        "Winds three six zero (variable three four zero to zero two zero) "
        "at 12 knots gusting to 20 knots. Visibility three miles. "
        "Temperature three degrees Celsius. Dew point minus one degree Celsius. "
        "Altimeter two nine point nine two. Heavy Rain. "
        "Broken layer at 1500ft (Cumulonimbus)"
    )
    ret = speech.metar(data, units)
    assert isinstance(ret, str)
    assert ret == spoken


@pytest.mark.parametrize(
    "type,start,end,prob,spoken",
    (
        (None, None, None, None, ""),
        ("FROM", "2808", "2815", None, "From 8 to 15 zulu,"),
        ("FROM", "2822", "2903", None, "From 22 to 3 zulu,"),
        ("BECMG", "3010", None, None, "At 10 zulu becoming"),
        (
            "PROB",
            "1303",
            "1305",
            "30",
            r"From 3 to 5 zulu, there's a 30% chance for",
        ),
        (
            "INTER",
            "1303",
            "1305",
            "45",
            r"From 3 to 5 zulu, there's a 45% chance for intermittent",
        ),
        ("INTER", "2423", "2500", None, "From 23 to midnight zulu, intermittent"),
        ("TEMPO", "0102", "0103", None, "From 2 to 3 zulu, temporary"),
    ),
)
def test_type_and_times(
    type: Optional[str],
    start: Optional[str],
    end: Optional[str],
    prob: Optional[str],
    spoken: str,
):
    """Tests line start from type, time, and probability values"""
    start_ts, end_ts = core.make_timestamp(start), core.make_timestamp(end)
    if prob is not None:
        prob = core.make_number(prob)
    ret = speech.type_and_times(type, start_ts, end_ts, prob)
    assert isinstance(ret, str)
    assert ret == spoken


@pytest.mark.parametrize(
    "shear,spoken",
    (
        ("", "Wind shear unknown"),
        ("WS020/07040KT", "Wind shear 2000ft from zero seven zero at 40 knots"),
        ("WS100/20020KT", "Wind shear 10000ft from two zero zero at 20 knots"),
    ),
)
def test_wind_shear(shear: str, spoken: str):
    """Tests converting wind shear code into a spoken string"""
    assert speech.wind_shear(shear) == spoken


def test_taf_line():  # sourcery skip: dict-assign-update-to-union
    """Tests converting TAF line data into into a single spoken string"""
    units = structs.Units.north_american()
    empty_fields = ("flight_rules", "probability", "raw", "sanitized")
    line = {
        "altimeter": parse_altimeter("2992"),
        "clouds": [core.make_cloud("BKN015CB")],
        "end_time": core.make_timestamp("1206"),
        "icing": ["611005"],
        "other": [],
        "start_time": core.make_timestamp("1202"),
        "transition_start": None,
        "turbulence": ["540553"],
        "type": "FROM",
        "visibility": core.make_number("3"),
        "wind_direction": core.make_number("360"),
        "wind_gust": core.make_number("20"),
        "wind_shear": "WS020/07040KT",
        "wind_speed": core.make_number("12"),
        "wx_codes": get_wx_codes(["+RA"])[1],
        "wind_variable_direction": [core.make_number("320"), core.make_number("370")],
    }
    line.update({k: None for k in empty_fields})
    line = structs.TafLineData(**line)
    spoken = (
        "From 2 to 6 zulu, Winds three six zero (variable three two zero to three seven zero) at 12 knots gusting to 20 knots. "
        "Wind shear 2000ft from zero seven zero at 40 knots. Visibility three miles. "
        "Altimeter two nine point nine two. Heavy Rain. "
        "Broken layer at 1500ft (Cumulonimbus). "
        "Occasional moderate turbulence in clouds from 5500ft to 8500ft. "
        "Light icing from 10000ft to 15000ft"
    )
    ret = speech.taf_line(line, units)
    assert isinstance(ret, str)
    assert ret == spoken


def test_taf():
    """Tests converting a TafData report into a single spoken string"""
    units = structs.Units.north_american()
    # pylint: disable=no-member
    empty_line = {k: None for k in structs.TafLineData.__dataclass_fields__.keys()}
    forecast = [
        structs.TafLineData(**{**empty_line, **line})
        for line in (
            {
                "type": "FROM",
                "start_time": core.make_timestamp("0410Z"),
                "end_time": core.make_timestamp("0414Z"),
                "visibility": core.make_number("3"),
                "wind_direction": core.make_number("360"),
                "wind_gust": core.make_number("20"),
                "wind_speed": core.make_number("12"),
            },
            {
                "type": "PROB",
                "probability": core.make_number("45"),
                "start_time": core.make_timestamp("0412Z"),
                "end_time": core.make_timestamp("0414Z"),
                "visibility": core.make_number("M1/4", m_minus=False),
            },
        )
    ]
    taf = structs.TafData(
        raw=None,
        sanitized=None,
        remarks=None,
        station=None,
        time=None,
        forecast=forecast,
        start_time=core.make_timestamp("0410Z"),
        end_time=core.make_timestamp("0414Z"),
    )
    ret = speech.taf(taf, units)
    spoken = (
        f"Starting on {taf.start_time.dt.strftime('%B')} 4th - From 10 to 14 zulu, "
        "Winds three six zero at 12 knots gusting to 20 knots. Visibility three miles. "
        r"From 12 to 14 zulu, there's a 45% chance for Visibility "
        "less than one quarter of a mile"
    )
    assert isinstance(ret, str)
    assert ret == spoken
