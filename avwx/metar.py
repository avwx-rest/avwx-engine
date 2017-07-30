"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/metar.py

Contains METAR-specific functions for fetching and parsing
"""

# stdlib
import json
from copy import copy
# library
from requests import get
from xmltodict import parse as parsexml
# module
import avwx.core as core
from avwx.exceptions import InvalidRequest
from avwx.static import REQUEST_URL, NA_UNITS, IN_UNITS, FLIGHT_RULES


def fetch(station: str) -> str:
    """Get METAR report for 'station' from www.aviationweather.gov
    Returns METAR report string or raises an error
    fetch pulls from the ADDS API and is 3x faster than fetch2
    """
    core.valid_station(station)
    xml = get(REQUEST_URL.format('metar', station)).text
    resp = parsexml(xml)
    resp_str = json.dumps(resp)
    for word in ['response', 'data', 'METAR', station]:
        if word not in resp_str:
            raise InvalidRequest(
                'Could not find "{}" in NOAA response\n{}'.format(word, json.dumps(resp, indent=4))
            )
    resp = json.loads(resp_str)['response']['data']['METAR']
    if isinstance(resp, dict):
        return resp['raw_text']
    elif isinstance(resp, list) and resp:
        return resp[0]['raw_text']
    else:
        raise InvalidRequest(
            'Could not find "raw_text" in NOAA response\n{}'.format(json.dumps(resp, indent=4))
        )


def fetch2(station: str) -> str:
    """Get METAR report for 'station' from www.aviationweather.gov
    Returns METAR report string or raises an error
    fetch2 scrapes the report from html
    """
    core.valid_station(station)
    url = (
        "http://www.aviationweather.gov/metar/data"
        "?ids={}"
        "&format=raw"
        "&date=0"
        "&hours=0"
    ).format(station)
    html = get(url).text
    if station + '<' in html:
        raise InvalidRequest('Station does not exist/Database lookup error')
    #Report begins with station iden
    start = html.find('<code>' + station + ' ') + 6
    #Report ends with html bracket
    end = html[start:].find('<')
    return html[start:start + end].replace('\n ', '')


def parse(station: str, txt: str) -> {str: object}:
    """Returns a dictionary of parsed METAR data
    Keys: Station, Time, Wind-Direction, Wind-Speed, Wind-Gust, Wind-Variable-Dir,
          Visibility, Runway-Vis-List, Altimeter, Temperature, Dewpoint,
          Cloud-List, Other-List, Remarks, Raw-Report, Units
    Units is dict of identified units of measurement for each field
    """
    core.valid_station(station)
    return parse_na(txt) if core.uses_na_format(station[:2]) else parse_in(txt)


def parse_na(txt: str) -> {str: object}:
    """Parser for the North American METAR variant"""
    units = copy(NA_UNITS)
    wxresp = {'Raw-Report': txt}
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
    """Parser for the International METAR variant"""
    units = copy(IN_UNITS)
    wxresp = {'Raw-Report': txt}
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
