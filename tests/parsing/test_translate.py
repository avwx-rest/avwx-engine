"""Test translation functions."""

# stdlib
from __future__ import annotations

# library
import pytest

# module
from avwx import static, structs
from avwx.current.base import get_wx_codes
from avwx.parsing import core, remarks, translate


@pytest.mark.parametrize(
    ("vis", "unit", "translation"),
    [
        ("", "m", ""),
        ("0000", "m", "0km (0sm)"),
        ("2000", "m", "2km (1.2sm)"),
        ("0900", "m", "0.9km (0.6sm)"),
        ("P6", "sm", "Greater than 6sm ( >10km )"),
        ("M1/4", "sm", "Less than .25sm ( <0.4km )"),
        ("3/4", "sm", "0.75sm (1.2km)"),
        ("3/2", "sm", "1.5sm (2.4km)"),
        ("3", "sm", "3sm (4.8km)"),
    ],
)
def test_visibility(vis: str, unit: str, translation: str) -> None:
    """Test visibility translation and conversion."""
    assert translate.base.visibility(core.make_number(vis, m_minus=False), unit) == translation


@pytest.mark.parametrize(
    ("alt", "repr", "unit", "translation"),
    [
        ("", "", "hPa", ""),
        ("1020", "1020", "hPa", "1020 hPa (30.12 inHg)"),
        ("0999", "0999", "hPa", "999 hPa (29.50 inHg)"),
        ("1012", "1012", "hPa", "1012 hPa (29.88 inHg)"),
        ("30.00", "3000", "inHg", "30.00 inHg (1016 hPa)"),
        ("29.92", "2992", "inHg", "29.92 inHg (1013 hPa)"),
        ("30.05", "3005", "inHg", "30.05 inHg (1018 hPa)"),
    ],
)
def test_altimeter(alt: str, repr: str, unit: str, translation: str) -> None:  # noqa: A002
    """Test altimeter translation and conversion."""
    assert translate.base.altimeter(core.make_number(alt, repr), unit) == translation


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
    cloud_objs = [core.make_cloud(cloud) for cloud in clouds]
    assert translate.base.clouds(cloud_objs) == f"{translation} - Reported AGL"


def test_no_clouds() -> None:
    assert translate.base.clouds(None) == ""
    assert translate.base.clouds([]) == "Sky clear"


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
    assert translate.base.wx_codes(code_objs) == translation


def test_shared() -> None:
    """Test availability of shared values between the METAR and TAF translations."""
    units = structs.Units.north_american()
    data = structs.SharedData(
        altimeter=core.make_number("29.92"),
        clouds=[core.make_cloud("OVC060")],
        flight_rules="",
        other=[],
        visibility=core.make_number("10"),
        wind_direction=core.make_number("0"),
        wind_gust=core.make_number("0"),
        wind_speed=core.make_number("0"),
        wx_codes=get_wx_codes(["RA"])[1],
    )
    trans = translate.base.current_shared(data, units)
    assert isinstance(trans, structs.ReportTrans)
    for key in ("altimeter", "clouds", "visibility", "wx_codes"):
        assert bool(getattr(trans, key))


# Test METAR translations


def test_cardinal_direction() -> None:
    """Test that a direction int returns the correct cardinal direction string."""
    # 12 - 360+
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
    ("wind", "vardir", "translation"),
    [
        (("", "", ""), None, ""),
        (
            ("360", "12", "20"),
            ["340", "020"],
            "N-360 (variable 340 to 020) at 12kt gusting to 20kt",
        ),
        (("000", "00", ""), None, "Calm"),
        (("VRB", "5", "12"), None, "Variable at 5kt gusting to 12kt"),
        (("270", "10", ""), ["240", "300"], "W-270 (variable 240 to 300) at 10kt"),
    ],
)
def test_wind(wind: tuple[str, str, str], vardir: list[str] | None, translation: str) -> None:
    """Test that wind values are translating into a single string."""
    wind_nums = [core.make_number(i) for i in wind]
    vardir_nums = [core.make_number(i) for i in vardir] if vardir else None
    assert translate.base.wind(*wind_nums, vardir_nums) == translation  # type: ignore


@pytest.mark.parametrize(
    ("temp", "unit", "translation"),
    [
        ("20", "F", "20°F (-7°C)"),
        ("M20", "F", "-20°F (-29°C)"),
        ("20", "C", "20°C (68°F)"),
        ("M20", "C", "-20°C (-4°F)"),
        ("", "F", ""),
    ],
)
def test_temperature(temp: str, unit: str, translation: str) -> None:
    """Test temperature translation and conversion."""
    assert translate.base.temperature(core.make_number(temp), unit) == translation


def test_metar() -> None:
    """Test end-to-end METAR translation."""
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
        "altimeter": core.make_number("29.92", "2992"),
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
            core.make_number("020"),
        ],
        "wx_codes": get_wx_codes(["+RA"])[1],
    } | {k: "" for k in empty_fields}
    metar_data = structs.MetarData(**data)  # type: ignore
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
    translated = translate.metar.translate_metar(metar_data, units)
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
    units = structs.Units.north_american()
    empty_line_fields = (
        "raw",
        "end_time",
        "start_time",
        "transition_start",
        "probability",
        "type",
        "flight_rules",
        "sanitized",
        "wind_variable_direction",
    )
    empty_fields = (
        "raw",
        "remarks",
        "sanitized",
        "station",
        "time",
        "start_time",
        "end_time",
    )
    line_data = {
        "altimeter": core.make_number("29.92", "2992"),
        "clouds": [core.make_cloud("BKN015CB")],
        "icing": ["611005"],
        "other": [],
        "turbulence": ["540553"],
        "visibility": core.make_number("3"),
        "wind_direction": core.make_number("360"),
        "wind_gust": core.make_number("20"),
        "wind_shear": "WS020/07040KT",
        "wind_speed": core.make_number("12"),
        "wx_codes": get_wx_codes(["+RA"])[1],
    }
    data = {"max_temp": "TX20/1518Z", "min_temp": "TN00/00"}
    for key in empty_line_fields:
        line_data[key] = ""
    for key in empty_fields:
        data[key] = ""
    taf_data = structs.TafData(forecast=[structs.TafLineData(**line_data)], **data)  # type: ignore
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
    translated = translate.taf.translate_taf(taf_data, units)
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
                "SLP137": "Sea level pressure: 1013.7 hPa",
                "T02720183": "Temperature 27.2°C and dewpoint 18.3°C",
            },
        ),
        (
            "RMK AO2 51014 21045 60720 70016",
            {
                "21045": "6-hour minimum temperature -4.5°C",
                "51014": "3-hour pressure difference: +/- 1.4 mb - Increasing, then steady",
                "60720": "Precipitation in the last 3/6 hours: 7.2 in",
                "70016": "Precipitation in the last 24 hours: 0.16 in",
                "AO2": "Automated with precipitation sensor",
            },
        ),
        (
            "RMK 98123 TSB20 P0123 NOSPECI $",
            {
                "$": "ASOS requires maintenance",
                "98123": "Duration of sunlight: 123 minutes",
                "NOSPECI": "No SPECI reports taken",
                "P0123": "Precipitation in the last hour: 1.23 in",
                "TSB20": "Thunderstorm began at :20",
            },
        ),
    ],
)
def test_translate(rmk: str, out: dict[str, str]) -> None:
    """Tests extracting translations from the remarks string"""
    data = remarks.parse(rmk)
    assert translate.remarks.translate(rmk, data) == out
