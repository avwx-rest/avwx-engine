"""
Contains TAF-specific functions for report parsing
"""

# module
from avwx.current.base import Report
from avwx.parsing import core, speech, summary, translate
from avwx.static import IN_UNITS, NA_UNITS
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
    report = core.sanitize_report_string(report)
    _, station, time = core.get_station_and_time(report[:20].split())
    retwx["station"] = station
    retwx["time"] = core.make_timestamp(time)
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
    report, retwx["remarks"] = core.get_taf_remarks(report)
    # Split and parse each line
    lines = core.split_taf(report)
    parsed_lines = parse_lines(lines, units, use_na)
    # Perform additional info extract and corrections
    if parsed_lines:
        (
            parsed_lines[-1]["other"],
            retwx["max_temp"],
            retwx["min_temp"],
        ) = core.get_temp_min_and_max(parsed_lines[-1]["other"])
        if not (retwx["max_temp"] or retwx["min_temp"]):
            (
                parsed_lines[0]["other"],
                retwx["max_temp"],
                retwx["min_temp"],
            ) = core.get_temp_min_and_max(parsed_lines[0]["other"])
        # Set start and end times based on the first line
        start, end = parsed_lines[0]["start_time"], parsed_lines[0]["end_time"]
        parsed_lines[0]["end_time"] = None
        retwx["start_time"], retwx["end_time"] = start, end
        parsed_lines = core.find_missing_taf_times(parsed_lines, start, end)
        parsed_lines = core.get_taf_flight_rules(parsed_lines)
    # Extract Oceania-specific data
    if retwx["station"][0] == "A":
        (
            parsed_lines[-1]["other"],
            retwx["alts"],
            retwx["temps"],
        ) = core.get_oceania_temp_and_alt(parsed_lines[-1]["other"])
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
        line = core.sanitize_line(raw_line)
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
                parsed_line[key] = core.make_timestamp(parsed_line[key])
            parsed_line["probability"] = core.make_number(prob[4:])
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
    wxdata = core.dedupe(line.split())
    wxdata = core.sanitize_report_list(wxdata)
    retwx = {"sanitized": " ".join(wxdata)}
    (
        wxdata,
        retwx["type"],
        retwx["start_time"],
        retwx["end_time"],
    ) = core.get_type_and_times(wxdata)
    wxdata, retwx["wind_shear"] = core.get_wind_shear(wxdata)
    (
        wxdata,
        retwx["wind_direction"],
        retwx["wind_speed"],
        retwx["wind_gust"],
        _,
    ) = core.get_wind(wxdata, units)
    wxdata, retwx["visibility"] = core.get_visibility(wxdata, units)
    wxdata, retwx["clouds"] = core.get_clouds(wxdata)
    (
        retwx["other"],
        retwx["altimeter"],
        retwx["icing"],
        retwx["turbulence"],
    ) = core.get_taf_alt_ice_turb(wxdata)
    return retwx


def parse_in_line(line: str, units: Units) -> {str: str}:
    """
    Parser for the International TAF forcast variant
    """
    wxdata = core.dedupe(line.split())
    wxdata = core.sanitize_report_list(wxdata)
    retwx = {"sanitized": " ".join(wxdata)}
    (
        wxdata,
        retwx["type"],
        retwx["start_time"],
        retwx["end_time"],
    ) = core.get_type_and_times(wxdata)
    wxdata, retwx["wind_shear"] = core.get_wind_shear(wxdata)
    (
        wxdata,
        retwx["wind_direction"],
        retwx["wind_speed"],
        retwx["wind_gust"],
        _,
    ) = core.get_wind(wxdata, units)
    if "CAVOK" in wxdata:
        retwx["visibility"] = core.make_number("CAVOK")
        retwx["clouds"] = []
        wxdata.pop(wxdata.index("CAVOK"))
    else:
        wxdata, retwx["visibility"] = core.get_visibility(wxdata, units)
        wxdata, retwx["clouds"] = core.get_clouds(wxdata)
    (
        retwx["other"],
        retwx["altimeter"],
        retwx["icing"],
        retwx["turbulence"],
    ) = core.get_taf_alt_ice_turb(wxdata)
    return retwx


class Taf(Report):
    """
    Class to handle TAF report data
    """

    def _post_update(self):
        self.data, self.units = parse(self.station, self.raw)
        self.translations = translate.taf(self.data, self.units)

    @property
    def summary(self) -> [str]:
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