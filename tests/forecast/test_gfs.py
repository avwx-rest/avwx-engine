"""
"""

# stdlib
from datetime import datetime, timedelta, timezone

# module
from avwx import structs
from avwx.forecast import gfs

# tests
from tests.util import BaseTest, get_data


class TestGfs(BaseTest):
    """
    """

    def test_split_line(self):
        """
        """
        text = " 1  2  3  4  5  6  7  8  9  0 "
        for size, prefix, expect in (
            (3, 0, ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]),
            (3, 3, ["2", "3", "4", "5", "6", "7", "8", "9", "0"]),
            (4, 0, ["1", "2  3", "4", "5", "6  7", "8", "9"]),
            (2, 7, ["3", "4", "", "5", "6", "", "7", "8", "", "9", "0"]),
        ):
            self.assertEqual(gfs._split_line(text, size, prefix), expect)

    def test_timestamp(self):
        """
        """
        for year, month, day, hour, minute, line in (
            (2020, 2, 11, 0, 0, "KMCO   GFS MOS GUIDANCE    2/11/2020  0000 UTC"),
            (2020, 12, 3, 12, 0, "KMCO   GFSX MOS GUIDANCE   12/03/2020  1200 UTC"),
        ):
            time = gfs._timestamp(line)
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
        """
        start_time = datetime(2020, 2, 11, 0, 0, tzinfo=timezone.utc)
        for counters, line in (
            (
                ((18, 3), (2, 6)),
                gfs._split_line(
                    "HR   06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 18 00 "
                ),
            ),
            (
                ((13, 12),),
                gfs._split_line(
                    "FHR  24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192",
                    size=4,
                    prefix=4,
                ),
            ),
        ):
            times = gfs._find_time_periods(line, start_time)
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


#     def test_init_parse(self):
#         """
#         """
#         pass

#     def test_numbers(self):
#         """
#         """
#         pass

#     def test_wind_direction(self):
#         """
#         """
#         pass

#     def test_code(self):
#         """
#         """
#         pass

#     def test_handlers(self):
#         """
#         """
#         pass


# class TestMav(BaseTest):
#     """
#     """

#     def test_thunder(self):
#         """
#         """
#         pass

#     def test_mav_handlers(self):
#         """
#         """
#         pass

#     def test_mav_ete(self):
#         """
#         """
#         pass


# class TestMex(BaseTest):
#     """
#     """

#     def test_mex_handlers(self):
#         """
#         """
#         pass

#     def test_mex_ete(self):
#         """
#         """
#         pass
