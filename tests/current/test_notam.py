"""
NOTAM Report Tests
"""

# stdlib
from dataclasses import asdict
from datetime import datetime, timezone

# library
from dateutil.tz import gettz

# module
from avwx import structs
from avwx.current import notam
from avwx.static.core import IN_UNITS

# tests
from tests.util import BaseTest, get_data


QUALIFIERS = [
    structs.Qualifiers(
        repr="ZNY/QPIXX/I/NBO/A/000/999/4038N07346W025",
        fir="ZNY",
        subject=structs.Code("PI", "Instrument approach procedure"),
        condition=structs.Code("XX", "Unknown"),
        traffic=structs.Code("I", "IFR"),
        purpose=[
            structs.Code("N", "Immediate"),
            structs.Code("B", "Briefing"),
            structs.Code("O", "Flight Operations"),
        ],
        scope=[structs.Code("A", "Aerodrome")],
        lower=structs.Number("000", 0, "zero"),
        upper=structs.Number("999", 999, "nine nine nine"),
        coord=structs.Coord(40.38, -73.46, "4038N07346W"),
        radius=structs.Number("025", 25, "two five"),
    ),
    structs.Qualifiers(
        repr="ZJX/undefined/NBO/A/000/999/2825N08118W025",
        fir="ZJX",
        subject=None,
        condition=None,
        traffic=None,
        purpose=[
            structs.Code("N", "Immediate"),
            structs.Code("B", "Briefing"),
            structs.Code("O", "Flight Operations"),
        ],
        scope=[structs.Code("A", "Aerodrome")],
        lower=structs.Number("000", 0, "zero"),
        upper=structs.Number("999", 999, "nine nine nine"),
        coord=structs.Coord(28.25, -81.18, "2825N08118W"),
        radius=structs.Number("025", 25, "two five"),
    ),
    structs.Qualifiers(
        repr="EGTT/QWMLW/IV/BO /AW/000/001/5125N00028W002",
        fir="EGTT",
        subject=structs.Code("WM", "Missile, gun or rocket firing"),
        condition=structs.Code("LW", "Will take place"),
        traffic=structs.Code("IV", "IFR and VFR"),
        purpose=[
            structs.Code("B", "Briefing"),
            structs.Code("O", "Flight Operations"),
        ],
        scope=[
            structs.Code("A", "Aerodrome"),
            structs.Code("W", "Warning"),
        ],
        lower=structs.Number("000", 0, "zero"),
        upper=structs.Number("001", 1, "one"),
        coord=structs.Coord(51.25, -0.28, "5125N00028W"),
        radius=structs.Number("002", 2, "two"),
    ),
]


COPIED_TAG_REPORT = """
A3475/22 NOTAMN
Q) LIMM/QFAXX/IV/NBO/A/000/999/4537N00843E005
A) LIMC B) 2205182200 C) PERM
E) REF AIP AD 2 LIMC 1-12 ITEM 20 'LOCAL TRAFFIC REGULATIONS'
BOX 2 'APRON' PARAGRAPH 2.1 'ORDERLY MOVEMENT OF AIRCRAFT ON
APRONS' INDENT 4 'SERVICES PROVIDED' POINT C) 'FOLLOW-ME ASSISTANCE
PROVIDED ON PILOT'S REQUEST AND MANDATORY IN CASE' ADD THE FOLLOWING
IN CASE:
- GENERAL AVIATION AIRCRAFT UP TO ICAO CODE B (MAXIMUM WINGSPAN 24
METERS) AND HELICOPTERS ARRIVING AND DEPARTING FROM STANDS 301 TO 320
AND FROM 330 TO 336.
ARR TAXI ROUTE: AFTER TWR INSTRUCTIONS VIA APN TAXIWAY P-K TO
INTERMEDIATE HOLDING POSITION (IHP) K9 WHERE FOLLOW-ME CAR WILL
BE WAITING.
DEP TAXI ROUTE: AFTER TWR INSTRUCTIONS AND WITH FOLLOW-ME
ASSISTANCE VIA APN TAXIWAY N-K TO IHP K8
"""


