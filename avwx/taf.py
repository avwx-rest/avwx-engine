"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/taf.py

Contains TAF-specific functions for fetching and parsing
"""

# stdlib
import json
from copy import copy
# library
from requests import get
from xmltodict import parse as parsexml
# module
from avwx import core
from avwx.exceptions import InvalidRequest
from avwx.static import REQUEST_URL, NA_UNITS, IN_UNITS, TAF_RMK, TAF_NEWLINE


def fetch(station: str) -> str:
    """Get TAF report for 'station' from www.aviationweather.gov
    Returns TAF report string or raises an error
    fetch pulls from the ADDS API and is 3x faster than fetch2
    """
    core.valid_station(station)
    xml = get(REQUEST_URL.format('taf', station)).text
    resp = parsexml(xml)
    resp_str = json.dumps(resp)
    for word in ['response', 'data', 'TAF', station]:
        if word not in resp_str:
            raise InvalidRequest(
                'Could not find "{}" in NOAA response\n{}'.format(word, json.dumps(resp, indent=4))
            )
    resp = json.loads(resp_str)['response']['data']['TAF']
    if isinstance(resp, dict):
        return resp['raw_text']
    elif isinstance(resp, list) and resp:
        return resp[0]['raw_text']
    else:
        raise InvalidRequest(
            'Could not find "raw_text" in NOAA response\n{}'.format(json.dumps(resp, indent=4))
        )


def fetch2(station: str) -> str:
    """Get TAF report for 'station' from www.aviationweather.gov
    Returns METAR report string or raises an error
    fetch2 scrapes the report from html
    """
    core.valid_station(station)
    url = (
        "http://www.aviationweather.gov/taf/data"
        "?ids={}"
        "&format=raw"
        "&submit=Get+TAF+data"
    ).format(station)
    html = get(url).text
    if station + '<' in html:
        raise InvalidRequest('Station does not exist/Database lookup error')
    # Standard report begins with 'TAF'
    start = html.find('<code>TAF ') + 6
    # US report begins with station iden
    if start == 5:
        start = html.find('<code>' + station + ' ') + 6
    # Beginning of report is non-standard/skewed
    if start == 5:
        raise InvalidRequest('Request response was not able to be isolated')
    # Report ends with html bracket
    end = html[start:].find('</code>')
    return html[start:start + end].replace('\n ', '')


def parse(station: str, txt: str, delim: str='<br/>&nbsp;&nbsp;') -> {str: object}:
    """Returns a dictionary of parsed TAF data
    'delim' is the divider between forecast lines. Ex: aviationweather.gov uses '<br/>&nbsp;&nbsp;'
    Keys: Station, Time, Forecast, Remarks, Min-Temp, Max-Temp, Raw-Report, Units
    Oceania stations also have the following keys: Temp-List, Alt-List
    Forecast is list of report dicts in order of time with the following keys:
    Type, Start-Time, End-Time, Flight-Rules, Wind-Direction, Wind-Speed, Wind-Gust, Wind-Shear,
    Visibility, Altimeter, Cloud-List, Icing-List, Turb-List, Other-List, Probability, Raw-Line
    Units is dict of identified units of measurement for each field
    """
    core.valid_station(station)
    retwx = {}
    retwx['Raw-Report'] = txt
    while len(txt) > 3 and txt[:4] in ['TAF ', 'AMD ', 'COR ']:
        txt = txt[4:]
    _, retwx['Station'], retwx['Time'] = core.get_station_and_time(txt[:20].split(' '))
    txt = txt.replace(retwx['Station'], '')
    txt = txt.replace(retwx['Time'], '')
    if core.uses_na_format(retwx['Station']):
        is_international = False
        units = copy(NA_UNITS)
    else:
        is_international = True
        units = copy(IN_UNITS)
    retwx['Remarks'] = ''
    parsed_lines = []
    prob = ''
    lines = txt.strip(' ').split(delim)
    while lines:
        line = lines[0].strip(' ')
        line = core.sanitize_line(line)
        #Remove Remarks from line
        index = core.find_first_in_list(line, TAF_RMK)
        if index != -1:
            retwx['Remarks'] = line[index:]
            line = line[:index].strip(' ')
        #Separate new lines fixed by sanitizeLine
        index = core.find_first_in_list(line, TAF_NEWLINE)
        if index != -1:
            lines.insert(1, line[index + 1:])
            line = line[:index]
        # Remove prob from the beginning of a line
        if line.startswith('PROB'):
            # Add standalone prob to next line
            if len(line) == 6:
                prob = line
                line = ''
            # Add to current line
            elif len(line) > 6:
                prob = line[:6]
                line = line[6:].strip()
        if line:
            # Separate full prob forecast into its own line
            if ' PROB' in line:
                probindex = line.index(' PROB')
                lines.insert(1, line[probindex + 1:])
                line = line[:probindex]
            raw_line = prob + ' ' + line if prob else line
            parsed_line, units = parse_in_line(line, units) if is_international \
                else parse_na_line(line, units)
            parsed_line['Probability'] = prob[4:]
            parsed_line['Raw-Line'] = raw_line
            prob = ''
            parsed_lines.append(parsed_line)
        lines.pop(0)
    if parsed_lines:
        parsed_lines[len(parsed_lines) - 1]['Other-List'], retwx['Max-Temp'], retwx['Min-Temp'] \
            = core.get_temp_min_and_max(parsed_lines[len(parsed_lines) - 1]['Other-List'])
        if not (retwx['Max-Temp'] or retwx['Min-Temp']):
            parsed_lines[0]['Other-List'], retwx['Max-Temp'], retwx['Min-Temp'] \
                = core.get_temp_min_and_max(parsed_lines[0]['Other-List'])
        parsed_lines = core.find_missing_taf_times(parsed_lines)
        parsed_lines = core.get_taf_flight_rules(parsed_lines)
    else:
        retwx['Min-Temp'] = ['', '']
        retwx['Max-Temp'] = ['', '']
    if retwx['Station'][0] == 'A':
        parsed_lines[len(parsed_lines) - 1]['Other-List'], retwx['Alt-List'], retwx['Temp-List'] \
            = core.get_oceania_temp_and_alt(parsed_lines[len(parsed_lines) - 1]['Other-List'])
    retwx['Forecast'] = parsed_lines
    retwx['Units'] = units
    return retwx


def parse_na_line(txt: str, units: {str: str}) -> ({str: object}, {str: str}):
    """Parser for the North American TAF forcast varient"""
    retwx = {}
    wxdata = txt.split(' ')
    wxdata, _, retwx['Wind-Shear'] = core.sanitize_report_list(wxdata, remove_clr_and_skc=False)
    wxdata, retwx['Type'], retwx['Start-Time'], retwx['End-Time'] = core.get_type_and_times(wxdata)
    wxdata, units, retwx['Wind-Direction'], retwx['Wind-Speed'],\
        retwx['Wind-Gust'], _ = core.get_wind(wxdata, units)
    wxdata, units, retwx['Visibility'] = core.get_visibility(wxdata, units)
    wxdata, retwx['Cloud-List'] = core.get_clouds(wxdata)
    retwx['Other-List'], retwx['Altimeter'], retwx['Icing-List'], retwx['Turb-List'] \
        = core.get_taf_alt_ice_turb(wxdata)
    return retwx, units


def parse_in_line(txt: str, units: {str: str}) -> ({str: object}, {str: str}):
    """Parser for the North American TAF forcast varient"""
    retwx = {}
    wxdata = txt.split(' ')
    wxdata, _, retwx['Wind-Shear'] = core.sanitize_report_list(wxdata, remove_clr_and_skc=False)
    wxdata, retwx['Type'], retwx['Start-Time'], retwx['End-Time'] = core.get_type_and_times(wxdata)
    wxdata, units, retwx['Wind-Direction'], retwx['Wind-Speed'],\
        retwx['Wind-Gust'], _ = core.get_wind(wxdata, units)
    if 'CAVOK' in wxdata:
        retwx['Visibility'] = '9999'
        retwx['Cloud-List'] = []
        wxdata.pop(wxdata.index('CAVOK'))
    else:
        wxdata, units, retwx['Visibility'] = core.get_visibility(wxdata, units)
        wxdata, retwx['Cloud-List'] = core.get_clouds(wxdata)
    retwx['Other-List'], retwx['Altimeter'], retwx['Icing-List'], retwx['Turb-List'] \
        = core.get_taf_alt_ice_turb(wxdata)
    return retwx, units
