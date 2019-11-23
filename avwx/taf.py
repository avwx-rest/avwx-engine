"""
Contains TAF-specific functions for report parsing
"""

# stdlib
from copy import copy

# module
from avwx import _core, service
from avwx.static import IN_UNITS, NA_UNITS, TAF_NEWLINE, TAF_RMK
from avwx.station import uses_na_format, valid_station
from avwx.structs import TafData, TafLineData, Units


def parse(station: str, report: str) -> (TafData, Units):
    """
    Returns TafData and Units dataclasses with parsed data and their associated units
    """
    if not report:
        return None, None
    valid_station(station)
    while len(report) > 3 and report[:4] in ("TAF ", "AMD ", "COR "):
        report = report[4:]
    retwx = {"end_time": None, "raw": report, "remarks": None, "start_time": None}
    report = _core.sanitize_report_string(report)
    _, station, time = _core.get_station_and_time(report[:20].split())
    retwx["station"] = station
    retwx["time"] = _core.make_timestamp(time)
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
    report, retwx["remarks"] = _core.get_taf_remarks(report)
    # Split and parse each line
    lines = _core.split_taf(report)
    parsed_lines = parse_lines(lines, units, use_na)
    # Perform additional info extract and corrections
    if parsed_lines:
        (
            parsed_lines[-1]["other"],
            retwx["max_temp"],
            retwx["min_temp"],
        ) = _core.get_temp_min_and_max(parsed_lines[-1]["other"])
        if not (retwx["max_temp"] or retwx["min_temp"]):
            (
                parsed_lines[0]["other"],
                retwx["max_temp"],
                retwx["min_temp"],
            ) = _core.get_temp_min_and_max(parsed_lines[0]["other"])
        # Set start and end times based on the first line
        start, end = parsed_lines[0]["start_time"], parsed_lines[0]["end_time"]
        parsed_lines[0]["end_time"] = None
        retwx["start_time"], retwx["end_time"] = start, end
        parsed_lines = _core.find_missing_taf_times(parsed_lines, start, end)
        parsed_lines = _core.get_taf_flight_rules(parsed_lines)
    # Extract Oceania-specific data
    if retwx["station"][0] == "A":
        (
            parsed_lines[-1]["other"],
            retwx["alts"],
            retwx["temps"],
        ) = _core.get_oceania_temp_and_alt(parsed_lines[-1]["other"])
    # Convert to dataclass
    retwx["forecast"] = [TafLineData(**line) for line in parsed_lines]
    return TafData(**retwx), units


def parse_lines(lines: [str], units: Units, use_na: bool = True) -> [dict]:
    """
    Returns a list of parsed line dictionaries
    """
    parsed_lines = []
    prob = ""
    while lines:
        raw_line = lines[0].strip()
        line = _core.sanitize_line(raw_line)
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
            for key in ("start_time", "end_time"):
                parsed_line[key] = _core.make_timestamp(parsed_line[key])
            parsed_line["probability"] = _core.make_number(prob[4:])
            parsed_line["raw"] = raw_line
            if prob:
                parsed_line["sanitized"] = prob + " " + parsed_line["sanitized"]
            prob = ""
            parsed_lines.append(parsed_line)
        lines.pop(0)
    return parsed_lines


def parse_na_line(line: str, units: Units) -> {str: str}:
    """
    Parser for the North American TAF forcast variant
    """
    wxdata = _core.dedupe(line.split())
    wxdata = _core.sanitize_report_list(wxdata)
    retwx = {"sanitized": " ".join(wxdata)}
    (
        wxdata,
        retwx["type"],
        retwx["start_time"],
        retwx["end_time"],
    ) = _core.get_type_and_times(wxdata)
    wxdata, retwx["wind_shear"] = _core.get_wind_shear(wxdata)
    (
        wxdata,
        retwx["wind_direction"],
        retwx["wind_speed"],
        retwx["wind_gust"],
        _,
    ) = _core.get_wind(wxdata, units)
    wxdata, retwx["visibility"] = _core.get_visibility(wxdata, units)
    wxdata, retwx["clouds"] = _core.get_clouds(wxdata)
    (
        retwx["other"],
        retwx["altimeter"],
        retwx["icing"],
        retwx["turbulence"],
    ) = _core.get_taf_alt_ice_turb(wxdata)
    return retwx


def parse_in_line(line: str, units: Units) -> {str: str}:
    """
    Parser for the International TAF forcast variant
    """
    wxdata = _core.dedupe(line.split())
    wxdata = _core.sanitize_report_list(wxdata)
    retwx = {"sanitized": " ".join(wxdata)}
    (
        wxdata,
        retwx["type"],
        retwx["start_time"],
        retwx["end_time"],
    ) = _core.get_type_and_times(wxdata)
    wxdata, retwx["wind_shear"] = _core.get_wind_shear(wxdata)
    (
        wxdata,
        retwx["wind_direction"],
        retwx["wind_speed"],
        retwx["wind_gust"],
        _,
    ) = _core.get_wind(wxdata, units)
    if "CAVOK" in wxdata:
        retwx["visibility"] = _core.make_number("CAVOK")
        retwx["clouds"] = []
        wxdata.pop(wxdata.index("CAVOK"))
    else:
        wxdata, retwx["visibility"] = _core.get_visibility(wxdata, units)
        wxdata, retwx["clouds"] = _core.get_clouds(wxdata)
    (
        retwx["other"],
        retwx["altimeter"],
        retwx["icing"],
        retwx["turbulence"],
    ) = _core.get_taf_alt_ice_turb(wxdata)
    return retwx
