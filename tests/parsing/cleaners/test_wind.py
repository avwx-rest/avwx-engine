"""
Wind cleaner tests
"""

import pytest

from avwx.parsing.sanitization.cleaners import wind as cleaners


@pytest.mark.parametrize(
    "wind,fixed",
    (
        ("O6O/10G18K", "06010G18KT"),
        ("VRBL03KT", "VRB03KT"),
        ("12007G15SM", "12007G15KT"),
        ("16010FG16KT", "16010G16KT"),
        ("20017SQ28KT", "20017G28KT"),
        ("VRB10G19MPSM", "VRB10G19MPS"),
        ("33010G20KTKT", "33010G20KT"),
        ("VRB16G36KTKT", "VRB16G36KT"),
        ("WBB010", "VRB010"),
    ),
)
def test_sanitize_wind(wind: str, fixed: str):
    """Tests the wind sanitization before checks"""
    assert cleaners.sanitize_wind(wind) == fixed


@pytest.mark.parametrize("item", (f"{'/'*i}KT" for i in range(1, 8)))
def test_empty_wind(item: str):
    assert cleaners.EmptyWind().can_handle(item) is True


@pytest.mark.parametrize("item", ("/////", "KMCO", "//SM", "TX12/1234"))
def test_not_empty_wind(item: str):
    assert cleaners.EmptyWind().can_handle(item) is False


@pytest.mark.parametrize("item,clean", (("22022KTG40", "22022G40KT"),))
def test_misplaced_wind_kt(item: str, clean: str):
    cleaner = cleaners.MisplaceWindKT()
    assert cleaner.can_handle(item) is True
    assert cleaner.clean(item) == clean


@pytest.mark.parametrize("item", ("KTEX"))
def test_not_misplaced_wind_kt(item: str):
    assert cleaners.MisplaceWindKT().can_handle(item) is False


@pytest.mark.parametrize("item,clean", (("360G17G32KT", "36017G32KT"),))
def test_double_gust(item: str, clean: str):
    cleaner = cleaners.DoubleGust()
    assert cleaner.can_handle(item) is True
    assert cleaner.clean(item) == clean


@pytest.mark.parametrize("item", ("KMCO", "22022G40KT", "VRB05KT"))
def test_not_double_gust(item: str):
    assert cleaners.DoubleGust().can_handle(item) is False


@pytest.mark.parametrize(
    "item,clean",
    (
        ("ABC36017G32KT", "36017G32KT"),
        ("ABCVRB12KT", "VRB12KT"),
    ),
)
def test_wind_leading_mistype(item: str, clean: str):
    cleaner = cleaners.WindLeadingMistype()
    assert cleaner.can_handle(item) is True
    assert cleaner.clean(item) == clean


@pytest.mark.parametrize("item", ("36017G32KT", "WS020/07040", "WS020/07040KT"))
def test_not_wind_leading_mistype(item: str):
    assert cleaners.WindLeadingMistype().can_handle(item) is False


@pytest.mark.parametrize("item,clean", (("14010-15KT", "14010G15KT"),))
def test_non_g_gust(item: str, clean: str):
    cleaner = cleaners.NonGGust()
    assert cleaner.can_handle(item) is True
    assert cleaner.clean(item) == clean


@pytest.mark.parametrize("item", ("36017G32KT",))
def test_not_non_g_gust(item: str):
    assert cleaners.NonGGust().can_handle(item) is False


@pytest.mark.parametrize("item,clean", (("2VRB02KT", "VRB02KT"),))
def test_remove_vrb_leading_digits(item: str, clean: str):
    cleaner = cleaners.RemoveVrbLeadingDigits()
    assert cleaner.can_handle(item) is True
    assert cleaner.clean(item) == clean


@pytest.mark.parametrize("item", ("36017G32KT", "VRB12KT"))
def test_not_remove_vrb_leading_digits(item: str):
    assert cleaners.RemoveVrbLeadingDigits().can_handle(item) is False
