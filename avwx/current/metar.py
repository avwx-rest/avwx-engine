"""
Contains METAR-specific functions for report parsing
"""

# stdlib
from datetime import date
from typing import List, Tuple

# module
from avwx.current.base import Report, get_wx_codes
from avwx.parsing import core, remarks, sanitization, speech, summary
from avwx.parsing.translate.metar import translate_metar
from avwx.static.core import FLIGHT_RULES, IN_UNITS, NA_UNITS
from avwx.static.metar import METAR_RMK
from avwx.station import uses_na_format, valid_station
from avwx.structs import MetarData, Number, Units


def get_remarks(txt: str) -> Tuple[List[str], str]:
    """
    Returns the report split into components and the remarks string

    Remarks can include items like RMK and on, NOSIG and on, and BECMG and on
    """
    txt = txt.replace("?", "").strip()
    # First look for Altimeter in txt
    alt_index = len(txt) + 1
    for item in [" A2", " A3", " Q1", " Q0", " Q9"]:
        index = txt.find(item)
        if len(txt) - 6 > index > -1 and txt[index + 2 : index + 6].isdigit():
            alt_index = index
    # Then look for earliest remarks 'signifier'
    sig_index = core.find_first_in_list(txt, METAR_RMK)
    if sig_index == -1:
        sig_index = len(txt) + 1
    if sig_index > alt_index > -1:
        return txt[: alt_index + 6].strip().split(), txt[alt_index + 7 :]
    if alt_index > sig_index > -1:
        return txt[:sig_index].strip().split(), txt[sig_index + 1 :]
    return txt.strip().split(), ""


def get_runway_visibility(data: List[str]) -> Tuple[List[str], List[str]]:
    """
    Returns the report list and the remove runway visibility list
    """
    runway_vis = []
    for i, item in reversed(list(enumerate(data))):
        if (
            len(item) > 4
            and item[0] == "R"
            and (item[3] == "/" or item[4] == "/")
            and item[1:3].isdigit()
        ):
            runway_vis.append(data.pop(i))
    runway_vis.sort()
    return data, runway_vis


def parse_altimeter(value: str) -> Number:
    """
    Parse an altimeter string into a Number
    """
    if not value or len(value) < 4:
        return None
    # QNH3003INS
    if len(value) >= 7 and value.endswith("INS"):
        return core.make_number(value[-7:-5] + "." + value[-5:-3], value, literal=True)
    number = value.replace(".", "")
    # Q1000/10
    if "/" in number:
        number = number.split("/")[0]
    if number.startswith("QNH"):
        number = "Q" + number[1:]
    if not (len(number) in (4, 5) and number[-4:].isdigit()):
        return None
    number = number.lstrip("AQ")
    if number[0] in ("2", "3"):
        number = number[:2] + "." + number[2:]
    elif number[0] not in ("0", "1"):
        return None
    return core.make_number(number, value, number, literal=True)


def get_altimeter(
    data: List[str], units: Units, version: str = "NA"
) -> Tuple[List[str], Number]:
    """
    Returns the report list and the removed altimeter item

    Version is 'NA' (North American / default) or 'IN' (International)
    """
    values = []
    for _ in range(2):
        if not data:
            break
        value = parse_altimeter(data[-1])
        if value is None:
            break
        values.append(value)
        data.pop(-1)
    if not values:
        return data, None
    values.sort(key=lambda x: x.value)
    altimeter = values[0 if version == "NA" else -1]
    units.altimeter = "inHg" if altimeter.value < 100 else "hPa"
    return data, altimeter


def get_temp_and_dew(data: str) -> Tuple[List[str], Number, Number]:
    """
    Returns the report list and removed temperature and dewpoint strings
    """
    for i, item in reversed(list(enumerate(data))):
        if "/" in item:
            # ///07
            if item[0] == "/":
                item = "/" + item.lstrip("/")
            # 07///
            elif item[-1] == "/":
                item = item.rstrip("/") + "/"
            tempdew = item.split("/")
            if len(tempdew) != 2:
                continue
            valid = True
            for j, temp in enumerate(tempdew):
                if temp in ["MM", "XX"]:
                    tempdew[j] = ""
                elif not core.is_possible_temp(temp):
                    valid = False
                    break
            if valid:
                data.pop(i)
                return (data, *[core.make_number(t) for t in tempdew])
    return data, None, None


