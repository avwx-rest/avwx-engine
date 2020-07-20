"""
Forecast module parsing tests
"""

# pylint: disable=protected-access,missing-class-docstring

# stdlib
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

# module
from avwx import structs
from avwx.forecast import base

# tests
from tests.util import BaseTest, get_data


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


class TestForecastBase(BaseTest):
    def test_split_line(self):
        """
        Tests splitting and stripping elements on a non-delineated line
        """
        text = " 1  2  3  4  5  6  7  8  9  0 "
        for size, prefix, expect in (
            (3, 0, ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]),
            (3, 3, ["2", "3", "4", "5", "6", "7", "8", "9", "0"]),
            (4, 0, ["1", "2  3", "4", "5", "6  7", "8", "9", "0"]),
            (2, 7, ["3", "4", "", "5", "6", "", "7", "8", "", "9", "0"]),
        ):
            self.assertEqual(base._split_line(text, size, prefix), expect)
        # MAV line
        text = "HR   06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 18 00 "
        line = base._split_line(text)
        self.assertEqual(len(line), 21)
        self.assertEqual(line[0], "06")
        self.assertEqual(line[-1], "00")
        # MEX line
        text = "FHR  24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192"
        line = base._split_line(text, size=4)
        self.assertEqual(len(line), 15)
        self.assertEqual(line[0], "24")
        self.assertEqual(line[-1], "192")

    def test_timestamp(self):
        """
        Tests Timestamp inference on the first line of the report
        """
        for year, month, day, hour, minute, line in (
            (2020, 2, 11, 0, 0, "KMCO   GFS MOS GUIDANCE    2/11/2020  0000 UTC"),
            (2020, 12, 3, 12, 0, "KMCO   GFSX MOS GUIDANCE   12/03/2020  1200 UTC"),
        ):
            time = base._timestamp(line)
            self.assertIsInstance(time, structs.Timestamp)
            self.assertIsInstance(time.repr, str)
            self.assertEqual(time.dt.year, year)
            self.assertEqual(time.dt.month, month)
            self.assertEqual(time.dt.day, day)
            self.assertEqual(time.dt.hour, hour)
            self.assertEqual(time.dt.minute, minute)
            self.assertEqual(time.dt.second, 0)

    def test_find_time_periods(self):
        """
        Tests creating datetime objects from a line of hours-since values
        """
        start_time = datetime(2020, 2, 11, 0, 0, tzinfo=timezone.utc)
        for counters, line in (
            (
                ((18, 3), (2, 6)),
                base._split_line(
                    "HR   06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 18 00 "
                ),
            ),
            (
                ((14, 12),),
                base._split_line(
                    "FHR  24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192",
                    size=4,
                ),
            ),
        ):
            times = base._find_time_periods(line, start_time)
            time = start_time + timedelta(hours=int(line[0]))
            self.assertIsInstance(times[0], dict)
            self.assert_timestamp(times[0]["time"], line[0], time)
            i = 1
            for j, delta in counters:
                for _ in range(j):
                    time = time + timedelta(hours=delta)
                    self.assertIsInstance(times[i], dict)
                    self.assert_timestamp(times[i]["time"], line[i], time)
                    i += 1

    def test_init_parse(self):
        """
        Tests first pass data creation and line splits
        """
        for report, time, line_length in (
            (MAV_HEAD, datetime(2020, 2, 11, 0, 0, tzinfo=timezone.utc), 3),
            (NBS_HEAD, datetime(2020, 7, 19, 16, 0, tzinfo=timezone.utc), 4),
        ):
            data, lines = base._init_parse(report)
            self.assertIsInstance(data, dict)
            self.assertIsInstance(lines, list)
            self.assertEqual(data["raw"], report.strip())
            self.assertEqual(data["station"], "KMCO")
            self.assertIsInstance(data["time"], structs.Timestamp)
            self.assertEqual(data["time"].dt, time)
            self.assertIsNone(data["remarks"])
            self.assertEqual(len(lines), line_length)

    def test_numbers(self):
        """
        Tests that number lines are converted to Number or None
        """
        for numbers, text, postfix in (
            ([1, 2, None, 34], "NUM   1  2    34", ""),
            ([10, 20, None, 340], "NUM   1  2    34", "0"),
        ):
            for i, number in enumerate(base._numbers(text, postfix=postfix)):
                num = numbers[i]
                if num is None:
                    self.assertIsNone(number)
                else:
                    raw = str(num)
                    if postfix:
                        raw = raw[: -len(postfix)]
                    self.assert_number(number, raw, num)

    def test_code(self):
        """
        Tests that codes are properly mapped into Code dataclasses
        """
        codes = {"A": 1, "B": 2}
        text = "COD A B   C"
        values = (("A", 1), ("B", 2), (None, None), ("C", "C"))
        for i, code in enumerate(base._code(codes)(text, size=2)):
            self.assert_code(code, *values[i])


class ForecastBase(BaseTest):

    maxDiff = None

    def _test_gfs_ete(self, report: base.Forecast):
        """
        Performs an end-to-end test of all report JSON files
        """
        for ref, icao, issued in get_data(__file__, report.__class__.__name__.lower()):
            station = report(icao)
            self.assertIsNone(station.last_updated)
            self.assertIsNone(station.issued)
            self.assertTrue(station.update(ref["data"]["raw"]))
            self.assertIsInstance(station.last_updated, datetime)
            self.assertEqual(station.issued, issued)
            # Clear timestamp due to parse_date limitations
            self.assertEqual(asdict(station.data), ref["data"])
