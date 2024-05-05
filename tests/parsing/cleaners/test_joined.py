"""
Joined space cleaner tests
"""

import pytest

from avwx.parsing.sanitization.cleaners import joined as cleaners


@pytest.mark.parametrize(
    "item,index",
    (
        ("OVC010FEW040", 6),
        ("SCT012CBOVC030TCU", 8),
        ("BKN01826/25", 6),
        ("BKN018M01/M05", 6),
    ),
)
def test_joined_cloud(item: str, index: str):
    assert cleaners.JoinedCloud().split_at(item) == index


@pytest.mark.parametrize(
    "item",
    ("OVC012", "FEW100CB", "TX12/12/12"),
)
def test_not_joined_cloud(item: str):
    assert cleaners.JoinedCloud().split_at(item) is None


@pytest.mark.parametrize(
    "item,index",
    (
        ("123456Z36010KT", 7),
        ("161200Z10SM", 7),
        ("1210/12169999", 9),
    ),
)
def test_joined_timestamp(item: str, index: str):
    assert cleaners.JoinedTimestamp().split_at(item) == index


@pytest.mark.parametrize(
    "item",
    ("123456Z", "1210/1216", "TX12/12/12", "PROB30", "KTFM"),
)
def test_not_joined_timestamp(item: str):
    assert cleaners.JoinedTimestamp().split_at(item) is None


@pytest.mark.parametrize(
    "item,index",
    (
        # TODO: Add tests for non KT units
        ("36010KT10SM", 7),
        ("VRB10KTOVC010", 7),
        ("36010G15KT1210/1216", 10),
    ),
)
def test_joined_wind(item: str, index: str):
    assert cleaners.JoinedWind().split_at(item) == index


@pytest.mark.parametrize(
    "item",
    ("123456Z", "VRB10KT", "10SM"),
)
def test_not_joined_wind(item: str):
    assert cleaners.JoinedWind().split_at(item) is None


@pytest.mark.parametrize(
    "item,index",
    (
        ("21016G28KTPROB40", 10),
        ("VCSHINTER", 4),
    ),
)
def test_joined_taf_new_line(item: str, index: str):
    assert cleaners.JoinedTafNewLine().split_at(item) == index


@pytest.mark.parametrize(
    "item,index",
    (
        ("TX32/2521ZTN24/2512Z", 10),
        ("TN24/2512ZTX32/2521Z", 10),
    ),
)
def test_joined_min_max_temperature(item: str, index: str):
    assert cleaners.JoinedMinMaxTemperature().split_at(item) == index


@pytest.mark.parametrize(
    "item",
    ("TX32/2521Z", "TXTN", "KMCO"),
)
def test_not_joined_min_max_temperature(item: str):
    assert cleaners.JoinedMinMaxTemperature().split_at(item) is None


@pytest.mark.parametrize(
    "item,index",
    (
        # TODO: Implement commented tests
        ("R36/1500DR18/P2000", 9),
        # ("R10C/2500FTTX32/2521Z", 11),
        # ("R04/0500KMCO", 8),
    ),
)
def test_joined_runway_visibility(item: str, index: str):
    assert cleaners.JoinedRunwayVisibility().split_at(item) == index


@pytest.mark.parametrize(
    "item",
    ("TX32/2521Z", "R01/1000FT", "KMCO"),
)
def test_not_joined_runway_visibility(item: str):
    assert cleaners.JoinedRunwayVisibility().split_at(item) is None
