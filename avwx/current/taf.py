"""
A TAF (Terminal Aerodrome Forecast) is a 24-hour weather forecast for the area
5 statute miles from the reporting station. They are update once every three or
six hours or when significant changes warrant an update, and the observations
are valid for six hours or until the next report is issued
"""

# stdlib
from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

# module
from avwx.current.base import Report, get_wx_codes
from avwx.parsing import core, speech, summary
from avwx.parsing.remarks import parse as parse_remarks
from avwx.parsing.sanitization.taf import clean_taf_list, clean_taf_string
from avwx.parsing.translate.taf import translate_taf
from avwx.static.core import FLIGHT_RULES
from avwx.static.taf import TAF_NEWLINE, TAF_NEWLINE_STARTSWITH, TAF_RMK
from avwx.station import uses_na_format, valid_station
from avwx.structs import (
    Cloud,
    Number,
    Sanitization,
    TafData,
    TafLineData,
    TafTrans,
    Timestamp,
    Units,
)

if TYPE_CHECKING:
    from datetime import date


class Taf(Report):
    """
    The Taf class offers an object-oriented approach to managing TAF data for a
    single station.

    ```python
    >>> from avwx import Taf
    >>> kjfk = Taf("KJFK")
    >>> kjfk.station.name
    'John F Kennedy International Airport'
    >>> kjfk.update()
    True
    >>> kjfk.last_updated
    datetime.datetime(2018, 3, 4, 23, 43, 26, 209644, tzinfo=datetime.timezone.utc)
    >>> kjfk.raw
    'KJFK 042030Z 0421/0524 33016G27KT P6SM BKN045 FM051600 36016G22KT P6SM BKN040 FM052100 35013KT P6SM SCT035'
    >>> len(kjfk.data.forecast)
    3
    >>> kjfk.data.forecast[0].flight_rules
    'VFR'
    >>> kjfk.translations.forecast[0].wind
    'NNW-330 at 16kt gusting to 27kt'
    >>> kjfk.speech
    'Starting on March 4th - From 21 to 16 zulu, Winds three three zero at 16kt gusting to 27kt. Visibility greater than six miles. Broken layer at 4500ft. From 16 to 21 zulu, Winds three six zero at 16kt gusting to 22kt. Visibility greater than six miles. Broken layer at 4000ft. From 21 to midnight zulu, Winds three five zero at 13kt. Visibility greater than six miles. Scattered clouds at 3500ft'
    ```

    The `parse` and `from_report` methods can parse a report string if you want
    to override the normal fetching process.

    ```python
    >>> from avwx import Taf
    >>> report = "TAF ZYHB 082300Z 0823/0911 VRB03KT 9999 SCT018 BKN120 TX14/0907Z TN04/0921Z FM090100 09015KT 9999 -SHRA WS020/13045KT SCT018 BKN120 BECMG 0904/0906 34008KT PROB30 TEMPO 0906/0911 7000 -RA SCT020 650104 530804 RMK FCST BASED ON AUTO OBS. NXT FCST BY 090600Z"
    >>> zyhb = Taf.from_report(report)
    True
    >>> zyhb.station.city
    'Hulan'
    >>> zyhb.data.remarks
    'RMK FCST BASED ON AUTO OBS. NXT FCST BY 090600Z'
    >>> zyhb.summary[-1]
    'Vis 7km, Light Rain, Scattered clouds at 2000ft, Frequent moderate turbulence in clear air from 8000ft to 12000ft, Moderate icing in clouds from 1000ft to 5000ft'
    ```
    """

    data: TafData | None = None
    translations: TafTrans | None = None  # type: ignore

    async def _post_update(self) -> None:
        if self.code is None or self.raw is None:
            return
        self.data, self.units, self.sanitization = parse(self.code, self.raw, self.issued)
        if self.data is None or self.units is None:
            return
        self.translations = translate_taf(self.data, self.units)

    def _post_parse(self) -> None:
        if self.code is None or self.raw is None:
            return
        self.data, self.units, self.sanitization = parse(self.code, self.raw, self.issued)
        if self.data is None or self.units is None:
            return
        self.translations = translate_taf(self.data, self.units)

    @property
    def summary(self) -> list[str]:
        """Condensed summary for each forecast created from translations."""
        if not self.translations:
            self.update()
        if self.translations is None or self.translations.forecast is None:
            return []
        return [summary.taf(trans) for trans in self.translations.forecast]

    @property
    def speech(self) -> str | None:
        """Report summary designed to be read by a text-to-speech program."""
        if not self.data:
            self.update()
        if self.data is None or self.units is None:
            return None
        return speech.taf(self.data, self.units)


