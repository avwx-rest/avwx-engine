"""NOTAM Report Tests."""

# ruff: noqa: SLF001

# stdlib
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

# library
import pytest
from dateutil.tz import gettz

# module
from avwx import structs
from avwx.current import notam
from avwx.static.notam import SUBJECT, TRANSPOSED_SUBJECT

# tests
from tests.util import get_data

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
        lower=structs.Altitude("000", 0, "zero"),
        upper=structs.Altitude("999", 999, "nine nine nine"),
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
        lower=structs.Altitude("000", 0, "zero"),
        upper=structs.Altitude("999", 999, "nine nine nine"),
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
        lower=structs.Altitude("000", 0, "zero"),
        upper=structs.Altitude("001", 1, "one"),
        coord=structs.Coord(51.25, -0.28, "5125N00028W"),
        radius=structs.Number("002", 2, "two"),
    ),
    structs.Qualifiers(
        repr="OIIX/QPIXX/A/000/999/",
        fir="OIIX",
        subject=structs.Code("PI", "Instrument approach procedure"),
        condition=structs.Code("XX", "Unknown"),
        traffic=None,
        purpose=[],
        scope=[
            structs.Code("A", "Aerodrome"),
        ],
        lower=structs.Altitude("000", 0, "zero"),
        upper=structs.Altitude("999", 999, "nine nine nine"),
        coord=None,
        radius=None,
    ),
    structs.Qualifiers(
        repr="FSSS/QXXXX/IV/NBO/AE/000/999",
        fir="FSSS",
        subject=structs.Code("XX", "Unknown"),
        condition=structs.Code("XX", "Unknown"),
        traffic=structs.Code("IV", "IFR and VFR"),
        purpose=[
            structs.Code("N", "Immediate"),
            structs.Code("B", "Briefing"),
            structs.Code("O", "Flight Operations"),
        ],
        scope=[
            structs.Code("A", "Aerodrome"),
            structs.Code("E", "En Route"),
        ],
        lower=structs.Altitude("000", 0, "zero"),
        upper=structs.Altitude("999", 999, "nine nine nine"),
        coord=None,
        radius=None,
    ),
    structs.Qualifiers(
        repr="FQBE/QWLPW/IV/NBO/W/000/012 255550S323435E",
        fir="FQBE",
        subject=structs.Code("WL", "Ascent of free balloon"),
        condition=structs.Code(repr="PW", value="Unknown"),
        traffic=structs.Code("IV", "IFR and VFR"),
        purpose=[
            structs.Code("N", "Immediate"),
            structs.Code("B", "Briefing"),
            structs.Code("O", "Flight Operations"),
        ],
        scope=[
            structs.Code("W", "Warning"),
        ],
        lower=structs.Altitude("000", 0, "zero"),
        upper=structs.Altitude("012", 12, "one two"),
        coord=None,
        radius=None,
    ),
    structs.Qualifiers(
        repr="MMFR/QOBCE//M/AE/000/999/1645N09947W",
        fir="MMFR",
        subject=structs.Code("OB", "Obstacle"),
        condition=structs.Code("CE", "Erected"),
        traffic=None,
        purpose=[
            structs.Code("M", "Miscellaneous"),
        ],
        scope=[
            structs.Code("A", "Aerodrome"),
            structs.Code("E", "En Route"),
        ],
        lower=structs.Altitude("000", 0, "zero"),
        upper=structs.Altitude("999", 999, "nine nine nine"),
        coord=structs.Coord(16.45, -99.47, "1645N09947W"),
        radius=None,
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


@pytest.mark.parametrize(
    ("text", "lat", "lon"),
    [
        ("5126N00036W", 51.26, -0.36),
        ("1234S14321E", -12.34, 143.21),
        ("2413N01234W", 24.13, -12.34),
    ],
)
def test_rear_coord(text: str, lat: float, lon: float) -> None:
    """Test converting rear-loc coord string to Coord struct."""
    coord = structs.Coord(lat, lon, text)
    assert notam._rear_coord(text) == coord


@pytest.mark.parametrize("text", ["latNlongE", "2102N086"])
def test_bad_rear_coord(text: str) -> None:
    assert notam._rear_coord(text) is None


@pytest.mark.parametrize(
    ("text", "number", "char", "rtype", "replaces"),
    [
        ("01/113 NOTAMN", "01/113", "N", "New", None),
    ],
)
def test_header(text: str, number: str, char: str, rtype: str, replaces: str | None) -> None:
    """Test parsing NOTAM headers."""
    ret_number, ret_type, ret_replaces = notam._header(text)
    code = structs.Code(f"NOTAM{char}", rtype)
    assert ret_number == number
    assert ret_type == code
    assert ret_replaces == replaces


@pytest.mark.parametrize("qualifier", QUALIFIERS)
def test_qualifiers(qualifier: structs.Qualifiers) -> None:
    """Test Qualifier struct parsing."""
    units = structs.Units.international()
    assert notam._qualifiers(qualifier.repr, units) == qualifier


@pytest.mark.parametrize(
    ("text", "subject"),
    [
        ("KFDC/QCHXX////000/999/", structs.Code("CH", "Chart")),
        ("EGTT/QPPCH/I/NBO/A/000/999/5129N00028W005", structs.Code("PP", "Obstacle clearance height")),
    ],
)
def test_qualifiers_subject(text: str, subject: structs.Code) -> None:
    """Test Q-code subjects outside the core ICAO table."""
    qualifiers = notam._qualifiers(text, structs.Units.international())
    assert qualifiers.subject == subject


@pytest.mark.parametrize(
    ("raw", "trim", "tz", "dt"),
    [
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
    ],
)
def test_make_year_timestamp(raw: str, trim: str, tz: str | None, dt: datetime) -> None:
    """Test datetime conversion from year-prefixed strings."""
    timestamp = structs.Timestamp(raw, dt)
    assert notam.make_year_timestamp(trim, raw, tz) == timestamp


@pytest.mark.parametrize(
    ("raw", "code", "value"),
    [
        ("PERM", "PERM", "Permanent"),
        ("PERM\n123", "PERM", "Permanent"),
        ("WIE", "WIE", "With Immediate Effect"),
    ],
)
def test_timestamp_codes(raw: str, code: str, value: str) -> None:
    """Test datetime conversion when given a known code."""
    assert notam.make_year_timestamp(raw, raw) == structs.Code(code, value)


def test_bad_year_timestamp() -> None:
    assert notam.make_year_timestamp(" ", " ", None) is None


@pytest.mark.parametrize(
    ("raw", "trim", "tz"),
    [
        # FAA checklist NOTAMs use hour 80 as a placeholder
        ("2604018000", "2604018000", None),
        ("2605018000 EST", "2605018000 ", "EST"),
        # 29 Feb in a non-leap year
        ("2502292359", "2502292359", None),
    ],
)
def test_impossible_year_timestamp(raw: str, trim: str, tz: str | None) -> None:
    """A value that is not a real time keeps its repr without a datetime."""
    assert notam.make_year_timestamp(trim, raw, tz) == structs.Timestamp(raw, None)


def test_parse_impossible_timestamps() -> None:
    """An impossible B) or C) time does not prevent parsing the rest of the report."""
    report = (
        "A1111/25 NOTAMR A1110/25 Q) ANYN/QKKKK/K/K/K/000/999/0032S16655E000 A) ANYN "
        "B) 2604018000 C) 2605018000 EST E) CHECKLIST YEAR=2025 0076 0080 0079"
    )
    data, _ = notam.parse(report)
    assert data.number == "A1111/25"
    assert data.station == "ANYN"
    assert data.start_time == structs.Timestamp("2604018000", None)
    assert data.end_time == structs.Timestamp("2605018000 EST", None)
    assert data.body == "CHECKLIST YEAR=2025 0076 0080 0079"


@pytest.mark.parametrize(
    ("start", "end", "start_dt", "end_dt"),
    [
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
        (
            "2303070658",
            "2306042200 EST",
            datetime(2023, 3, 7, 6, 58, tzinfo=gettz("EST")),
            datetime(2023, 6, 4, 22, 0, tzinfo=gettz("EST")),
        ),
        ("", "", None, None),
    ],
)
def test_parse_linked_times(start: str, end: str, start_dt: datetime | None, end_dt: datetime | None) -> None:
    """Test parsing start and end times with shared timezone."""
    ret_start, ret_end = notam.parse_linked_times(start, end)
    start_comp = structs.Timestamp(start, start_dt) if start_dt else None
    end_comp = structs.Timestamp(end, end_dt) if end_dt else None
    assert ret_start == start_comp
    assert ret_end == end_comp


@pytest.mark.parametrize(
    ("raw", "value", "flight_level"),
    [
        ("000", 0, False),
        ("999", 999, False),
        ("9500FT.", 9500, False),
        # Flight levels, however they are written
        ("FL150", 150, True),
        ("F430", 430, True),
        # Strict altitudes are not flight levels
        ("SFC", 0, False),
        ("UNL", 999, False),
        ("7000FT AMSL", 7000, False),
    ],
)
def test_make_altitude(raw: str, value: int, flight_level: bool) -> None:  # noqa: FBT001
    """Test altitude parsing."""
    altitude = notam.make_altitude(raw, structs.Units.international())
    assert isinstance(altitude, structs.Altitude)
    assert altitude.value == value
    assert altitude.flight_level is flight_level


@pytest.mark.parametrize("raw", ["", "G", "AGL", "TWY CLSD"])
def test_bad_altitude(raw: str) -> None:
    """Test filtering bad altitude values."""
    assert notam.make_altitude(raw, structs.Units.international()) is None


def test_copied_tag() -> None:
    """Test an instance when the body includes a previously used tag value."""
    resp = notam.Notams.from_report(COPIED_TAG_REPORT)
    assert resp is not None
    assert resp.data is not None
    data = resp.data[0]
    assert data.body.startswith("REF AIP") is True
    assert isinstance(data.end_time, structs.Code)
    assert data.end_time.repr == "PERM"


def test_parse() -> None:
    """Test returned structs from the parse function."""
    report = "01/113 NOTAMN \r\nQ) ZNY/QMXLC/IV/NBO/A/000/999/4038N07346W005 \r\nA) KJFK \r\nB) 2101081328 \r\nC) 2209301100 \r\n\r\nE) TWY TB BTN TERMINAL 8 RAMP AND TWY A CLSD"
    data, _ = notam.parse(report)
    assert isinstance(data, structs.NotamData)
    assert data.raw == report


@pytest.mark.parametrize(
    ("line", "fixed"),
    [
        ("01/113 NOTAMN \r\nQ) 1234", "01/113 NOTAMN \nQ) 1234"),
        # Keys given without a following space are repaired
        ("F0910/26 NOTAMN\nQ)RJJJ", "F0910/26 NOTAMN\nQ) RJJJ"),
        ("A)RJFF B)2609011400 C)2609272130", "A) RJFF B) 2609011400 C) 2609272130"),
        ("E)TWY A CLSD", "E) TWY A CLSD"),
        # Already spaced keys are left as they are
        ("E) TWY A CLSD", "E) TWY A CLSD"),
        # A key quoted mid-word or mid-token is not a key and is left alone
        ("E) RWY 09/27(B)CLSD", "E) RWY 09/27(B)CLSD"),
        ("E) SEE ITEMB)NOTE", "E) SEE ITEMB)NOTE"),
        # Known transposed Q-code subjects are swapped back
        ("Q) ZLA/QXMLC/IV/NBO/A/000/999", "Q) ZLA/QMXLC/IV/NBO/A/000/999"),
        ("Q) ZLA/QHMLX/IV/NBO/A/000/999", "Q) ZLA/QMHLX/IV/NBO/A/000/999"),
        ("Q)RJJJ/QLOXX/IV/NBO/A/000/999", "Q) RJJJ/QOLXX/IV/NBO/A/000/999"),
        # Other subjects, including unknown ones, are left alone
        ("Q) ZJX/QMLAT/IV/NBO/A/000/999", "Q) ZJX/QMLAT/IV/NBO/A/000/999"),
        ("Q) RJJJ/QMXLC/IV/NBO/A/000/999", "Q) RJJJ/QMXLC/IV/NBO/A/000/999"),
    ],
)
def test_sanitize(line: str, fixed: str) -> None:
    """Test report sanitization."""
    assert notam.sanitize(line) == fixed


@pytest.mark.parametrize(("wrong", "right"), TRANSPOSED_SUBJECT.items())
def test_transposed_subject_table(wrong: str, right: str) -> None:
    """Only unknown subjects are corrected, and only to known ones."""
    assert wrong not in SUBJECT
    assert right in SUBJECT
    assert wrong == right[::-1]


@pytest.mark.parametrize(
    ("report", "subject"),
    [
        (
            (
                "M0230/26 NOTAMN \nQ) ZLA/QXMLC/IV/NBO/A/000/999/3635N11540W005 \nA) KINS \n"
                "B) 2608101503 \nC) 2610092359 \nE) TWY G CLSD LGTD AND BARRICADED"
            ),
            structs.Code("MX", "Taxiway"),
        ),
        (
            (
                "M0230/26 NOTAMN \nQ) ZLA/QHMLX/IV/NBO/A/000/999/3747N11646W005 \nA) KTNX \n"
                "B) 2608191744 \nC) 2611132359 \nE) RWY 15 APPROACH END BAK 14 CAUTION POSSIBLE TAILHOOK SKIP"
            ),
            structs.Code("MH", "Runway arresting gear"),
        ),
        (
            (
                "M1139/26 NOTAMN \nQ) RJJJ/QLOXX/IV/NBO/A/000/999/3544N13920E005 \nA) RJTY \n"
                "B) 2609272022 \nC) 2610262021 \nE) NO STADIUM OR OBSTRUCTION LIGHTS ON THE AFSOC RAMP"
            ),
            structs.Code("OL", "Obstacle lights"),
        ),
    ],
)
def test_parse_transposed_subject(report: str, subject: structs.Code) -> None:
    """A transposed Q-code subject is corrected, and the raw report kept as given."""
    data, _ = notam.parse(report)
    assert data.qualifiers is not None
    assert data.qualifiers.subject == subject
    assert data.raw == report


@pytest.mark.parametrize(
    "report",
    [
        "!SUAC 09/481 ZFW AIRSPACE AR112H(E) ACT FL240-FL260 2609300245-2609300330",
        (
            "!ISM 09/037 ISM OBST EXCAVATOR (ASN UNKNOWN) 281750N0812627W (35FT N TWY A) 98FT "
            "(16FT AGL) FLAGGED, NOT LGTD DLY 1100-2100 2609281100-2610022100"
        ),
        (
            "!ZAK 09/001 ZAK NAV GPS (MAWTS1 GPS 26-01) (INCLUDING WAAS, GBAS,\nAND ADS-B) MAY NOT BE "
            "AVBL WI A 404NM RADIUS CENTERED AT\n325229N1145314W (BZA28016) FL400-UNL. 2609302100-2609302229"
        ),
    ],
)
def test_parse_domestic_ignores_item_keys(report: str) -> None:
    """A US domestic NOTAM is not split on text that looks like an ICAO item key."""
    data, _ = notam.parse(report)
    assert data.raw == report
    assert data.number is None
    assert data.qualifiers is None
    assert data.station is None
    assert data.body == ""


def test_parse_item_key_inside_body() -> None:
    """A letter in parentheses inside an item is not read as the next key."""
    report = (
        "A0001/26 NOTAMN\nQ) RJJJ/QRRCA/IV/BO/W/000/260/3500N13900E010\nA) RJJJ\n"
        "B) 2609300245 C) 2609300330\nE) AIRSPACE AR112H(F) ACT"
    )
    data, _ = notam.parse(report)
    assert data.body == "AIRSPACE AR112H(F) ACT"
    assert data.lower is None


def test_parse_flight_level_limits() -> None:
    """A G) line naming a flight level is parsed rather than dropped."""
    report = (
        "P4594/26 NOTAMN\nQ) UHMM/QRTCA/IV/BO/W/000/150/5629N16049E042\n"
        "A) UHMM B) 2608272300 C) 2608280800\nE) AIRSPACE CLSD WI AREA\nF) SFC  G) FL150"
    )
    data, _ = notam.parse(report)

    assert data.lower == structs.Altitude("SFC", 0, "surface", flight_level=False)
    assert data.upper == structs.Altitude("FL150", 150, "flight level one five zero", flight_level=True)
    # The Q) line carries the same limit rounded to hundreds of feet, but is not
    # treated as a flight level. See make_altitude.
    assert data.qualifiers is not None
    assert data.qualifiers.upper == structs.Altitude("150", 150, "one five zero")


def test_parse_keys_without_trailing_space() -> None:
    """Some sources omit the space after a key, ie "E)TWY CLSD".

    Taken from a live FNS-NDS message. The same report with spaced keys must parse
    identically.
    """
    report = (
        "F0910/26 NOTAMN\nQ)RJJJ/QMXLC/IV/M/A/000/999/3335N13027E005\n"
        "A)RJFF B)2609011400 C)2609272130\nD)01-14 19-23 26-27 1400/2130\n"
        "E)TWY A(FM K1 TO E8),ACFT STAND TXL K1 THRU K7,Y CLSD DUE TO MAINT"
    )
    data, _ = notam.parse(report)

    assert data.station == "RJFF"
    assert data.number == "F0910/26"
    assert data.schedule == "01-14 19-23 26-27 1400/2130"
    assert data.body == "TWY A(FM K1 TO E8),ACFT STAND TXL K1 THRU K7,Y CLSD DUE TO MAINT"
    assert data.qualifiers is not None
    assert data.qualifiers.fir == "RJJJ"
    assert data.qualifiers.subject == structs.Code("MX", "Taxiway")
    assert data.qualifiers.condition == structs.Code("LC", "Closed")
    assert data.start_time is not None
    assert data.start_time.dt == datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)
    assert data.end_time is not None
    assert data.end_time.dt == datetime(2026, 9, 27, 21, 30, tzinfo=timezone.utc)

    spaced_report = (
        "F0910/26 NOTAMN\nQ) RJJJ/QMXLC/IV/M/A/000/999/3335N13027E005\n"
        "A) RJFF B) 2609011400 C) 2609272130\nD) 01-14 19-23 26-27 1400/2130\n"
        "E) TWY A(FM K1 TO E8),ACFT STAND TXL K1 THRU K7,Y CLSD DUE TO MAINT"
    )
    spaced, _ = notam.parse(spaced_report)
    ignored = {"raw": None, "sanitized": None}
    assert asdict(spaced) | ignored == asdict(data) | ignored


@pytest.mark.parametrize(("ref", "icao", "unused"), get_data(__file__, "notam"))
def test_notam_e2e(ref: dict, icao: str, unused: Any) -> None:  # noqa: ARG001
    """Perform an end-to-end test of all NOTAM JSON files."""
    station = notam.Notams(icao)
    assert station.last_updated is None
    reports = [report["data"]["raw"] for report in ref["reports"]]
    assert station.parse(reports) is True
    assert isinstance(station.last_updated, datetime)
    for parsed, report in zip(station.data, ref["reports"], strict=True):
        assert asdict(parsed) == report["data"]
