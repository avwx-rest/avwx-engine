"""
Separated space cleaner tests
"""

import pytest

from avwx.parsing.sanitization.cleaners import separated as cleaners


@pytest.mark.parametrize(
    "first,second",
    (
        ("10", "SM"),
        ("1", "0SM"),
    ),
)
def test_separated_distance(first: str, second: str):
    assert cleaners.SeparatedDistance().can_handle(first, second) is True


@pytest.mark.parametrize("first,second", (("KMCO", "10SM"),))
def test_not_separated_distance(first: str, second: str):
    assert cleaners.SeparatedDistance().can_handle(first, second) is False


@pytest.mark.parametrize(
    "first,second",
    (
        # TODO: Add tests for M01
        ("12", "/10"),
        ("01", "/00"),
    ),
)
def test_separated_first_temperature(first: str, second: str):
    assert cleaners.SeparatedFirstTemperature().can_handle(first, second) is True


@pytest.mark.parametrize(
    "first,second",
    (
        ("9999", "/Z"),
        ("KMCO", "/12"),
    ),
)
def test_not_separated_first_temperature(first: str, second: str):
    assert cleaners.SeparatedFirstTemperature().can_handle(first, second) is False


@pytest.mark.parametrize(
    "first,second",
    (
        ("OVC", "040"),
        ("FEW", "100"),
    ),
)
def test_separated_cloud_altitude(first: str, second: str):
    assert cleaners.SeparatedCloudAltitude().can_handle(first, second) is True


@pytest.mark.parametrize(
    "first,second",
    (
        ("OVC040", "9999"),
        ("FEW", "PLANES"),
    ),
)
def test_not_separated_cloud_altitude(first: str, second: str):
    assert cleaners.SeparatedCloudAltitude().can_handle(first, second) is False


@pytest.mark.parametrize(
    "first,second",
    (
        # TODO: Add tests for M01
        ("12/", "10"),
        ("01/", "00"),
    ),
)
def test_separated_second_temperature(first: str, second: str):
    assert cleaners.SeparatedSecondTemperature().can_handle(first, second) is True


@pytest.mark.parametrize(
    "first,second",
    (
        ("TX/", "12"),
        ("TN/", "9999"),
    ),
)
def test_not_separated_second_temperature(first: str, second: str):
    assert cleaners.SeparatedSecondTemperature().can_handle(first, second) is False


@pytest.mark.parametrize(
    "first,second",
    (
        ("Q", "1001"),
        ("Q", "0998"),
        ("A", "2992"),
        ("A", "3011"),
    ),
)
def test_separated_altimeter_letter(first: str, second: str):
    assert cleaners.SeparatedAltimeterLetter().can_handle(first, second) is True


@pytest.mark.parametrize(
    "first,second",
    (
        ("Q", "9999"),
        ("A", "9999"),
        ("Z", "2992"),
        ("A", "B"),
    ),
)
def test_not_separated_altimeter_letter(first: str, second: str):
    assert cleaners.SeparatedAltimeterLetter().can_handle(first, second) is False


@pytest.mark.parametrize(
    "first,second",
    (
        # TODO: Add tests for M01
        ("12/1", "0"),
        ("04/0", "1"),
    ),
)
def test_separated_temperature_trailing_digit(first: str, second: str):
    assert (
        cleaners.SeparatedTemperatureTrailingDigit().can_handle(first, second) is True
    )


@pytest.mark.parametrize(
    "first,second",
    (
        ("12/1", "9999"),
        ("KMCO", "0"),
    ),
)
def test_not_separated_temperature_trailing_digit(first: str, second: str):
    assert (
        cleaners.SeparatedTemperatureTrailingDigit().can_handle(first, second) is False
    )


@pytest.mark.parametrize(
    "first,second",
    (
        # TODO: Add tests for non KT units
        ("36010G20", "KT"),
        ("VRB04G15", "KT"),
        ("10320", "KT"),
        ("36010K", "T"),
        ("VRB11K", "T"),
    ),
)
def test_separated_wind_unit(first: str, second: str):
    assert cleaners.SeparatedWindUnit().can_handle(first, second) is True


@pytest.mark.parametrize(
    "first,second",
    (
        ("36005KT", "KT"),
        ("KMCO", "KT"),
    ),
)
def test_not_separated_wind_unit(first: str, second: str):
    assert cleaners.SeparatedWindUnit().can_handle(first, second) is False


@pytest.mark.parametrize(
    "first,second",
    (
        ("OVC022", "CB"),
        ("FEW040", "TCU"),
    ),
)
def test_separated_cloud_qualifier(first: str, second: str):
    assert cleaners.SeparatedCloudQualifier().can_handle(first, second) is True


@pytest.mark.parametrize(
    "first,second",
    (
        ("OVC040", "OVC050"),
        ("36010KT", "SKC"),
    ),
)
def test_not_separated_cloud_qualifier(first: str, second: str):
    assert cleaners.SeparatedCloudQualifier().can_handle(first, second) is False


@pytest.mark.parametrize(
    "first,second",
    (
        ("FM", "122400"),
        ("TL", "160400Z"),
    ),
)
def test_separated_taf_time_prefix(first: str, second: str):
    assert cleaners.SeparatedTafTimePrefix().can_handle(first, second) is True


@pytest.mark.parametrize(
    "first,second",
    (
        ("FM", "10SM"),
        ("TL", "12/03"),
    ),
)
def test_not_separated_taf_time_prefix(first: str, second: str):
    assert cleaners.SeparatedTafTimePrefix().can_handle(first, second) is False


@pytest.mark.parametrize(
    "first,second",
    (
        ("TX", "20/10"),
        ("TN", "M01/12"),
    ),
)
def test_separated_min_max_temperature_prefix(first: str, second: str):
    assert cleaners.SeparatedMinMaxTemperaturePrefix().can_handle(first, second) is True


@pytest.mark.parametrize(
    "first,second",
    (
        ("TX", "9999"),
        ("KMCO", "20/10"),
    ),
)
def test_not_separated_min_max_temperature_prefix(first: str, second: str):
    assert (
        cleaners.SeparatedMinMaxTemperaturePrefix().can_handle(first, second) is False
    )