LINE_FIXES = {
    "TEMP0": "TEMPO",
    "TEMP O": "TEMPO",
    "TMPO": "TEMPO",
    "TE MPO": "TEMPO",
    "TEMP ": "TEMPO ",
    "T EMPO": "TEMPO",
    " EMPO": " TEMPO",
    "TEMO": "TEMPO",
    "BECM G": "BECMG",
    "BEMCG": "BECMG",
    "BE CMG": "BECMG",
    "B ECMG": "BECMG",
    " BEC ": " BECMG ",
    "BCEMG": "BECMG",
    "BEMG": "BECMG",
}


def sanitize_line(txt: str, sans: Sanitization) -> str:
    """Fix common mistakes with 'new line' signifiers so that they can be recognized."""
    for key, fix in LINE_FIXES.items():
        if key in txt:
            txt = txt.replace(key, fix)
            sans.log(key, fix)
    # Fix when space is missing following new line signifiers
    for item in ["BECMG", "TEMPO"]:
        if item in txt and f"{item} " not in txt:
            index = txt.find(item) + len(item)
            txt = f"{txt[:index]} {txt[index:]}"
            sans.extra_spaces_needed = True
    return txt


def get_taf_remarks(txt: str) -> tuple[str, str]:
    """Return report and remarks separated if found."""
    remarks_start = core.find_first_in_list(txt, TAF_RMK)
    if remarks_start == -1:
        return txt, ""
    remarks = txt[remarks_start:]
    txt = txt[:remarks_start].strip()
    return txt, remarks


def get_alt_ice_turb(
    data: list[str],
) -> tuple[list[str], Number | None, list[str], list[str]]:
    """Return the report list and removed: Altimeter string, Icing list, Turbulence list."""
    altimeter_number = None
    icing, turbulence = [], []
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item.startswith("QNH") and item[3:7].isdigit():
            altimeter = data.pop(i)[3:7]
            if altimeter[0] in ("2", "3"):
                altimeter = f"{altimeter[:2]}.{altimeter[2:]}"
            altimeter_number = core.make_number(altimeter, literal=True)
        elif item.isdigit():
            if item[0] == "6":
                icing.append(data.pop(i))
            elif item[0] == "5":
                turbulence.append(data.pop(i))
    return data, altimeter_number, icing, turbulence


def is_normal_time(item: str) -> bool:
    """Return if the item looks like a valid TAF (1200/1400) time range."""
    return len(item) == 9 and item[4] == "/" and item[:4].isdigit() and item[5:].isdigit()


def starts_new_line(item: str) -> bool:
    """Returns True if the given element should start a new report line"""
    if item in TAF_NEWLINE:
        return True
    return any(item.startswith(start) for start in TAF_NEWLINE_STARTSWITH)


def split_taf(txt: str) -> list[str]:
    """Split a TAF report into each distinct time period."""
    lines = []
    split = txt.split()
    last_index = 0
    e_splits = enumerate(split)
    next(e_splits)
    for i, item in e_splits:
        if (starts_new_line(item) and not split[i - 1].startswith("PROB")) or (
            is_normal_time(item) and not starts_new_line(split[i - 1])
        ):
            lines.append(" ".join(split[last_index:i]))
            last_index = i
    lines.append(" ".join(split[last_index:]))
    return lines


