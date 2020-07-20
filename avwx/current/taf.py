"""
Contains TAF-specific functions for report parsing
"""

# stdlib
from datetime import date
from typing import Dict, List, Tuple

# module
from avwx.current.base import Report, get_wx_codes
from avwx.parsing import core, sanitization, speech, summary
from avwx.parsing.translate.taf import translate_taf
from avwx.static.core import FLIGHT_RULES, IN_UNITS, NA_UNITS
from avwx.static.taf import TAF_RMK, TAF_NEWLINE, TAF_NEWLINE_STARTSWITH
from avwx.station import uses_na_format, valid_station
from avwx.structs import TafData, TafLineData, Timestamp, Units


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
    """
    Fixes common mistakes with 'new line' signifiers so that they can be recognized
    """
    for key, fix in LINE_FIXES.items():
        txt = txt.replace(key, fix)
    # Fix when space is missing following new line signifiers
    for item in ["BECMG", "TEMPO"]:
        if item in txt and item + " " not in txt:
            index = txt.find(item) + len(item)
            txt = txt[:index] + " " + txt[index:]
    return txt


def get_taf_remarks(txt: str) -> Tuple[str, str]:
    """
    Returns report and remarks separated if found
    """
    remarks_start = core.find_first_in_list(txt, TAF_RMK)
    if remarks_start == -1:
        return txt, ""
    remarks = txt[remarks_start:]
    txt = txt[:remarks_start].strip()
    return txt, remarks


def get_alt_ice_turb(data: List[str]) -> Tuple[List[str], str, List[str], List[str]]:
    """
    Returns the report list and removed: Altimeter string, Icing list, Turbulence list
    """
    altimeter = ""
    icing, turbulence = [], []
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item.startswith("QNH") and item[3:7].isdigit():
            altimeter = data.pop(i)[3:7]
            if altimeter[0] in ("2", "3"):
                altimeter = altimeter[:2] + "." + altimeter[2:]
            altimeter = core.make_number(altimeter, literal=True)
        elif item.isdigit():
            if item[0] == "6":
                icing.append(data.pop(i))
            elif item[0] == "5":
                turbulence.append(data.pop(i))
    return data, altimeter, icing, turbulence


def starts_new_line(item: str) -> bool:
    """
    Returns True if the given element should start a new report line
    """
    if item in TAF_NEWLINE:
        return True
    for start in TAF_NEWLINE_STARTSWITH:
        if item.startswith(start):
            return True
    return False


def split_taf(txt: str) -> List[str]:
    """
    Splits a TAF report into each distinct time period
    """
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
def get_type_and_times(data: List[str]) -> Tuple[List[str], str, str, str]:
    """
    Returns the report list and removed:
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


def _is_tempo_or_prob(line: dict) -> bool:
    """
    Returns True if report type is TEMPO or non-null probability
    """
    return line.get("type") == "TEMPO" or line.get("probability") is not None


def _get_next_time(lines: List[dict], target: str) -> str:
    """
    Returns the next normal time target value or empty
    """
    for line in lines:
        if _is_tempo_or_prob(line):
            continue
        if target == "start_time":
            time = line["transition_start"] or line[target]
        else:
            time = line[target]
        if time:
            return time
    return ""


def find_missing_taf_times(
    lines: List[dict], start: Timestamp, end: Timestamp
) -> List[dict]:
    """
    Fix any missing time issues (except for error/empty lines)
    """
    if not lines:
        return lines
    # Assign start time
    lines[0]["start_time"] = start
    # Fix other times
    last_fm_line = 0
    for i, line in enumerate(lines):
        if _is_tempo_or_prob(line):
            continue
        last_fm_line = i
        # Search remaining lines to fill empty end or previous for empty start
        for target, other, direc in (("start", "end", -1), ("end", "start", 1)):
            target += "_time"
            if not line[target]:
                line[target] = _get_next_time(lines[i::direc][1:], other + "_time")
    # Special case for final forcast
    if last_fm_line:
        lines[last_fm_line]["end_time"] = end
    # Reset original end time if still empty
    if lines and not lines[0]["end_time"]:
        lines[0]["end_time"] = end
    return lines


def get_wind_shear(data: List[str]) -> Tuple[List[str], str]:
    """
    Returns the report list and the remove wind shear
    """
    shear = None
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item.startswith("WS") and item[5] == "/":
            shear = data.pop(i).replace("KT", "")
    return data, shear


def get_temp_min_and_max(data: List[str]) -> Tuple[List[str], str, str]:
    """
    Pull out Max temp at time and Min temp at time items from wx list
    """
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
    return data, temp_max, temp_min


def get_oceania_temp_and_alt(data: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Get Temperature and Altimeter lists for Oceania TAFs
    """
    tlist, qlist = [], []
    if "T" in data:
        data, tlist = core.get_digit_list(data, data.index("T"))
    if "Q" in data:
        data, qlist = core.get_digit_list(data, data.index("Q"))
    return data, tlist, qlist


