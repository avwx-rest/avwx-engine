"""
GFS service forecast parsing tests
"""

# pylint: disable=protected-access,missing-class-docstring,redefined-builtin

# stdlib
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

# module
from avwx import structs
from avwx.forecast import gfs

# tests
from tests.util import BaseTest, get_data

MAV_REPORT = """
KMCO   GFS MOS GUIDANCE    2/11/2020  0000 UTC                      
DT /FEB  11            /FEB  12                /FEB  13          /  
HR   06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 18 00 
X/N                    85          67          87          66    85 
TMP  66 65 65 74 82 84 76 72 70 69 69 77 84 85 77 72 70 68 68 82 77 
DPT  64 64 64 68 66 64 66 68 68 67 67 69 66 65 66 67 67 66 66 67 66 
CLD  BK OV OV BK SC BK SC SC SC OV BK SC BK BK SC FW SC SC BK BK BK 
WDR  13 14 14 16 18 18 14 17 30 36 09 16 16 16 15 16 16 17 18 20 21 
WSP  05 04 03 08 08 07 06 04 02 01 01 06 12 11 06 06 05 04 04 12 06 
P06         2     2     4    12     5     7     1     0     6  5 26 
P12                     4          15           8           6    33 
Q06         0     0     0     0     0     0     0     0     0  0  0 
Q12                     0           0           0           0     0 
T06      0/16  0/ 5  1/ 3  2/ 0  1/18  1/ 6  1/18  0/ 2  0/ 6 12/14 
T12            0/16        2/ 8        1/18        2/18     1/ 6    
POZ   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0 
POS   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  1  0  0  0 
TYP   R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R 
CIG   8  3  2  8  8  8  8  8  8  6  6  8  6  8  8  8  8  8  5  6  8 
VIS   7  7  4  7  7  7  7  7  7  5  1  7  7  7  7  7  7  7  5  7  7 
OBV   N  N BR  N  N  N  N  N  N BR FG  N  N  N  N  N  N  N BR  N  N
"""

MEX_REPORT = """
KMCO   GFSX MOS GUIDANCE   2/03/2020  1200 UTC                       
FHR  24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192      
     TUE 04| WED 05| THU 06| FRI 07| SAT 08| SUN 09| MON 10|TUE CLIMO
N/X  50  76| 57  81| 66  83| 58  68| 47  74| 56  74| 60  80| 62 49 73
TMP  52  67| 59  72| 68  73| 58  59| 49  66| 58  65| 62  70| 64      
DPT  48  55| 57  66| 67  63| 48  40| 42  53| 54  55| 58  62| 62      
CLD  CL  CL| PC  OV| OV  OV| OV  PC| PC  CL| PC  PC| PC  OV| PC      
WND   4   6|  4  10| 10  18| 15  12|  7  10|  7  11|  9  10|  7      
P12   1   1|  3  19| 30  45| 84  14|  8   8| 16  13| 14  19| 16 14 19
P24       1|     26|     53|    100|      8|     23|     25|       25
Q12   0   0|  0   0|  0   1|  4   0|  0   0|  0   0|       |         
Q24       0|      0|      1|      4|      0|      0|       |         
T12   0   0|  0   6|  6  14|  5   0|  0   3|  3   4|  2   8|  3      
T24        |  2    |  6    | 30    |  1    |  3    |  4    | 11      
PZP   0   0|  0   0|  0   1|  1   0|  0   1|  1   1|  1   0|  0      
PSN   0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0      
PRS   0   0|  0   0|  1   1|  0   1|  1   2|  1   1|  2   1|  1      
TYP   R   R|  R   R|  R   R|  R   R|  R   R|  R   R|  R   R|  R      
SNW        |      4|      0|      0|      0|      0|       |         
"""


class TestGfs(BaseTest):
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
            self.assertEqual(gfs._split_line(text, size, prefix), expect)
        # MAV line
        text = "HR   06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 18 00 "
        line = gfs._split_line(text)
        self.assertEqual(len(line), 21)
        self.assertEqual(line[0], "06")
        self.assertEqual(line[-1], "00")
        # MEX line
        text = "FHR  24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192"
        line = gfs._split_line(text, size=4)
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
        Tests creating datetime objects from a line of hours-since values
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
                ((14, 12),),
                gfs._split_line(
                    "FHR  24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192",
                    size=4,
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

    def test_init_parse(self):
        """
        Tests first pass data creation and line splits
        """
        for report, time, line_length in (
            (MAV_REPORT, datetime(2020, 2, 11, 0, 0, tzinfo=timezone.utc), 21),
            (MEX_REPORT, datetime(2020, 2, 3, 12, 0, tzinfo=timezone.utc), 19),
        ):
            data, lines = gfs._init_parse(report)
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
            for i, number in enumerate(gfs._numbers(text, postfix=postfix)):
                num = numbers[i]
                if num is None:
                    self.assertIsNone(number)
                else:
                    repr = str(num)
                    if postfix:
                        repr = repr[: -len(postfix)]
                    self.assert_number(number, repr, num)

    def test_wind_direction(self):
        """
        Tests that a line is converted into wind direction Number dataclasses
        """
        text = "WDR 12    34"
        values = (("12", 120), (None, None), ("34", 340))
        for i, number in enumerate(gfs._wind_direction(text)):
            self.assert_number(number, *values[i])

    def test_code(self):
        """
        Tests that codes are properly mapped into Code dataclasses
        """
        codes = {"A": 1, "B": 2}
        text = "COD A B   C"
        values = (("A", 1), ("B", 2), (None, None), ("C", "C"))
        for i, code in enumerate(gfs._code(codes)(text, size=2)):
            self.assert_code(code, *values[i])


class GfsForecastBase(BaseTest):

    maxDiff = None

    def _test_gfs_ete(self, report: gfs.Forecast):
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


class TestMav(GfsForecastBase):
    def test_thunder(self):
        """
        Tests that a line is converted into Number tuples
        """
        text = "T06     12/16  0/ 5"
        _values = (None, None, (("12", 12), ("16", 16)), None, (("0", 0), ("5", 5)))
        for codes, values in zip(gfs._thunder(text), _values):
            if values is None:
                self.assertIsNone(codes)
            else:
                for code, value in zip(codes, values):
                    self.assert_number(code, *value)

    def test_mav_ete(self):
        """
        Performs an end-to-end test of all MAV JSON files
        """
        self._test_gfs_ete(gfs.Mav)


class TestMex(GfsForecastBase):
    def test_mex_ete(self):
        """
        Performs an end-to-end test of all MEX JSON files
        """
        self._test_gfs_ete(gfs.Mex)