# TAF line report type and start/end times
def get_type_and_times(
    data: list[str],
) -> tuple[list[str], str, str | None, str | None, str | None]:
    """Extract the report type string, start time string, and end time string."""
    report_type, start_time, end_time, transition = "FROM", None, None, None
    # TEMPO, BECMG, INTER
    if data and data[0] in TAF_NEWLINE or len(data[0]) == 6 and data[0].startswith("PROB"):
        report_type = data.pop(0)
    if data:
        item, length = data[0], len(data[0])
        # 1200/1306
        if is_normal_time(item):
            start_time, end_time = data.pop(0).split("/")

        # 1200 1306
        elif len(data) == 8 and length == 4 and len(data[1]) == 4 and item.isdigit() and data[1].isdigit():
            start_time = data.pop(0)
            end_time = data.pop(0)

        # 120000
        elif length == 6 and item.isdigit() and item[-2:] == "00":
            start_time = data.pop(0)[:4]
        # FM120000
        elif length > 7 and item.startswith("FM"):
            report_type = "FROM"
            if "/" in item and item[2:].split("/")[0].isdigit() and item[2:].split("/")[1].isdigit():
                start_time, end_time = data.pop(0)[2:].split("/")
            elif item[2:8].isdigit():
                start_time = data.pop(0)[2:6]
            # TL120600
            if data and length > 7 and data[0].startswith("TL") and data[0][2:8].isdigit():
                end_time = data.pop(0)[2:6]
        elif report_type == "BECMG" and length == 5:
            # 1200/
            if item[-1] == "/" and item[:4].isdigit():
                start_time = data.pop(0)[:4]
            # /1200
            elif item[0] == "/" and item[1:].isdigit():
                end_time = data.pop(0)[1:]
    if report_type == "BECMG":
        transition, start_time, end_time = start_time, end_time, None
    return data, report_type, start_time, end_time, transition


def _is_tempo_or_prob(line: TafLineData) -> bool:
    """Return True if report type is TEMPO or non-null probability."""
    return line.type == "TEMPO" or line.probability is not None


def _get_next_time(lines: list[TafLineData], target: str) -> Timestamp | None:
    """Returns the next normal time target value or empty"""
    for line in lines:
        if _is_tempo_or_prob(line):
            continue
        time = line.transition_start or getattr(line, target) if target == "start_time" else getattr(line, target)
        if time:
            return time  # type: ignore
    return None


def find_missing_taf_times(
    lines: list[TafLineData], start: Timestamp | None, end: Timestamp | None
) -> list[TafLineData]:
    """Fix any missing time issues except for error/empty lines."""
    if not lines:
        return lines
    # Assign start time
    lines[0].start_time = start
    # Fix other times
    last_fm_line = 0
    for i, line in enumerate(lines):
        if _is_tempo_or_prob(line):
            continue
        last_fm_line = i
        # Search remaining lines to fill empty end or previous for empty start
        for target, other, direc in (("start", "end", -1), ("end", "start", 1)):
            target += "_time"  # noqa: PLW2901
            if not getattr(line, target):
                setattr(line, target, _get_next_time(lines[i::direc][1:], f"{other}_time"))
    # Special case for final forcast
    if last_fm_line:
        lines[last_fm_line].end_time = end
    # Reset original end time if still empty
    if lines and not lines[0].end_time:
        lines[0].end_time = end
    return lines


def get_wind_shear(data: list[str]) -> tuple[list[str], str | None]:
    """Return the report list and the remove wind shear."""
    shear = None
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item.startswith("WS") and item[5] == "/":
            shear = data.pop(i).replace("KT", "")
    return data, shear


def get_temp_min_and_max(
    data: list[str],
) -> tuple[list[str], str | None, str | None]:
    """Pull out Max temp at time and Min temp at time items from wx list."""
    temp_max, temp_min = "", ""
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item[0] == "T" and "/" in item:
            # TX12/1316Z
            if item[1] == "X":
                temp_max = data.pop(i)
            # TNM03/1404Z
            elif item[1] == "N":
                temp_min = data.pop(i)
            # TM03/1404Z T12/1316Z -> Will fix TN/TX
            elif item[1] == "M" or item[1].isdigit():
                if temp_min:
                    if int(temp_min[2 : temp_min.find("/")].replace("M", "-")) > int(
                        item[1 : item.find("/")].replace("M", "-")
                    ):
                        temp_max, temp_min = f"TX{temp_min[2:]}", f"TN{item[1:]}"
                    else:
                        temp_max = f"TX{item[1:]}"
                else:
                    temp_min = f"TN{item[1:]}"
                data.pop(i)
    return data, temp_max or None, temp_min or None


