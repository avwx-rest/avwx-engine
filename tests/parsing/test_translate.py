"""Test translation functions."""

# stdlib
from __future__ import annotations

# library
import pytest

# module
from avwx import structs
from avwx.current.base import get_wx_codes
from avwx.parsing import core, remarks, translate
from avwx.parsing.translate import base as trans_base
from avwx.units import Measurement


@pytest.mark.parametrize(
    ("magnitude", "unit", "vis_repr", "translation"),
    [
        (None, "m", None, ""),
        (0, "m", None, "0km (0sm)"),
        (2000, "m", None, "2km (1.2sm)"),
        (900, "m", None, "0.9km (0.6sm)"),
        (6, "sm", "P6", "Greater than 6sm ( >10km )"),
        (0.25, "sm", "M1/4", "Less than .25sm ( <0.4km )"),
        (0.75, "sm", None, "0.75sm (1.2km)"),
        (1.5, "sm", None, "1.5sm (2.4km)"),
        (3, "sm", None, "3sm (4.8km)"),
    ],
)
def test_visibility(magnitude: float | None, unit: str, vis_repr: str | None, translation: str) -> None:
    """Test visibility translation and conversion."""
    vis = Measurement(magnitude, unit) if magnitude is not None else None
    assert trans_base.visibility(vis, vis_repr) == translation


@pytest.mark.parametrize(
    ("magnitude", "unit", "translation"),
    [
        (None, "hPa", ""),
        (1020, "hPa", "1020 hPa (30.12 inHg)"),
        (999, "hPa", "999 hPa (29.50 inHg)"),
        (1012, "hPa", "1012 hPa (29.88 inHg)"),
        (30.00, "inHg", "30.00 inHg (1016 hPa)"),
        (29.92, "inHg", "29.92 inHg (1013 hPa)"),
        (30.05, "inHg", "30.05 inHg (1018 hPa)"),
    ],
)
def test_altimeter(magnitude: float | None, unit: str, translation: str) -> None:
    """Test altimeter translation and conversion."""
    alt = Measurement(magnitude, unit) if magnitude is not None else None
    assert trans_base.altimeter(alt) == translation


@pytest.mark.parametrize(
    ("clouds", "translation"),
    [
        (["BKN", "FEW020"], "Few clouds at 2000ft"),
        (
            ["OVC030", "SCT100"],
            "Overcast layer at 3000ft, Scattered clouds at 10000ft",
        ),
        (["BKN015CB"], "Broken layer at 1500ft (Cumulonimbus)"),
    ],
)
def test_clouds(clouds: list[str], translation: str) -> None:
    """Test translating each cloud into a single string."""
    cloud_objs = [core.make_cloud(cloud)[0] for cloud in clouds]
    assert trans_base.clouds(cloud_objs) == f"{translation} - Reported AGL"


def test_no_clouds() -> None:
    assert trans_base.clouds(None) == ""
    assert trans_base.clouds([]) == "Sky clear"


@pytest.mark.parametrize(
    ("codes", "translation"),
    [
        ([], ""),
        (["VCFC", "+RA"], "Vicinity Funnel Cloud, Heavy Rain"),
        (["-SN"], "Light Snow"),
    ],
)
def test_wx_codes(codes: list[str], translation: str) -> None:
    """Test translating a list of weather codes into a single string."""
    code_objs = get_wx_codes(codes)[1]
    assert trans_base.wx_codes(code_objs) == translation


def test_shared() -> None:
    """Test availability of shared values between the METAR and TAF translations."""
    data = structs.SharedData(
        altimeter=Measurement(29.92, "inHg"),
        clouds=[core.make_cloud("OVC060")[0]],
        flight_rules=structs.FlightRules.VFR,
        other=[],
        visibility=Measurement(10, "sm"),
        wind_direction=Measurement(0, "degree"),
        wind_gust=Measurement(0, "kt"),
        wind_speed=Measurement(0, "kt"),
        wx_codes=get_wx_codes(["RA"])[1],
    )
    repr_data = structs.SharedRepr(
        altimeter=None,
        clouds=["OVC060"],
        other=[],
        visibility=None,
        wind_direction=None,
        wind_gust=None,
        wind_speed=None,
        wx_codes=[],
    )
    trans = translate.base.current_shared(data, repr_data)
    assert isinstance(trans, structs.ReportTrans)
    for key in ("altimeter", "clouds", "visibility", "wx_codes"):
        assert bool(getattr(trans, key))


# Test METAR translations