class TestNotam(BaseTest):
    """Tests Notam class and parsing"""

    maxDiff = None

    def test_rear_coord(self):
        """Tests converting rear-loc coord string to Coord struct"""
        for text, lat, lon in (
            ("5126N00036W", 51.26, -0.36),
            ("1234S14321E", -12.34, 143.21),
            ("2413N01234W", 24.13, -12.34),
        ):
            coord = structs.Coord(lat, lon, text)
            self.assertEqual(notam._rear_coord(text), coord)
        self.assertIsNone(notam._rear_coord("latNlongE"))

    def test_header(self):
        """Tests parsing NOTAM headers"""
        for text, number, char, rtype, replaces in (
            ("01/113 NOTAMN", "01/113", "N", "New", None),
        ):
            ret_number, ret_type, ret_replaces = notam._header(text)
            code = structs.Code("NOTAM" + char, rtype)
            self.assertEqual(ret_number, number)
            self.assertEqual(ret_type, code)
            self.assertEqual(ret_replaces, replaces)

    def test_qualifiers(self):
        """Tests Qualifier struct parsing"""
        units = structs.Units(**IN_UNITS)
        for qualifier in QUALIFIERS:
            self.assertEqual(notam._qualifiers(qualifier.repr, units), qualifier)

    def test_make_year_timestamp(self):
        """Tests datetime conversion from year-prefixed strings"""
        for raw, trim, tz, dt in (
            (
                "2110121506",
                "2110121506",
                None,
                datetime(2021, 10, 12, 15, 6, tzinfo=timezone.utc),
            ),
            (
                "2205241452EST",
                "2205241452",
                "EST",
                datetime(2022, 5, 24, 14, 52, tzinfo=gettz("EST")),
            ),
            ("PERM", "PERM", None, datetime(2100, 1, 1, tzinfo=timezone.utc)),
        ):
            timestamp = structs.Timestamp(raw, dt)
            self.assertEqual(notam.make_year_timestamp(trim, raw, tz), timestamp)
        self.assertIsNone(notam.make_year_timestamp(" ", " ", None))

    def test_parse_linked_times(self):
        """Tests parsing start and end times with shared timezone"""
        for start, end, start_dt, end_dt in (
            (
                "2107221958",
                "2307221957EST",
                datetime(2021, 7, 22, 19, 58, tzinfo=gettz("EST")),
                datetime(2023, 7, 22, 19, 57, tzinfo=gettz("EST")),
            ),
            (
                "2203231000",
                "2303231300",
                datetime(2022, 3, 23, 10, 0, tzinfo=timezone.utc),
                datetime(2023, 3, 23, 13, 0, tzinfo=timezone.utc),
            ),
            (
                "2107221958EST",
                "",
                datetime(2021, 7, 22, 19, 58, tzinfo=gettz("EST")),
                None,
            ),
            (
                "",
                "2107221958",
                None,
                datetime(2021, 7, 22, 19, 58, tzinfo=timezone.utc),
            ),
            ("", "", None, None),
        ):
            ret_start, ret_end = notam.parse_linked_times(start, end)
            start_comp = structs.Timestamp(start, start_dt) if start_dt else None
            end_comp = structs.Timestamp(end, end_dt) if end_dt else None
            self.assertEqual(ret_start, start_comp)
            self.assertEqual(ret_end, end_comp)

    def test_copied_tag(self):
        """Tests an instance when the body includes a previously used tag value"""
        data = notam.Notams.from_report(COPIED_TAG_REPORT).data[0]
        self.assertTrue(data.body.startswith("REF AIP"))
        self.assertEqual(data.end_time.repr, "PERM")
        self.assertIsInstance(data.end_time.dt, datetime)

    def test_parse(self):
        """Tests returned structs from the parse function"""
        report = "01/113 NOTAMN \r\nQ) ZNY/QMXLC/IV/NBO/A/000/999/4038N07346W005 \r\nA) KJFK \r\nB) 2101081328 \r\nC) 2209301100 \r\n\r\nE) TWY TB BTN TERMINAL 8 RAMP AND TWY A CLSD"
        data, _ = notam.parse(report)
        self.assertIsInstance(data, structs.NotamData)
        self.assertEqual(data.raw, report)

    def test_sanitize(self):
        """Tests report sanitization"""
        for line, fixed in (("01/113 NOTAMN \r\nQ) 1234", "01/113 NOTAMN \nQ) 1234"),):
            self.assertEqual(notam.sanitize(line), fixed)

    def test_notam_e2e(self):
        """Performs an end-to-end test of all NOTAM JSON files"""
        for ref, icao, _ in get_data(__file__, "notam"):
            station = notam.Notams(icao)
            self.assertIsNone(station.last_updated)
            reports = [report["data"]["raw"] for report in ref["reports"]]
            self.assertTrue(station.parse(reports))
            self.assertIsInstance(station.last_updated, datetime)
            for parsed, report in zip(station.data, ref["reports"]):
                self.assertEqual(asdict(parsed), report["data"])
