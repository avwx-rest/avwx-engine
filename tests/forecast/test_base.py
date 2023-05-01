"""
Forecast module parsing tests
"""

# pylint: disable=protected-access,missing-class-docstring

# stdlib
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Union

# library
import pytest

# module
from avwx import structs
from avwx.forecast import base

# tests
from tests.util import assert_code, assert_number, assert_timestamp


MAV_HEAD = """
KMCO   GFS MOS GUIDANCE    2/11/2020  0000 UTC
DT /FEB  11            /FEB  12                /FEB  13          /
HR   06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 18 00
"""

NBS_HEAD = """
KMCO    NBM V3.2 NBS GUIDANCE    7/19/2020  1600 UTC
DT      /JULY 20                /JULY 21                /JULY 22
UTC  21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15
FHR  05 08 11 14 17 20 23 26 29 32 35 38 41 44 47 50 53 56 59 62 65 68 71
"""


@pytest.mark.parametrize("target,length", ((0, 47), (1, 67), (2, 68)))
def test_trim_lines(target: int, length: int):
    """Tests trimming line length based on the length of a target line"""
    lines = base._trim_lines(MAV_HEAD.strip().split("\n"), target)
    assert len(lines) == 3
    for line in lines:
        assert length >= len(line)


@pytest.mark.parametrize(
    "size,prefix,expect",
    (
        (3, 0, ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]),
        (3, 3, ["2", "3", "4", "5", "6", "7", "8", "9", "0"]),
        (4, 0, ["1", "2  3", "4", "5", "6  7", "8", "9", "0"]),
        (2, 7, ["3", "4", "", "5", "6", "", "7", "8", "", "9", "0"]),
    ),
)
def test_split_line(size: int, prefix: int, expect: List[str]):
    """Tests splitting and stripping elements on a non-delineated line"""
    text = " 1  2  3  4  5  6  7  8  9  0 "
    assert base._split_line(text, size, prefix) == expect


def test_split_mav_line():
    text = "HR   06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 18 00 "
    line = base._split_line(text)
    assert len(line) == 21
    assert line[0] == "06"
    assert line[-1] == "00"


def test_split_mex_line():
    text = "FHR  24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192"
    line = base._split_line(text, size=4)
    assert len(line) == 15
    assert line[0] == "24"
    assert line[-1] == "192"


@pytest.mark.parametrize(
    "year,month,day,hour,minute,line",
    (
        (2020, 2, 11, 0, 0, "KMCO   GFS MOS GUIDANCE    2/11/2020  0000 UTC"),
        (2020, 12, 3, 12, 0, "KMCO   GFSX MOS GUIDANCE   12/03/2020  1200 UTC"),
    ),
)
def test_timestamp(year: int, month: int, day: int, hour: int, minute: int, line: str):
    """Tests Timestamp inference on the first line of the report"""
    time = base._timestamp(line)
    assert isinstance(time, structs.Timestamp)
    assert isinstance(time.repr, str)
    assert time.dt.year == year
    assert time.dt.month == month
    assert time.dt.day == day
    assert time.dt.hour == hour
    assert time.dt.minute == minute
    assert time.dt.second == 0


@pytest.mark.parametrize(
    "counters,line",
    (
        (
            [(18, 3), (2, 6)],
            base._split_line(
                "HR   06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 18 00 "
            ),
        ),
        (
            [(14, 12)],
            base._split_line(
                "FHR  24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192",
                size=4,
            ),
        ),
    ),
)
def test_find_time_periods(counters: List[Tuple[int, int]], line: List[str]):
    """Tests creating datetime objects from a line of hours-since values"""
    start_time = datetime(2020, 2, 11, 0, 0, tzinfo=timezone.utc)
    times = base._find_time_periods(line, start_time)
    time = start_time + timedelta(hours=int(line[0]))
    assert isinstance(times[0], dict)
    assert_timestamp(times[0]["time"], line[0], time)
    i = 1
    for j, delta in counters:
        for _ in range(j):
            time = time + timedelta(hours=delta)
            assert isinstance(times[i], dict)
            assert_timestamp(times[i]["time"], line[i], time)
            i += 1


@pytest.mark.parametrize(
    "report,time,line_length",
    (
        (MAV_HEAD, datetime(2020, 2, 11, 0, 0, tzinfo=timezone.utc), 3),
        (NBS_HEAD, datetime(2020, 7, 19, 16, 0, tzinfo=timezone.utc), 4),
    ),
)
def test_init_parse(report: str, time: datetime, line_length: int):
    """Tests first pass data creation and line splits"""
    data, lines = base._init_parse(report)
    assert isinstance(data, structs.ReportData)
    assert isinstance(lines, list)
    assert data.raw == report.strip()
    assert data.station == "KMCO"
    assert isinstance(data.time, structs.Timestamp)
    assert data.time.dt == time
    assert data.remarks is None
    assert len(lines) == line_length


@pytest.mark.parametrize(
    "numbers,line,prefix,postfix,decimal",
    (
        ([1, 2, None, 34], "NUM   1  2    34", "", "", None),
        ([10, 20, None, 340], "NUM   1  2    34", "", "0", None),
        ([110, 120, None, 1340], "NUM   1  2    34", "1", "0", None),
        ([1.1, 1.2, None, 13.4], "NUM   1  2    34", "1", "", -1),
    ),
)
def test_numbers(
    numbers: List[Union[int, float, None]],
    line: str,
    prefix: str,
    postfix: str,
    decimal: Optional[int],
):
    """Tests that number lines are converted to Number or None"""
    raw = line[4:]
    raw = [raw[i : (i + 3)].strip() for i in range(0, len(raw), 3)]
    for i, number in enumerate(base._numbers(line, 3, prefix, postfix, decimal)):
        num, text = numbers[i], raw[i]
        if num is None:
            assert number is None
        else:
            assert_number(number, text, num)


def test_code():
    """Tests that codes are properly mapped into Code dataclasses"""
    codes = {"A": 1, "B": 2}
    text = "COD A B   C"
    values = (("A", 1), ("B", 2), (None, None), ("C", "C"))
    for i, code in enumerate(base._code(codes)(text, size=2)):
        assert_code(code, *values[i])


class ForecastBase:
    report: base.Forecast

    def test_forecast_ete(self, ref: dict, icao: str, issued: datetime):
        """Performs an end-to-end test of all report JSON files"""
        station = self.report(icao)
        assert station.last_updated is None
        assert station.issued is None
        print(ref["data"]["raw"])
        assert station.parse(ref["data"]["raw"]) is True
        assert isinstance(station.last_updated, datetime)
        assert station.issued == issued
        # Clear timestamp due to parse_date limitations
        assert asdict(station.data) == ref["data"]
