"""
Contains METAR-specific functions for report parsing
"""

# stdlib
from copy import copy
# module
from avwx import core, remarks, service
from avwx.static import NA_UNITS, IN_UNITS, FLIGHT_RULES
from avwx.structs import MetarData, Units

def parse(station: str, report: str) -> (MetarData, Units):
    """
    Returns MetarData and Units dataclasses with parsed data and their associated units
    """
    core.valid_station(station)
    if not report:
        return None, None
    return parse_na(report) if core.uses_na_format(station[:2]) else parse_in(report)


def parse_na(report: str) -> (MetarData, Units):
    """
    Parser for the North American METAR variant
    """
    units = Units(**NA_UNITS)
    clean = core.sanitize_report_string(report)
    wxresp = {'raw': report, 'sanitized': clean}
    wxdata, wxresp['remarks'] = core.get_remarks(clean)
    wxdata = core.dedupe(wxdata)
    wxdata, wxresp['runway_visibility'], _ = core.sanitize_report_list(wxdata)
    wxdata, wxresp['station'], wxresp['time'] = core.get_station_and_time(wxdata)
    wxdata, wxresp['clouds'] = core.get_clouds(wxdata)
    wxdata, wxresp['wind_direction'], wxresp['wind_speed'], \
        wxresp['wind_gust'], wxresp['wind_variable_direction'] = core.get_wind(wxdata, units)
    wxdata, wxresp['altimeter'] = core.get_altimeter(wxdata, units, 'NA')
    wxdata, wxresp['visibility'] = core.get_visibility(wxdata, units)
    wxresp['other'], wxresp['temperature'], wxresp['dewpoint'] = core.get_temp_and_dew(wxdata)
    condition = core.get_flight_rules(wxresp['visibility'], core.get_ceiling(wxresp['clouds']))
    wxresp['flight_rules'] = FLIGHT_RULES[condition]
    wxresp['remarks_info'] = remarks.parse(wxresp['remarks'])
    wxresp['time'] = core.make_timestamp(wxresp['time'])
    return MetarData(**wxresp), units


def parse_in(report: str) -> (MetarData, Units):
    """
    Parser for the International METAR variant
    """
    units = Units(**IN_UNITS)
    clean = core.sanitize_report_string(report)
    wxresp = {'raw': report, 'sanitized': clean}
    wxdata, wxresp['remarks'] = core.get_remarks(clean)
    wxdata = core.dedupe(wxdata)
    wxdata, wxresp['runway_visibility'], _ = core.sanitize_report_list(wxdata)
    wxdata, wxresp['station'], wxresp['time'] = core.get_station_and_time(wxdata)
    if 'CAVOK' not in wxdata:
        wxdata, wxresp['clouds'] = core.get_clouds(wxdata)
    wxdata, wxresp['wind_direction'], wxresp['wind_speed'], \
        wxresp['wind_gust'], wxresp['wind_variable_direction'] = core.get_wind(wxdata, units)
    wxdata, wxresp['altimeter'] = core.get_altimeter(wxdata, units, 'IN')
    if 'CAVOK' in wxdata:
        wxresp['visibility'] = core.make_number('CAVOK')
        wxresp['clouds'] = []
        wxdata.remove('CAVOK')
    else:
        wxdata, wxresp['visibility'] = core.get_visibility(wxdata, units)
    wxresp['other'], wxresp['temperature'], wxresp['dewpoint'] = core.get_temp_and_dew(wxdata)
    condition = core.get_flight_rules(wxresp['visibility'], core.get_ceiling(wxresp['clouds']))
    wxresp['flight_rules'] = FLIGHT_RULES[condition]
    wxresp['remarks_info'] = remarks.parse(wxresp['remarks'])
    wxresp['time'] = core.make_timestamp(wxresp['time'])
    return MetarData(**wxresp), units
