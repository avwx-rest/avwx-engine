"""
Contains TAF-specific functions for report parsing
"""

# stdlib
from datetime import date
from typing import List, Tuple, Optional

# module
from avwx.current.base import Report, get_wx_codes
from avwx.parsing import core, sanitization, speech, summary
from avwx.parsing.remarks import parse as parse_remarks
from avwx.parsing.translate.taf import translate_taf
from avwx.static.core import FLIGHT_RULES, IN_UNITS, NA_UNITS
from avwx.static.taf import TAF_RMK, TAF_NEWLINE, TAF_NEWLINE_STARTSWITH
from avwx.station import uses_na_format, valid_station
from avwx.structs import Cloud, Number, TafData, TafLineData, TafTrans, Timestamp, Units


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


def sanitize_line(txt: str) -> str:
    """Fixes common mistakes with 'new line' signifiers so that they can be recognized"""
    for key, fix in LINE_FIXES.items():
        txt = txt.replace(key, fix)
    # Fix when space is missing following new line signifiers
    for item in ["BECMG", "TEMPO"]:
        if item in txt and item + " " not in txt:
            index = txt.find(item) + len(item)
            txt = txt[:index] + " " + txt[index:]
    return txt


def get_taf_remarks(txt: str) -> Tuple[str, str]:
    """Returns report and remarks separated if found"""
    remarks_start = core.find_first_in_list(txt, TAF_RMK)
    if remarks_start == -1:
        return txt, ""
    remarks = txt[remarks_start:]
    txt = txt[:remarks_start].strip()
    return txt, remarks


def get_alt_ice_turb(
    data: List[str],
) -> Tuple[List[str], Optional[Number], List[str], List[str]]:
    """Returns the report list and removed: Altimeter string, Icing list, Turbulence list"""
    altimeter_number = None
    icing, turbulence = [], []
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item.startswith("QNH") and item[3:7].isdigit():
            altimeter = data.pop(i)[3:7]
            if altimeter[0] in ("2", "3"):
                altimeter = altimeter[:2] + "." + altimeter[2:]
            altimeter_number = core.make_number(altimeter, literal=True)
        elif item.isdigit():
            if item[0] == "6":
                icing.append(data.pop(i))
            elif item[0] == "5":
                turbulence.append(data.pop(i))
    return data, altimeter_number, icing, turbulence


def starts_new_line(item: str) -> bool:
    """Returns True if the given element should start a new report line"""
    if item in TAF_NEWLINE:
        return True
    for start in TAF_NEWLINE_STARTSWITH:
        if item.startswith(start):
            return True
    return False


def split_taf(txt: str) -> List[str]:
    """Splits a TAF report into each distinct time period"""
    lines = []
    split = txt.split()
    last_index = 0
    for i, item in enumerate(split):
        if starts_new_line(item) and i != 0 and not split[i - 1].startswith("PROB"):
            lines.append(" ".join(split[last_index:i]))
            last_index = i
    lines.append(" ".join(split[last_index:]))
    return lines


# TAF line report type and start/end times
def get_type_and_times(
    data: List[str],
) -> Tuple[List[str], str, Optional[str], Optional[str], Optional[str]]:
    """Returns the report list and removed:

    Report type string, start time string, end time string
    """
    report_type, start_time, end_time, transition = "FROM", None, None, None
    if data:
        # TEMPO, BECMG, INTER
        if data[0] in TAF_NEWLINE:
            report_type = data.pop(0)
        # PROB[30,40]
        elif len(data[0]) == 6 and data[0].startswith("PROB"):
            report_type = data.pop(0)
    if data:
        # 1200/1306
        if (
            len(data[0]) == 9
            and data[0][4] == "/"
            and data[0][:4].isdigit()
            and data[0][5:].isdigit()
        ):
            start_time, end_time = data.pop(0).split("/")
        # FM120000
        elif len(data[0]) > 7 and data[0].startswith("FM"):
            report_type = "FROM"
            if (
                "/" in data[0]
                and data[0][2:].split("/")[0].isdigit()
                and data[0][2:].split("/")[1].isdigit()
            ):
                start_time, end_time = data.pop(0)[2:].split("/")
            elif data[0][2:8].isdigit():
                start_time = data.pop(0)[2:6]
            # TL120600
            if (
                data
                and len(data[0]) > 7
                and data[0].startswith("TL")
                and data[0][2:8].isdigit()
            ):
                end_time = data.pop(0)[2:6]
    if report_type == "BECMG":
        transition, start_time, end_time = start_time, end_time, None
    return data, report_type, start_time, end_time, transition


