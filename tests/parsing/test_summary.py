"""Test summary functions."""

# module
from avwx import structs
from avwx.parsing import summary


def test_metar() -> None:
    """Test that METAR translations are summarized in the proper order."""
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
    text = (
        "Winds N-360 (variable 340 to 020) at 12kt gusting to 20kt, "
        "Vis 3sm, Temp 3°C, Dew -1°C, Alt 29.92 inHg, "
        "Heavy Rain, Broken layer at 1500ft (Cumulonimbus)"
    )
    assert summary.metar(trans) == text


def test_taf() -> None:
    """Test that TAF line translations are summarized in the proper order."""
    trans = structs.TafLineTrans(
        altimeter="29.92 inHg (1013 hPa)",
        clouds="Broken layer at 1500ft (Cumulonimbus) - Reported AGL",
        icing="Light icing from 10000ft to 15000ft",
        turbulence="Occasional moderate turbulence in clouds from 5500ft to 8500ft",
        visibility="3sm (4.8km)",
        wind_shear="Wind shear 2000ft from 070 at 40kt",
        wind="N-360 at 12kt gusting to 20kt",
        wx_codes="Heavy Rain",
    )
    text = (
        "Winds N-360 at 12kt gusting to 20kt, Vis 3sm, Alt 29.92 inHg, "
        "Heavy Rain, Broken layer at 1500ft (Cumulonimbus), "
        "Wind shear 2000ft from 070 at 40kt, "
        "Occasional moderate turbulence in clouds from 5500ft to 8500ft, "
        "Light icing from 10000ft to 15000ft"
    )
    assert summary.taf(trans) == text
