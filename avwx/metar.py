"""
Contains METAR-specific functions for report parsing
"""

# stdlib
from copy import copy

# module
from avwx import _core, remarks, service
from avwx.static import FLIGHT_RULES, IN_UNITS, NA_UNITS
from avwx.station import uses_na_format, valid_station
from avwx.structs import MetarData, Units


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
    clean = _core.sanitize_report_string(report)
    wxdata, wxresp["remarks"] = _core.get_remarks(clean)
    wxdata = _core.dedupe(wxdata)
    wxdata = _core.sanitize_report_list(wxdata)
    wxresp["sanitized"] = " ".join(wxdata + [wxresp["remarks"]])
    wxdata, wxresp["station"], wxresp["time"] = _core.get_station_and_time(wxdata)
    wxdata, wxresp["runway_visibility"] = _core.get_runway_visibility(wxdata)
    wxdata, wxresp["clouds"] = _core.get_clouds(wxdata)
    (
        wxdata,
        wxresp["wind_direction"],
        wxresp["wind_speed"],
        wxresp["wind_gust"],
        wxresp["wind_variable_direction"],
    ) = _core.get_wind(wxdata, units)
    wxdata, wxresp["altimeter"] = _core.get_altimeter(wxdata, units, "NA")
    wxdata, wxresp["visibility"] = _core.get_visibility(wxdata, units)
    wxresp["other"], wxresp["temperature"], wxresp["dewpoint"] = _core.get_temp_and_dew(
        wxdata
    )
    condition = _core.get_flight_rules(
        wxresp["visibility"], _core.get_ceiling(wxresp["clouds"])
    )
    wxresp["flight_rules"] = FLIGHT_RULES[condition]
    wxresp["remarks_info"] = remarks.parse(wxresp["remarks"])
    wxresp["time"] = _core.make_timestamp(wxresp["time"])
    return MetarData(**wxresp), units


def parse_in(report: str) -> (MetarData, Units):
    """
    Parser for the International METAR variant
    """
    units = Units(**IN_UNITS)
    wxresp = {"raw": report}
    clean = _core.sanitize_report_string(report)
    wxdata, wxresp["remarks"] = _core.get_remarks(clean)
    wxdata = _core.dedupe(wxdata)
    wxdata = _core.sanitize_report_list(wxdata)
    wxresp["sanitized"] = " ".join(wxdata + [wxresp["remarks"]])
    wxdata, wxresp["station"], wxresp["time"] = _core.get_station_and_time(wxdata)
    wxdata, wxresp["runway_visibility"] = _core.get_runway_visibility(wxdata)
    if "CAVOK" not in wxdata:
        wxdata, wxresp["clouds"] = _core.get_clouds(wxdata)
    (
        wxdata,
        wxresp["wind_direction"],
        wxresp["wind_speed"],
        wxresp["wind_gust"],
        wxresp["wind_variable_direction"],
    ) = _core.get_wind(wxdata, units)
    wxdata, wxresp["altimeter"] = _core.get_altimeter(wxdata, units, "IN")
    if "CAVOK" in wxdata:
        wxresp["visibility"] = _core.make_number("CAVOK")
        wxresp["clouds"] = []
        wxdata.remove("CAVOK")
    else:
        wxdata, wxresp["visibility"] = _core.get_visibility(wxdata, units)
    wxresp["other"], wxresp["temperature"], wxresp["dewpoint"] = _core.get_temp_and_dew(
        wxdata
    )
    condition = _core.get_flight_rules(
        wxresp["visibility"], _core.get_ceiling(wxresp["clouds"])
    )
    wxresp["flight_rules"] = FLIGHT_RULES[condition]
    wxresp["remarks_info"] = remarks.parse(wxresp["remarks"])
    wxresp["time"] = _core.make_timestamp(wxresp["time"])
    return MetarData(**wxresp), units