def _is_tempo_or_prob(line: TafLineData) -> bool:
    """Returns True if report type is TEMPO or non-null probability"""
    return line.type == "TEMPO" or line.probability is not None


def _get_next_time(lines: List[TafLineData], target: str) -> Optional[Timestamp]:
    """Returns the next normal time target value or empty"""
    for line in lines:
        if _is_tempo_or_prob(line):
            continue
        if target == "start_time":
            time = line.transition_start or getattr(line, target)
        else:
            time = getattr(line, target)
        if time:
            return time
    return None


def find_missing_taf_times(
    lines: List[TafLineData], start: Optional[Timestamp], end: Optional[Timestamp]
) -> List[TafLineData]:
    """Fix any missing time issues (except for error/empty lines)"""
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
            target += "_time"
            if not getattr(line, target):
                setattr(
                    line, target, _get_next_time(lines[i::direc][1:], other + "_time")
                )
    # Special case for final forcast
    if last_fm_line:
        lines[last_fm_line].end_time = end
    # Reset original end time if still empty
    if lines and not lines[0].end_time:
        lines[0].end_time = end
    return lines


def get_wind_shear(data: List[str]) -> Tuple[List[str], Optional[str]]:
    """Returns the report list and the remove wind shear"""
    shear = None
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item.startswith("WS") and item[5] == "/":
            shear = data.pop(i).replace("KT", "")
    return data, shear


def get_temp_min_and_max(
    data: List[str],
) -> Tuple[List[str], Optional[str], Optional[str]]:
    """Pull out Max temp at time and Min temp at time items from wx list"""
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
                        temp_max = "TX" + temp_min[2:]
                        temp_min = "TN" + item[1:]
                    else:
                        temp_max = "TX" + item[1:]
                else:
                    temp_min = "TN" + item[1:]
                data.pop(i)
    return data, temp_max or None, temp_min or None


