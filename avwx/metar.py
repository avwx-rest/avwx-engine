"""
Contains METAR-specific functions for fetching and parsing
"""

# stdlib
from copy import copy
# module
from avwx import core, service
from avwx.static import NA_UNITS, IN_UNITS, FLIGHT_RULES

def fetch(station: str) -> str:
    """
    Returns METAR report string or raises an error
    
    Maintains backwards compatability but uses the new Request object
    """
    return service.get_service(station)('metar').fetch(station)


def parse(station: str, txt: str) -> {str: object}:
    """Returns a dictionary of parsed METAR data

    Keys: Station, Time, Wind-Direction, Wind-Speed, Wind-Gust, Wind-Variable-Dir,
          Visibility, Runway-Vis-List, Altimeter, Temperature, Dewpoint,
          Cloud-List, Other-List, Remarks, Units

    Units is dict of identified units of measurement for each field
    """
    core.valid_station(station)
    return parse_na(txt) if core.uses_na_format(station[:2]) else parse_in(txt)


def parse_na(txt: str) -> {str: object}:
    """
    Parser for the North American METAR variant
    """
    units = copy(NA_UNITS)
    wxresp = {}
    txt = core.sanitize_report_string(txt)
    wxdata, wxresp['Remarks'] = core.get_remarks(txt)
    wxdata, wxresp['Runway-Vis-List'], _ = core.sanitize_report_list(wxdata)
    wxdata, wxresp['Station'], wxresp['Time'] = core.get_station_and_time(wxdata)
    wxdata, wxresp['Cloud-List'] = core.get_clouds(wxdata)
    wxdata, units, wxresp['Wind-Direction'], wxresp['Wind-Speed'], \
        wxresp['Wind-Gust'], wxresp['Wind-Variable-Dir'] = core.get_wind(wxdata, units)
    wxdata, units, wxresp['Altimeter'] = core.get_altimeter(wxdata, units, 'NA')
    wxdata, units, wxresp['Visibility'] = core.get_visibility(wxdata, units)
    wxresp['Other-List'], wxresp['Temperature'], wxresp['Dewpoint'] = core.get_temp_and_dew(wxdata)
    wxresp['Units'] = units
    condition = core.get_flight_rules(wxresp['Visibility'], core.get_ceiling(wxresp['Cloud-List']))
    wxresp['Flight-Rules'] = FLIGHT_RULES[condition]
    wxresp['Remarks-Info'] = core.parse_remarks(wxresp['Remarks'])
    return wxresp


def parse_in(txt: str) -> {str: object}:
    """
    Parser for the International METAR variant
    """
    units = copy(IN_UNITS)
    wxresp = {}
    txt = core.sanitize_report_string(txt)
    wxdata, wxresp['Remarks'] = core.get_remarks(txt)
    wxdata, wxresp['Runway-Vis-List'], _ = core.sanitize_report_list(wxdata)
    wxdata, wxresp['Station'], wxresp['Time'] = core.get_station_and_time(wxdata)
    if 'CAVOK' not in wxdata:
        wxdata, wxresp['Cloud-List'] = core.get_clouds(wxdata)
    wxdata, units, wxresp['Wind-Direction'], wxresp['Wind-Speed'], \
        wxresp['Wind-Gust'], wxresp['Wind-Variable-Dir'] = core.get_wind(wxdata, units)
    wxdata, units, wxresp['Altimeter'] = core.get_altimeter(wxdata, units, 'IN')
    if 'CAVOK' in wxdata:
        wxresp['Visibility'] = '9999'
        wxresp['Cloud-List'] = []
        wxdata.remove('CAVOK')
    else:
        wxdata, units, wxresp['Visibility'] = core.get_visibility(wxdata, units)
    wxresp['Other-List'], wxresp['Temperature'], wxresp['Dewpoint'] = core.get_temp_and_dew(wxdata)
    wxresp['Units'] = units
    condition = core.get_flight_rules(wxresp['Visibility'], core.get_ceiling(wxresp['Cloud-List']))
    wxresp['Flight-Rules'] = FLIGHT_RULES[condition]
    wxresp['Remarks-Info'] = core.parse_remarks(wxresp['Remarks'])
    return wxresp