def test_cardinal_direction() -> None:
    """Test that a direction int returns the correct cardinal direction string."""
    from avwx import static

    keys = (12, 34, 57, 79)
    for i, cardinal in enumerate(static.core.CARDINAL_DEGREES.keys()):
        lower = keys[i % 4] + 90 * (i // 4)
        upper = keys[0] + 90 * ((i // 4) + 1) - 1 if i % 4 == 3 else keys[(i % 4) + 1] + 90 * (i // 4) - 1
        for direction in range(lower, upper + 1):
            assert translate.base.get_cardinal_direction(direction) == cardinal
    # -10 - 11
    for direction in range(-10, 12):
        assert translate.base.get_cardinal_direction(direction) == "N"


@pytest.mark.parametrize(
    ("wind", "vardir", "direction_repr", "translation"),
    [
        (("", "", ""), None, None, ""),
        (
            ("360", "12", "20"),
            ["340", "020"],
            "360",
            "N-360 (variable 340 to 020) at 12kt gusting to 20kt",
        ),
        (("000", "00", ""), None, "000", "Calm"),
        (("VRB", "5", "12"), None, "VRB", "Variable at 5kt gusting to 12kt"),
        (("270", "10", ""), ["240", "300"], "270", "W-270 (variable 240 to 300) at 10kt"),
    ],
)
def test_wind(
    wind: tuple[str, str, str],
    vardir: list[str] | None,
    direction_repr: str | None,
    translation: str,
) -> None:
    """Test that wind values are translating into a single string."""
    dir_str, spd_str, gust_str = wind
    direction = Measurement(float(dir_str), "degree") if dir_str and dir_str not in ("VRB", "000") else None
    speed = Measurement(float(spd_str), "kt") if spd_str else None
    gust = Measurement(float(gust_str), "kt") if gust_str else None
    vardir_m = [Measurement(float(v), "degree") for v in vardir] if vardir else None
    assert translate.base.wind(direction, speed, gust, vardir_m, direction_repr) == translation


@pytest.mark.parametrize(
    ("magnitude", "unit", "translation"),
    [
        (None, "degF", ""),
        (20, "degF", "20°F (-7°C)"),
        (-20, "degF", "-20°F (-29°C)"),
        (20, "degC", "20°C (68°F)"),
        (-20, "degC", "-20°C (-4°F)"),
    ],
)
def test_temperature(magnitude: float | None, unit: str, translation: str) -> None:
    """Test temperature translation and conversion."""
    temp = Measurement(magnitude, unit) if magnitude is not None else None
    assert translate.base.temperature(temp) == translation


def test_metar() -> None:
    """Test end-to-end METAR translation."""
    metar_data = structs.MetarData(
        altimeter=Measurement(29.92, "inHg"),
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
    trans = structs.MetarTrans(
        altimeter="29.92 inHg (1013 hPa)",
        clouds="Broken layer at 1500ft (Cumulonimbus) - Reported AGL",
        dewpoint="-1°C (30°F)",
        remarks={},
        temperature="3°C (37°F)",
        visibility="3sm (4.8km)",
        wind="N-360 (variable 340 to 020) at 12kt gusting to 20kt",
        wx_codes="Heavy Rain",
    )
    translated = translate.metar.translate_metar(metar_data, metar_repr)
    assert isinstance(translated, structs.MetarTrans)
    assert translated == trans


# Test TAF translations


@pytest.mark.parametrize(
    ("shear", "translation"),
    [
        ("", ""),
        ("WS020/07040KT", "Wind shear 2000ft from 070 at 40kt"),
        ("WS100/20020KT", "Wind shear 10000ft from 200 at 20kt"),
    ],
)
def test_wind_shear(shear: str, translation: str) -> None:
    """Test wind shear unpacking and translation."""
    assert translate.taf.wind_shear(shear) == translation


@pytest.mark.parametrize(
    ("turb_ice", "translation"),
    [
        ([], ""),
        (
            ["540553"],
            "Occasional moderate turbulence in clouds from 5500ft to 8500ft",
        ),
        (["611005"], "Light icing from 10000ft to 15000ft"),
        (
            ["610023", "610062"],
            "Light icing from 200ft to 3200ft, Light icing from 600ft to 2600ft",
        ),
    ],
)
def test_turb_ice(turb_ice: list[str], translation: str) -> None:
    """Test turbulence and icing translations."""
    assert translate.taf.turb_ice(turb_ice) == translation


@pytest.mark.parametrize(
    ("temp", "translation"),
    [
        ("", ""),
        ("TX20/1518Z", "Maximum temperature of 20°C (68°F) at 15-18:00Z"),
        ("TXM02/04", "Maximum temperature of -2°C (28°F) at 04:00Z"),
        ("TN00/00", "Minimum temperature of 0°C (32°F) at 00:00Z"),
    ],
)
def test_min_max_temp(temp: str, translation: str) -> None:
    """Test temperature time translation and conversion."""
    assert translate.taf.min_max_temp(temp) == translation


def test_taf() -> None:
    """Test end-to-end TAF translation."""
    line_data = structs.TafLineData(
        altimeter=Measurement(29.92, "inHg"),
        clouds=[core.make_cloud("BKN015CB")[0]],
        end_time=None,
        flight_rules=structs.FlightRules.VFR,
        icing=["611005"],
        other=[],
        probability=None,
        raw="",
        sanitized="",
        start_time=None,
        transition_start=None,
        turbulence=["540553"],
        type="FROM",
        visibility=Measurement(3, "sm"),
        wind_direction=Measurement(360, "degree"),
        wind_gust=Measurement(20, "kt"),
        wind_shear="WS020/07040KT",
        wind_speed=Measurement(12, "kt"),
        wind_variable_direction=None,
        wx_codes=get_wx_codes(["+RA"])[1],
    )
    line_repr = structs.TafLineRepr(
        altimeter=None,
        clouds=["BKN015CB"],
        end_time=None,
        icing=["611005"],
        other=[],
        probability=None,
        raw="",
        sanitized="",
        start_time=None,
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
    taf_data = structs.TafData(
        end_time=None,
        forecast=[line_data],
        is_amended=False,
        is_correction=False,
        max_temp="TX20/1518Z",
        min_temp="TN00/00",
        raw="",
        remarks=None,
        sanitized="",
        start_time=None,
        station=None,
        time=None,
    )
    taf_repr = structs.TafRepr(
        forecast=[line_repr],
        raw="",
        remarks=None,
        sanitized="",
        station=None,
        time=None,
    )
    line_trans = structs.TafLineTrans(
        altimeter="29.92 inHg (1013 hPa)",
        clouds="Broken layer at 1500ft (Cumulonimbus) - Reported AGL",
        icing="Light icing from 10000ft to 15000ft",
        turbulence="Occasional moderate turbulence in clouds from 5500ft to 8500ft",
        visibility="3sm (4.8km)",
        wind_shear="Wind shear 2000ft from 070 at 40kt",
        wind="N-360 at 12kt gusting to 20kt",
        wx_codes="Heavy Rain",
    )
    trans = structs.TafTrans(
        forecast=[line_trans],
        max_temp="Maximum temperature of 20°C (68°F) at 15-18:00Z",
        min_temp="Minimum temperature of 0°C (32°F) at 00:00Z",
        remarks={},
    )
    translated = translate.taf.translate_taf(taf_data, taf_repr)
    assert isinstance(translated, structs.TafTrans)
    for line in translated.forecast:
        assert isinstance(line, structs.TafLineTrans)
    assert translated == trans


# Test remarks translations


@pytest.mark.parametrize(
    ("rmk", "out"),
    [
        (
            "RMK AO1 ACFT MSHP SLP137 T02720183 BINOVC",
            {
                "ACFT MSHP": "Aircraft mishap",
                "AO1": "Automated with no precipitation sensor",
                "BINOVC": "Breaks in Overcast",
                "sea_level_pressure": "Sea level pressure: 1013.7 hPa",
                "temperature_decimal": "Temperature 27.2°C and dewpoint 18.3°C",
            },
        ),
        (
            "RMK AO2 51014 21045 60720 70016",
            {
                "minimum_temperature_6h": "6-hour minimum temperature -4.5°C",
                "51014": "3-hour pressure difference: +/- 1.4 hPa - Increasing, then steady",
                "precip_36h": "Precipitation in the last 3/6 hours: 7.2 in",
                "precip_24h": "Precipitation in the last 24 hours: 0.16 in",
                "AO2": "Automated with precipitation sensor",
            },
        ),
        (
            "RMK 98123 TSB20 P0123 NOSPECI $",
            {
                "$": "ASOS requires maintenance",
                "sunshine_minutes": "Duration of sunlight: 123.0 minutes",
                "NOSPECI": "No SPECI reports taken",
                "precip_hourly": "Precipitation in the last hour: 1.23 in",
                "TSB20": "Thunderstorm began at :20",
            },
        ),
    ],
)
def test_translate(rmk: str, out: dict[str, str]) -> None:
    """Tests extracting translations from the remarks string"""
    data = remarks.parse(rmk)
    assert translate.remarks.translate(rmk, data) == out