def get_oceania_temp_and_alt(data: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Get Temperature and Altimeter lists for Oceania TAFs."""
    tlist: list[str] = []
    qlist: list[str] = []
    if "T" in data:
        data, tlist = core.get_digit_list(data, data.index("T"))
    if "Q" in data:
        data, qlist = core.get_digit_list(data, data.index("Q"))
    return data, tlist, qlist


def get_taf_flight_rules(lines: list[TafLineData]) -> list[TafLineData]:
    """Get flight rules by looking for missing data in prior reports."""
    for i, line in enumerate(lines):
        temp_vis, temp_cloud, is_clear = line.visibility, line.clouds, False
        for report in reversed(lines[: i + 1]):
            if not _is_tempo_or_prob(report):
                if not temp_vis:
                    temp_vis = report.visibility
                # SKC or CLR should force no clouds instead of looking back
                if "SKC" in report.other or "CLR" in report.other or temp_vis and temp_vis.repr == "CAVOK":
                    is_clear = True
                elif temp_cloud == []:
                    temp_cloud = report.clouds
                if temp_vis and temp_cloud != []:
                    break
        if is_clear:
            temp_cloud = []
        line.flight_rules = FLIGHT_RULES[core.get_flight_rules(temp_vis, core.get_ceiling(temp_cloud))]
    return lines


def fix_report_header(report: str) -> str:
    """Correct the header order for key elements."""
    split_report = report.split()

    # Limit scope to only the first few elements. Remarks may include similar tokens
    header_length = min(len(split_report), 6)
    headers = split_report[:header_length]

    fixed_headers = []
    for target in ("TAF", "AMD", "COR"):
        with suppress(ValueError):
            headers.remove(target)
            fixed_headers.append(target)

    return " ".join(fixed_headers + headers + split_report[header_length:])


def _is_possible_start_end_time_slash(item: str) -> bool:
    """Return True if item is a possible period start or end with missing element."""
    return len(item) == 5 and (
        # 1200/
        (item[-1] == "/" and item[:4].isdigit())
        or
        # /1200
        (item[0] == "/" and item[1:].isdigit())
    )


def parse(
    station: str, report: str, issued: date | None = None
) -> tuple[TafData | None, Units | None, Sanitization | None]:
    """Return TafData and Units dataclasses with parsed data and their associated units."""
    if not report:
        return None, None, None
    valid_station(station)
    report = fix_report_header(report)
    while len(report) > 3 and report[:4] in ("TAF ", "AMD ", "COR "):
        report = report[4:]
    start_time: Timestamp | None = None
    end_time: Timestamp | None = None
    sans = Sanitization()
    sanitized = clean_taf_string(report, sans)
    _, new_station, time = core.get_station_and_time(sanitized[:20].split())
    if new_station is not None:
        station = new_station
    sanitized = sanitized.replace(station, "")
    if time:
        sanitized = sanitized.replace(time, "").strip()
    units = Units.north_american() if uses_na_format(station) else Units.international()
    # Find and remove remarks
    sanitized, remarks = get_taf_remarks(sanitized)
    # Split and parse each line
    lines = split_taf(sanitized)
    parsed_lines = parse_lines(lines, units, sans, issued)
    # Perform additional info extract and corrections
    max_temp: str | None = None
    min_temp: str | None = None
    if parsed_lines:
        (
            parsed_lines[-1].other,
            max_temp,
            min_temp,
        ) = get_temp_min_and_max(parsed_lines[-1].other)
        if not (max_temp or min_temp):
            (
                parsed_lines[0].other,
                max_temp,
                min_temp,
            ) = get_temp_min_and_max(parsed_lines[0].other)
        # Set start and end times based on the first line
        start_time, end_time = parsed_lines[0].start_time, parsed_lines[0].end_time
        parsed_lines[0].end_time = None
        parsed_lines = find_missing_taf_times(parsed_lines, start_time, end_time)
        parsed_lines = get_taf_flight_rules(parsed_lines)
    # Extract Oceania-specific data
    alts: list[str] | None = None
    temps: list[str] | None = None
    if station[0] == "A":
        (
            parsed_lines[-1].other,
            alts,
            temps,
        ) = get_oceania_temp_and_alt(parsed_lines[-1].other)
    # Convert wx codes
    for line in parsed_lines:
        line.other, line.wx_codes = get_wx_codes(line.other)
    sanitized = " ".join(i for i in (station, time, sanitized) if i)
    struct = TafData(
        raw=report,
        sanitized=sanitized,
        station=station,
        time=core.make_timestamp(time, target_date=issued),
        remarks=remarks,
        remarks_info=parse_remarks(remarks),
        forecast=parsed_lines,
        start_time=start_time,
        end_time=end_time,
        max_temp=max_temp,
        min_temp=min_temp,
        alts=alts,
        temps=temps,
    )
    return struct, units, sans


def parse_lines(lines: list[str], units: Units, sans: Sanitization, issued: date | None = None) -> list[TafLineData]:
    """Return a list of parsed line dictionaries."""
    parsed_lines: list[TafLineData] = []
    prob = ""
    while lines:
        raw_line = lines[0].strip()
        line = sanitize_line(raw_line, sans)
        # Remove prob from the beginning of a line
        if line.startswith("PROB"):
            # Add standalone prob to next line
            if len(line) == 6:
                prob = line
                line = ""
            # Add to current line
            elif len(line) > 6:
                prob = line[:6]
                line = line[6:].strip()
        if line:
            parsed_line = parse_line(line, units, sans, issued)
            parsed_line.probability = None if " " in prob else core.make_number(prob[4:])
            parsed_line.raw = raw_line
            if prob:
                parsed_line.sanitized = f"{prob} {parsed_line.sanitized}"
            prob = ""
            parsed_lines.append(parsed_line)
        lines.pop(0)
    return parsed_lines


def parse_line(line: str, units: Units, sans: Sanitization, issued: date | None = None) -> TafLineData:
    """Parser for the International TAF forcast variant."""
    data: list[str] = core.dedupe(line.split())
    # Grab original time piece under certain conditions to preserve a useful slash
    old_time = data[1] if len(data) > 1 and _is_possible_start_end_time_slash(data[1]) else None
    data = clean_taf_list(data, sans)
    if old_time and len(data) > 1 and data[1] == old_time.strip("/"):
        data[1] = old_time
    sanitized = " ".join(data)
    data, report_type, start_time, end_time, transition = get_type_and_times(data)
    data, wind_shear = get_wind_shear(data)
    (
        data,
        wind_direction,
        wind_speed,
        wind_gust,
        wind_variable_direction,
    ) = core.get_wind(data, units)
    if "CAVOK" in data:
        visibility = core.make_number("CAVOK")
        clouds: list[Cloud] = []
        data.pop(data.index("CAVOK"))
    else:
        data, visibility = core.get_visibility(data, units)
        data, clouds = core.get_clouds(data)
    other, altimeter, icing, turbulence = get_alt_ice_turb(data)
    return TafLineData(
        altimeter=altimeter,
        clouds=clouds,
        flight_rules="",
        other=other,
        visibility=visibility,
        wind_direction=wind_direction,
        wind_gust=wind_gust,
        wind_speed=wind_speed,
        wx_codes=[],
        end_time=core.make_timestamp(end_time, target_date=issued),
        icing=icing,
        probability=None,
        raw=line,
        sanitized=sanitized,
        start_time=core.make_timestamp(start_time, target_date=issued),
        transition_start=core.make_timestamp(transition, target_date=issued),
        turbulence=turbulence,
        type=report_type,
        wind_shear=wind_shear,
        wind_variable_direction=wind_variable_direction,
    )
