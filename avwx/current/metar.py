"""
Contains METAR-specific functions for report parsing
"""

# module
from avwx.current.base import Report, get_wx_codes
from avwx.parsing import core, remarks, speech, summary
from avwx.parsing.translate.metar import translate_metar
from avwx.static.core import FLIGHT_RULES, IN_UNITS, NA_UNITS
from avwx.static.metar import METAR_RMK
from avwx.station import uses_na_format, valid_station
from avwx.structs import MetarData, Number, Units


def get_remarks(txt: str) -> ([str], str):
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


def get_runway_visibility(wxdata: [str]) -> ([str], [str]):
    """
    Returns the report list and the remove runway visibility list
    """
    runway_vis = []
    for i, item in reversed(list(enumerate(wxdata))):
        if (
            len(item) > 4
            and item[0] == "R"
            and (item[3] == "/" or item[4] == "/")
            and item[1:3].isdigit()
        ):
            runway_vis.append(wxdata.pop(i))
    runway_vis.sort()
    return wxdata, runway_vis


def get_altimeter(wxdata: [str], units: Units, version: str = "NA") -> ([str], Number):
    """
    Returns the report list and the removed altimeter item

    Version is 'NA' (North American / default) or 'IN' (International)
    """
    if not wxdata:
        return wxdata, None
    altimeter = ""
    target = wxdata[-1]
    # Handle QNH prefix:
    buf = 1
    if target.startswith("QNH"):
        buf = 3
        target = target.replace("QNH", "Q")
    if version == "NA":
        # Version target
        if target[0] == "A":
            altimeter = wxdata.pop()[buf:]
        # Other version but prefer normal if available
        elif target[0] == "Q":
            if len(wxdata) > 1 and wxdata[-2][0] == "A":
                wxdata.pop()
                altimeter = wxdata.pop()[buf:]
            else:
                units.altimeter = "hPa"
                altimeter = wxdata.pop()[buf:].lstrip(".")
        # Else grab the digits
        elif len(target) == 4 and target.isdigit():
            altimeter = wxdata.pop()
    elif version == "IN":
        # Version target
        if target[0] == "Q":
            altimeter = wxdata.pop()[buf:].lstrip(".")
            if "/" in altimeter:
                altimeter = altimeter[: altimeter.find("/")]
        # Other version but prefer normal if available
        elif target[0] == "A":
            if len(wxdata) > 1 and wxdata[-2][0] == "Q":
                wxdata.pop()
                altimeter = wxdata.pop()[buf:]
            else:
                units.altimeter = "inHg"
                altimeter = wxdata.pop()[buf:]
    # Some stations report both, but we only need one
    if wxdata and (wxdata[-1][0] == "A" or wxdata[-1][0] == "Q"):
        wxdata.pop()
    # convert to Number
    altimeter = altimeter.replace("/", "").strip("AQ")
    if not altimeter:
        return wxdata, None
    if units.altimeter == "inHg":
        value = altimeter[:2] + "." + altimeter[2:]
    else:
        value = altimeter
    return wxdata, core.make_number(value, altimeter)


def get_temp_and_dew(wxdata: str) -> ([str], Number, Number):
    """
    Returns the report list and removed temperature and dewpoint strings
    """
    for i, item in reversed(list(enumerate(wxdata))):
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
                wxdata.pop(i)
                return (wxdata, *[core.make_number(t) for t in tempdew])
    return wxdata, None, None


def parse(station: str, report: str) -> (MetarData, Units):
    """
    Returns MetarData and Units dataclasses with parsed data and their associated units
    """
    valid_station(station)
    if not report:
        return None, None
    return parse_na(report) if uses_na_format(station[:2]) else parse_in(report)


def parse_na(report: str) -> (MetarData, Units):
    """
    Parser for the North American METAR variant
    """
    units = Units(**NA_UNITS)
    wxresp = {"raw": report}
    clean = core.sanitize_report_string(report)
    wxdata, wxresp["remarks"] = get_remarks(clean)
    wxdata = core.dedupe(wxdata)
    wxdata = core.sanitize_report_list(wxdata)
    wxresp["sanitized"] = " ".join(wxdata + [wxresp["remarks"]])
    wxdata, wxresp["station"], wxresp["time"] = core.get_station_and_time(wxdata)
    wxdata, wxresp["runway_visibility"] = get_runway_visibility(wxdata)
    wxdata, wxresp["clouds"] = core.get_clouds(wxdata)
    (
        wxdata,
        wxresp["wind_direction"],
        wxresp["wind_speed"],
        wxresp["wind_gust"],
        wxresp["wind_variable_direction"],
    ) = core.get_wind(wxdata, units)
    wxdata, wxresp["altimeter"] = get_altimeter(wxdata, units, "NA")
    wxdata, wxresp["visibility"] = core.get_visibility(wxdata, units)
    wxdata, wxresp["temperature"], wxresp["dewpoint"] = get_temp_and_dew(wxdata)
    condition = core.get_flight_rules(
        wxresp["visibility"], core.get_ceiling(wxresp["clouds"])
    )
    wxresp["other"], wxresp["wx_codes"] = get_wx_codes(wxdata)
    wxresp["flight_rules"] = FLIGHT_RULES[condition]
    wxresp["remarks_info"] = remarks.parse(wxresp["remarks"])
    wxresp["time"] = core.make_timestamp(wxresp["time"])
    return MetarData(**wxresp), units


def parse_in(report: str) -> (MetarData, Units):
    """
    Parser for the International METAR variant
    """
    units = Units(**IN_UNITS)
    wxresp = {"raw": report}
    clean = core.sanitize_report_string(report)
    wxdata, wxresp["remarks"] = get_remarks(clean)
    wxdata = core.dedupe(wxdata)
    wxdata = core.sanitize_report_list(wxdata)
    wxresp["sanitized"] = " ".join(wxdata + [wxresp["remarks"]])
    wxdata, wxresp["station"], wxresp["time"] = core.get_station_and_time(wxdata)
    wxdata, wxresp["runway_visibility"] = get_runway_visibility(wxdata)
    if "CAVOK" not in wxdata:
        wxdata, wxresp["clouds"] = core.get_clouds(wxdata)
    (
        wxdata,
        wxresp["wind_direction"],
        wxresp["wind_speed"],
        wxresp["wind_gust"],
        wxresp["wind_variable_direction"],
    ) = core.get_wind(wxdata, units)
    wxdata, wxresp["altimeter"] = get_altimeter(wxdata, units, "IN")
    if "CAVOK" in wxdata:
        wxresp["visibility"] = core.make_number("CAVOK")
        wxresp["clouds"] = []
        wxdata.remove("CAVOK")
    else:
        wxdata, wxresp["visibility"] = core.get_visibility(wxdata, units)
    wxdata, wxresp["temperature"], wxresp["dewpoint"] = get_temp_and_dew(wxdata)
    condition = core.get_flight_rules(
        wxresp["visibility"], core.get_ceiling(wxresp["clouds"])
    )
    wxresp["other"], wxresp["wx_codes"] = get_wx_codes(wxdata)
    wxresp["flight_rules"] = FLIGHT_RULES[condition]
    wxresp["remarks_info"] = remarks.parse(wxresp["remarks"])
    wxresp["time"] = core.make_timestamp(wxresp["time"])
    return MetarData(**wxresp), units


class Metar(Report):
    """
    Class to handle METAR report data
    """

    def _post_update(self):
        self.data, self.units = parse(self.icao, self.raw)
        self.translations = translate_metar(self.data, self.units)

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
