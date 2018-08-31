"""
Contains TAF-specific functions for fetching and parsing
"""

# stdlib
from copy import copy
# module
from avwx import core, service
from avwx.static import NA_UNITS, IN_UNITS, TAF_RMK, TAF_NEWLINE
from avwx.structs import TafData, TafLineData, Units


def fetch(station: str) -> str:
    """
    Returns TAF report string or raises an error

    Maintains backwards compatability but uses the new Service object.
    It is recommended to use the Service class directly instead of this function
    """
    return service.get_service(station)('taf').fetch(station)


def parse(station: str, txt: str, delim: str = '<br/>&nbsp;&nbsp;') -> TafData:
    """
    Returns TafData and Units dataclasses with parsed data and their associated units

    'delim' is the divider between forecast lines. Ex: aviationweather.gov uses '<br/>&nbsp;&nbsp;'
    """
    core.valid_station(station)
    while len(txt) > 3 and txt[:4] in ('TAF ', 'AMD ', 'COR '):
        txt = txt[4:]
    _, station, time = core.get_station_and_time(txt[:20].split(' '))
    retwx = {
        'end_time': None,
        'raw': txt,
        'remarks': None,
        'start_time': None,
        'station': station,
        'time': core.make_timestamp(time)
    }
    txt = txt.replace(station, '')
    txt = txt.replace(time, '')
    if core.uses_na_format(station):
        use_na = True
        units = Units(**NA_UNITS)
    else:
        use_na = False
        units = Units(**IN_UNITS)
    parsed_lines, retwx['remarks'] = parse_lines(txt.strip().split(delim), units, use_na)
    # Perform additional info extract and corrections
    if parsed_lines:
        parsed_lines[-1]['other'], retwx['max_temp'], retwx['min_temp'] \
            = core.get_temp_min_and_max(parsed_lines[-1]['other'])
        if not (retwx['max_temp'] or retwx['min_temp']):
            parsed_lines[0]['other'], retwx['max_temp'], retwx['min_temp'] \
                = core.get_temp_min_and_max(parsed_lines[0]['other'])
        # Set start and end times based on the first line
        start, end = parsed_lines[0]['start_time'], parsed_lines[0]['end_time']
        parsed_lines[0]['end_time'] = None
        retwx['start_time'], retwx['end_time'] = start, end
        parsed_lines = core.find_missing_taf_times(parsed_lines, start, end)
        parsed_lines = core.get_taf_flight_rules(parsed_lines)
    # Extract Oceania-specific data
    if retwx['station'][0] == 'A':
        parsed_lines[-1]['other'], retwx['alts'], retwx['temps'] \
            = core.get_oceania_temp_and_alt(parsed_lines[-1]['other'])
    # Convert to dataclass
    retwx['forecast'] = [TafLineData(**line) for line in parsed_lines]
    return TafData(**retwx), units


def parse_lines(lines: [str], units: Units, use_na: bool = True) -> ([dict], str):
    """
    Returns a list of parsed line dictionaries and the remarks string if found
    """
    parsed_lines = []
    prob = ''
    remarks = ''
    while lines:
        raw_line = lines[0].strip(' ')
        line = core.sanitize_line(raw_line)
        #Remove Remarks from line
        index = core.find_first_in_list(line, TAF_RMK)
        if index != -1:
            remarks = line[index:]
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
            parsed_line = (parse_na_line if use_na else parse_in_line)(line, units)
            for key in ('start_time', 'end_time'):
                parsed_line[key] = core.make_timestamp(parsed_line[key])
            parsed_line['probability'] = core.make_number(prob[4:])
            parsed_line['raw'] = raw_line
            parsed_line['sanitized'] = prob + ' ' + line if prob else line
            prob = ''
            parsed_lines.append(parsed_line)
        lines.pop(0)
    return parsed_lines, remarks


def parse_na_line(txt: str, units: Units) -> {str: str}:
    """
    Parser for the North American TAF forcast varient
    """
    retwx = {}
    wxdata = txt.split(' ')
    wxdata, _, retwx['wind_shear'] = core.sanitize_report_list(wxdata)
    wxdata, retwx['type'], retwx['start_time'], retwx['end_time'] = core.get_type_and_times(wxdata)
    wxdata, retwx['wind_direction'], retwx['wind_speed'],\
        retwx['wind_gust'], _ = core.get_wind(wxdata, units)
    wxdata, retwx['visibility'] = core.get_visibility(wxdata, units)
    wxdata, retwx['clouds'] = core.get_clouds(wxdata)
    retwx['other'], retwx['altimeter'], retwx['icing'], retwx['turbulance'] \
        = core.get_taf_alt_ice_turb(wxdata)
    return retwx


def parse_in_line(txt: str, units: Units) -> {str: str}:
    """
    Parser for the International TAF forcast varient
    """
    retwx = {}
    wxdata = txt.split(' ')
    wxdata, _, retwx['wind_shear'] = core.sanitize_report_list(wxdata)
    wxdata, retwx['type'], retwx['start_time'], retwx['end_time'] = core.get_type_and_times(wxdata)
    wxdata, retwx['wind_direction'], retwx['wind_speed'],\
        retwx['wind_gust'], _ = core.get_wind(wxdata, units)
    if 'CAVOK' in wxdata:
        retwx['visibility'] = '9999'
        retwx['clouds'] = []
        wxdata.pop(wxdata.index('CAVOK'))
    else:
        wxdata, retwx['visibility'] = core.get_visibility(wxdata, units)
        wxdata, retwx['clouds'] = core.get_clouds(wxdata)
    retwx['other'], retwx['altimeter'], retwx['icing'], retwx['turbulance'] \
        = core.get_taf_alt_ice_turb(wxdata)
    return retwx
