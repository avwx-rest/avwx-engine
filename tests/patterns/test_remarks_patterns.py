"""Tests for the remarks module in the patterns package"""

import pytest

import avwx.patterns.remarks as rp
from tests.patterns.utils import assert_match, assert_group_dict

param = pytest.mark.parametrize  # alias


@param("inp, should_match", [(" ACFT MSHP ", True), (" ANACFT_MSHP ", False)])
def test_aircraft_mishap(inp, should_match):
    """Aircraft Mishap"""
    assert_match(rp.AIRCRAFT_MISHAP_RE, inp, should_match)


@param(
    "inp, should_match",
    [(" AO1 ", True), (" AO2 ", True), (" AO3 ", False), (" AAO1 ", False),],
)
def test_automated_station(inp, should_match):
    """Automated Station"""
    assert_match(rp.AUTOMATED_STATION_RE, inp, should_match)


@param(
    "inp, direction, speed, hours, minutes",
    [
        (" PK WND 36050/0130 ", "360", "50", "01", "30"),
        (" PK_WND_36050/0130 ", "360", "50", "01", "30"),
        (" PK_WND_36050/30 ", "360", "50", None, "30"),
    ],
)
def test_peak_wind_groups(inp, direction, speed, hours, minutes):
    """Peak Wind"""
    exp_dict = {
        "direction": direction,
        "speed": speed,
        "hours": hours,
        "minutes": minutes,
    }
    assert_group_dict(rp.PEAK_WIND_RE, inp, exp_dict)


@param(
    "inp, hours, minutes", [(" WSHFT 0123 ", "01", "23"), (" WSHFT 23 ", None, "23"),]
)
def test_wind_shift(inp, hours, minutes):
    """Wind Shift"""
    exp_dict = {"hours": hours, "minutes": minutes}
    assert_group_dict(rp.WIND_SHIFT_RE, inp, exp_dict)


@param("inp, lower, upper", [(" CIG 012V345 ", "012", "345"), (" CIG 1V2 ", "1", "2")])
def test_variable_ceiling_height(inp, lower, upper):
    """Variable Ceiling Height"""
    exp_dict = {"lower": lower, "upper": upper}
    assert_group_dict(rp.VARIABLE_CEILING_HEIGHT_RE, inp, exp_dict)


@param("inp, direction", [(" PRESFR ", "F"), (" PRESRR ", "R")])
def test_pressure_change(inp, direction):
    """Pressure Change"""
    exp_dict = {"direction": direction}

    assert_group_dict(rp.PRESSURE_CHANGE_RE, inp, exp_dict)


@param(
    "inp, location, visibility",
    [
        (" TWR VIS 1 ", "TWR", "1"),
        (" TWR VIS 1/2 ", "TWR", "1/2"),
        (" SFC VIS 1/4 ", "SFC", "1/4"),
    ],
)
def test_tower_or_surface_visibility(inp, location, visibility):
    """Tower or Surface Visibility"""
    match = rp.TOWER_OR_SURFACE_VISIBILITY_RE.search(inp)

    assert match.groupdict() == {"location": location, "visibility": visibility}


@param(
    "inp, vis, loc",
    [("VIS 3/4 RWY11", "3/4", "RWY11"), ("VIS 1 1/2 RWY01", "1 1/2", "RWY01")],
)
def test_secondary_location_visibility(inp, vis, loc):
    """Visibility at Second Location"""
    expected_dict = {"visibility": vis, "location": loc}

    assert_group_dict(rp.VISIBILITY_AT_SECOND_LOCATION_RE, inp, expected_dict)


@param(
    "inp, lower, upper",
    [(" VIS 3/4V1 1/2 ", "3/4", "1 1/2"), (" VIS 1 1/2V2 3/4 ", "1 1/2", "2 3/4")],
)
def test_variable_prevailing_visibility(inp, lower, upper):
    """Variable Prevailing Visibility"""
    match = rp.VARIABLE_PREVAILING_VISIBILITY_RE.search(inp)

    assert match.groupdict() == {"lower": lower, "upper": upper}


@param("inp, pressure", [("SLP123", "123"), ("SLP12", "12"),])
def test_sea_level_pressure(inp, pressure):
    """Sea Level Pressure"""
    match = rp.SEA_LEVEL_PRESSURE_RE.search(inp)

    assert match.groupdict() == {"pressure": pressure}


@param(
    "inp, activity, began_ended, minutes, loc, move",
    [
        ("TORNADO", "TORNADO", None, None, None, None),
        ("WATERSPOUT B25 NNE MOV W", "WATERSPOUT", "B", "25", "NNE", "W"),
    ],
)
def test_tornado_activity(inp, activity, began_ended, minutes, loc, move):
    """Tornado Activity"""

    assert_group_dict(
        rp.TORNADO_ACTIVITY_RE,
        inp,
        {
            "activity": activity,
            "began_ended": began_ended,
            "minutes": minutes,
            "location": loc,
            "movement": move,
        },
    )


@param(
    "inp, freq, loc",
    [("FRQ LTG NE", "FRQ", "NE"), ("LTG", None, None), ("LTG SSW", None, "SSW")],
)
def test_lightning(inp, freq, loc):
    """Lightning"""
    expected = {"frequent": freq, "direction": loc}

    assert_group_dict(rp.LIGHTNING_RE, inp, expected)


_input_params = (
    "inp, precip, first, first_type, first_time, second, second_type, second_time"
)


@param(
    _input_params,
    [
        ("RAB0123E1234", "RA", "B0123", "B", "0123", "E1234", "E", "1234"),
        ("RAB12", "RA", "B12", "B", "12", None, None, None),
        ("  TSE1234  ", "TS", "E1234", "E", "1234", None, None, None),
        ("TSB12E0112", "TS", "B12", "B", "12", "E0112", "E", "0112"),
    ],
)
def test_beginning_ending_of_precip_and_ts(
    inp, precip, first, first_type, first_time, second, second_type, second_time,
):
    """Beginning and Ending of Precipitation/Thunderstorm"""
    expected = {
        "precip": precip,
        "first": first,
        "first_type": first_type,
        "first_time": first_time,
        "second": second,
        "second_type": second_type,
        "second_time": second_time,
    }

    assert_group_dict(rp.BEGINNING_ENDING_OF_PRECIP_AND_TS, inp, expected)


@param("inp, height, location", [("CIG 017 RWY11", "017", "RWY11")])
def test_ceiling_at_second_location(inp, height, location):
    """Ceiling at Second Location"""
    expected = {"height": height, "location": location}

    assert_group_dict(rp.CEILING_HEIGHT_AT_SECOND_LOCATION_RE, inp, expected)