def sanitize(report: str) -> Tuple[str, str, List[str]]:
    """
    Returns a sanitized report, remarks, and elements ready for parsing
    """
    clean = sanitization.sanitize_report_string(report)
    data, remark_str = get_remarks(clean)
    data = core.dedupe(data)
    data = sanitization.sanitize_report_list(data)
    clean = " ".join(data)
    if remark_str:
        clean += " " + remark_str
    return clean, remark_str, data


def parse(station: str, report: str, issued: date = None) -> Tuple[MetarData, Units]:
    """
    Returns MetarData and Units dataclasses with parsed data and their associated units
    """
    valid_station(station)
    if not report:
        return None, None
    parser = parse_na if uses_na_format(station[:2]) else parse_in
    return parser(report, issued)


def parse_na(report: str, issued: date = None) -> Tuple[MetarData, Units]:
    """
    Parser for the North American METAR variant
    """
    units = Units(**NA_UNITS)
    resp = {"raw": report}
    resp["sanitized"], resp["remarks"], data = sanitize(report)
    data, resp["station"], resp["time"] = core.get_station_and_time(data)
    data, resp["runway_visibility"] = get_runway_visibility(data)
    data, resp["clouds"] = core.get_clouds(data)
    (
        data,
        resp["wind_direction"],
        resp["wind_speed"],
        resp["wind_gust"],
        resp["wind_variable_direction"],
    ) = core.get_wind(data, units)
    data, resp["altimeter"] = get_altimeter(data, units, "NA")
    data, resp["visibility"] = core.get_visibility(data, units)
    data, resp["temperature"], resp["dewpoint"] = get_temp_and_dew(data)
    condition = core.get_flight_rules(
        resp["visibility"], core.get_ceiling(resp["clouds"])
    )
    resp["other"], resp["wx_codes"] = get_wx_codes(data)
    resp["flight_rules"] = FLIGHT_RULES[condition]
    resp["remarks_info"] = remarks.parse(resp["remarks"])
    resp["time"] = core.make_timestamp(resp["time"], target_date=issued)
    return MetarData(**resp), units


def parse_in(report: str, issued: date = None) -> Tuple[MetarData, Units]:
    """
    Parser for the International METAR variant
    """
    units = Units(**IN_UNITS)
    resp = {"raw": report}
    resp["sanitized"], resp["remarks"], data = sanitize(report)
    data, resp["station"], resp["time"] = core.get_station_and_time(data)
    data, resp["runway_visibility"] = get_runway_visibility(data)
    if "CAVOK" not in data:
        data, resp["clouds"] = core.get_clouds(data)
    (
        data,
        resp["wind_direction"],
        resp["wind_speed"],
        resp["wind_gust"],
        resp["wind_variable_direction"],
    ) = core.get_wind(data, units)
    data, resp["altimeter"] = get_altimeter(data, units, "IN")
    if "CAVOK" in data:
        resp["visibility"] = core.make_number("CAVOK")
        resp["clouds"] = []
        data.remove("CAVOK")
    else:
        data, resp["visibility"] = core.get_visibility(data, units)
    data, resp["temperature"], resp["dewpoint"] = get_temp_and_dew(data)
    condition = core.get_flight_rules(
        resp["visibility"], core.get_ceiling(resp["clouds"])
    )
    resp["other"], resp["wx_codes"] = get_wx_codes(data)
    resp["flight_rules"] = FLIGHT_RULES[condition]
    resp["remarks_info"] = remarks.parse(resp["remarks"])
    resp["time"] = core.make_timestamp(resp["time"], target_date=issued)
    return MetarData(**resp), units


class Metar(Report):
    """
    Class to handle METAR report data
    """

    def _post_update(self):
        self.data, self.units = parse(self.icao, self.raw, self.issued)
        self.translations = translate_metar(self.data, self.units)

    @staticmethod
    def sanitize(report: str) -> str:
        """
        Sanitizes a METAR string
        """
        return sanitize(report)[0]

    @property
    def summary(self) -> str:
        """
        Condensed report summary created from translations
        """
        if not self.translations:
            self.update()
        return summary.metar(self.translations)

    @property
    def speech(self) -> str:
        """
        Report summary designed to be read by a text-to-speech program
        """
        if not self.data:
            self.update()
        return speech.metar(self.data, self.units)