def get_taf_flight_rules(lines: List[dict]) -> List[dict]:
    """
    Get flight rules by looking for missing data in prior reports
    """
    for i, line in enumerate(lines):
        temp_vis, temp_cloud = line["visibility"], line["clouds"]
        for report in reversed(lines[: i + 1]):
            if not _is_tempo_or_prob(report):
                if not temp_vis:
                    temp_vis = report["visibility"]
                # SKC or CLR should force no clouds instead of looking back
                if "SKC" in report["other"] or "CLR" in report["other"]:
                    temp_cloud = "temp-clear"
                elif temp_cloud == []:
                    temp_cloud = report["clouds"]
                if temp_vis and temp_cloud != []:
                    break
        if temp_cloud == "temp-clear":
            temp_cloud = []
        line["flight_rules"] = FLIGHT_RULES[
            core.get_flight_rules(temp_vis, core.get_ceiling(temp_cloud))
        ]
    return lines


def parse(station: str, report: str, issued: date = None) -> Tuple[TafData, Units]:
    """
    Returns TafData and Units dataclasses with parsed data and their associated units
    """
    if not report:
        return None, None
    valid_station(station)
    while len(report) > 3 and report[:4] in ("TAF ", "AMD ", "COR "):
        report = report[4:]
    ret = {"end_time": None, "raw": report, "remarks": None, "start_time": None}
    report = sanitization.sanitize_report_string(report)
    _, station, time = core.get_station_and_time(report[:20].split())
    ret["station"] = station
    ret["time"] = core.make_timestamp(time, target_date=issued)
    report = report.replace(station, "")
    if time:
        report = report.replace(time, "").strip()
    if uses_na_format(station):
        use_na = True
        units = Units(**NA_UNITS)
    else:
        use_na = False
        units = Units(**IN_UNITS)
    # Find and remove remarks
    report, ret["remarks"] = get_taf_remarks(report)
    # Split and parse each line
    lines = split_taf(report)
    parsed_lines = parse_lines(lines, units, use_na, issued)
    # Perform additional info extract and corrections
    if parsed_lines:
        (
            parsed_lines[-1]["other"],
            ret["max_temp"],
            ret["min_temp"],
        ) = get_temp_min_and_max(parsed_lines[-1]["other"])
        if not (ret["max_temp"] or ret["min_temp"]):
            (
                parsed_lines[0]["other"],
                ret["max_temp"],
                ret["min_temp"],
            ) = get_temp_min_and_max(parsed_lines[0]["other"])
        # Set start and end times based on the first line
        start, end = parsed_lines[0]["start_time"], parsed_lines[0]["end_time"]
        parsed_lines[0]["end_time"] = None
        ret["start_time"], ret["end_time"] = start, end
        parsed_lines = find_missing_taf_times(parsed_lines, start, end)
        parsed_lines = get_taf_flight_rules(parsed_lines)
    # Extract Oceania-specific data
    if ret["station"][0] == "A":
        (
            parsed_lines[-1]["other"],
            ret["alts"],
            ret["temps"],
        ) = get_oceania_temp_and_alt(parsed_lines[-1]["other"])
    # Convert wx codes
    for i, line in enumerate(parsed_lines):
        parsed_lines[i]["other"], parsed_lines[i]["wx_codes"] = get_wx_codes(
            line["other"]
        )
    # Convert to dataclass
    ret["forecast"] = [TafLineData(**line) for line in parsed_lines]
    return TafData(**ret), units