def get_oceania_temp_and_alt(data: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """Get Temperature and Altimeter lists for Oceania TAFs"""
    tlist: List[str] = []
    qlist: List[str] = []
    if "T" in data:
        data, tlist = core.get_digit_list(data, data.index("T"))
    if "Q" in data:
        data, qlist = core.get_digit_list(data, data.index("Q"))
    return data, tlist, qlist


def get_taf_flight_rules(lines: List[TafLineData]) -> List[TafLineData]:
    """Get flight rules by looking for missing data in prior reports"""
    for i, line in enumerate(lines):
        temp_vis, temp_cloud, is_clear = line.visibility, line.clouds, False
        for report in reversed(lines[: i + 1]):
            if not _is_tempo_or_prob(report):
                if not temp_vis:
                    temp_vis = report.visibility
                # SKC or CLR should force no clouds instead of looking back
                if "SKC" in report.other or "CLR" in report.other:
                    is_clear = True
                elif temp_vis and temp_vis.repr == "CAVOK":
                    is_clear = True
                elif temp_cloud == []:
                    temp_cloud = report.clouds
                if temp_vis and temp_cloud != []:
                    break
        if is_clear:
            temp_cloud = []
        line.flight_rules = FLIGHT_RULES[
            core.get_flight_rules(temp_vis, core.get_ceiling(temp_cloud))
        ]
    return lines


def parse(
    station: str, report: str, issued: date = None
) -> Tuple[Optional[TafData], Optional[Units]]:
    """Returns TafData and Units dataclasses with parsed data and their associated units"""
    # pylint: disable=too-many-locals
    if not report:
        return None, None
    valid_station(station)
    while len(report) > 3 and report[:4] in ("TAF ", "AMD ", "COR "):
        report = report[4:]
    start_time: Optional[Timestamp] = None
    end_time: Optional[Timestamp] = None
    sanitized = sanitization.sanitize_report_string(report)
    _, new_station, time = core.get_station_and_time(sanitized[:20].split())
    if new_station is not None:
        station = new_station
    sanitized = sanitized.replace(station, "")
    if time:
        sanitized = sanitized.replace(time, "").strip()
    if uses_na_format(station):
        units = Units(**NA_UNITS)
    else:
        units = Units(**IN_UNITS)
    # Find and remove remarks
    sanitized, remarks = get_taf_remarks(sanitized)
    # Split and parse each line
    lines = split_taf(sanitized)
    parsed_lines = parse_lines(lines, units, issued)
    # Perform additional info extract and corrections
    max_temp: Optional[str] = None
    min_temp: Optional[str] = None
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
    alts: Optional[List[str]] = None
    temps: Optional[List[str]] = None
    if station[0] == "A":
        (
            parsed_lines[-1].other,
            alts,
            temps,
        ) = get_oceania_temp_and_alt(parsed_lines[-1].other)
    # Convert wx codes
    for i, line in enumerate(parsed_lines):
        parsed_lines[i].other, parsed_lines[i].wx_codes = get_wx_codes(line.other)
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
    return struct, units


def parse_lines(
    lines: List[str], units: Units, issued: date = None
) -> List[TafLineData]:
    """Returns a list of parsed line dictionaries"""
    parsed_lines: List[TafLineData] = []
    prob = ""
    while lines:
        raw_line = lines[0].strip()
        line = sanitize_line(raw_line)
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
            parsed_line = parse_line(line, units, issued)
            parsed_line.probability = (
                None if " " in prob else core.make_number(prob[4:])
            )
            parsed_line.raw = raw_line
            if prob:
                parsed_line.sanitized = prob + " " + parsed_line.sanitized
            prob = ""
            parsed_lines.append(parsed_line)
        lines.pop(0)
    return parsed_lines


# def parse_na_line(line: str, units: Units) -> TafLineData:
#     """Parser for the North American TAF forcast variant"""
#     data = core.dedupe(line.split())
#     data = sanitization.sanitize_report_list(data, remove_clr_and_skc=False)
#     sanitized = " ".join(data)
#     data, report_type, start_time, end_time, transition = get_type_and_times(data)
#     data, wind_shear = get_wind_shear(data)
#     data, wind_direction, wind_speed, wind_gust, _ = core.get_wind(data, units)
#     data, visibility = core.get_visibility(data, units)
#     data, clouds = core.get_clouds(data)
#     other, altimeter, icing, turbulence = get_alt_ice_turb(data)
#     return TafLineData(
#         altimeter=altimeter,
#         clouds=clouds,
#         flight_rules="",
#         other=other,
#         visibility=visibility,
#         wind_direction=wind_direction,
#         wind_gust=wind_gust,
#         wind_speed=wind_speed,
#         wx_codes=[],
#         end_time=end_time,
#         icing=icing,
#         probability=None,
#         raw=line,
#         sanitized=sanitized,
#         start_time=start_time,
#         transition_start=transition,
#         turbulence=turbulence,
#         type=report_type,
#         wind_shear=wind_shear,
#     )


def parse_line(line: str, units: Units, issued: date = None) -> TafLineData:
    """Parser for the International TAF forcast variant"""
    # pylint: disable=too-many-locals
    data = core.dedupe(line.split())
    data = sanitization.sanitize_report_list(data, remove_clr_and_skc=False)
    sanitized = " ".join(data)
    data, report_type, start_time, end_time, transition = get_type_and_times(data)
    data, wind_shear = get_wind_shear(data)
    data, wind_direction, wind_speed, wind_gust, _ = core.get_wind(data, units)
    if "CAVOK" in data:
        visibility = core.make_number("CAVOK")
        clouds: List[Cloud] = []
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
    )


class Taf(Report):
    """Class to handle TAF report data"""

    data: Optional[TafData] = None
    translations: Optional[TafTrans] = None  # type: ignore

    async def _post_update(self):
        self.data, self.units = parse(self.icao, self.raw, self.issued)
        self.translations = translate_taf(self.data, self.units)

    def _post_parse(self):
        self.data, self.units = parse(self.icao, self.raw, self.issued)
        self.translations = translate_taf(self.data, self.units)

    @property
    def summary(self) -> List[str]:
        """Condensed summary for each forecast created from translations"""
        if not self.translations:
            self.update()
        if self.translations is None or self.translations.forecast is None:
            return []
        return [summary.taf(trans) for trans in self.translations.forecast]

    @property
    def speech(self) -> Optional[str]:
        """Report summary designed to be read by a text-to-speech program"""
        if not self.data:
            self.update()
        if self.data is None or self.units is None:
            return None
        return speech.taf(self.data, self.units)