def parse_lines(
    lines: List[str], units: Units, use_na: bool = True, issued: date = None
) -> List[dict]:
    """
    Returns a list of parsed line dictionaries
    """
    parsed_lines = []
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
            parsed_line = (parse_na_line if use_na else parse_in_line)(line, units)
            for key in ("start_time", "end_time", "transition_start"):
                parsed_line[key] = core.make_timestamp(
                    parsed_line[key], target_date=issued
                )
            parsed_line["probability"] = core.make_number(prob[4:])
            parsed_line["raw"] = raw_line
            if prob:
                parsed_line["sanitized"] = prob + " " + parsed_line["sanitized"]
            prob = ""
            parsed_lines.append(parsed_line)
        lines.pop(0)
    return parsed_lines


def parse_na_line(line: str, units: Units) -> Dict[str, str]:
    """
    Parser for the North American TAF forcast variant
    """
    data = core.dedupe(line.split())
    data = sanitization.sanitize_report_list(data, remove_clr_and_skc=False)
    ret = {"sanitized": " ".join(data)}
    (
        data,
        ret["type"],
        ret["start_time"],
        ret["end_time"],
        ret["transition_start"],
    ) = get_type_and_times(data)
    data, ret["wind_shear"] = get_wind_shear(data)
    (
        data,
        ret["wind_direction"],
        ret["wind_speed"],
        ret["wind_gust"],
        _,
    ) = core.get_wind(data, units)
    data, ret["visibility"] = core.get_visibility(data, units)
    data, ret["clouds"] = core.get_clouds(data)
    (
        ret["other"],
        ret["altimeter"],
        ret["icing"],
        ret["turbulence"],
    ) = get_alt_ice_turb(data)
    return ret


def parse_in_line(line: str, units: Units) -> Dict[str, str]:
    """
    Parser for the International TAF forcast variant
    """
    data = core.dedupe(line.split())
    data = sanitization.sanitize_report_list(data, remove_clr_and_skc=False)
    ret = {"sanitized": " ".join(data)}
    (
        data,
        ret["type"],
        ret["start_time"],
        ret["end_time"],
        ret["transition_start"],
    ) = get_type_and_times(data)
    data, ret["wind_shear"] = get_wind_shear(data)
    (
        data,
        ret["wind_direction"],
        ret["wind_speed"],
        ret["wind_gust"],
        _,
    ) = core.get_wind(data, units)
    if "CAVOK" in data:
        ret["visibility"] = core.make_number("CAVOK")
        ret["clouds"] = []
        data.pop(data.index("CAVOK"))
    else:
        data, ret["visibility"] = core.get_visibility(data, units)
        data, ret["clouds"] = core.get_clouds(data)
    (
        ret["other"],
        ret["altimeter"],
        ret["icing"],
        ret["turbulence"],
    ) = get_alt_ice_turb(data)
    return ret


class Taf(Report):
    """
    Class to handle TAF report data
    """

    def _post_update(self):
        self.data, self.units = parse(self.icao, self.raw, self.issued)
        self.translations = translate_taf(self.data, self.units)

    @property
    def summary(self) -> List[str]:
        """
        Condensed summary for each forecast created from translations
        """
        if not self.translations:
            self.update()
        return [summary.taf(trans) for trans in self.translations.forecast]

    @property
    def speech(self) -> str:
        """
        Report summary designed to be read by a text-to-speech program
        """
        if not self.data:
            self.update()
        return speech.taf(self.data, self.units)
