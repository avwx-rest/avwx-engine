#!/usr/bin/python3

"""
Creates files for end-to-end tests
"""

# stdlib
import json
from dataclasses import asdict
# module
import avwx

def make_metar_test(station: str):
    """
    Builds METAR test files
    """
    m = avwx.Metar(station)
    m.update()
    # Clear timestamp due to parse_date limitations
    m.data.time = None
    return {
        'data': asdict(m.data),
        'translations': asdict(m.translations),
        'summary': m.summary,
        'speech': m.speech,
        'station_info': asdict(m.station_info)
    }

def make_taf_test(station: str, report: str = None):
    """
    Builds TAF test files
    """
    t = avwx.Taf(station)
    t.update(report)
    data = asdict(t.data)
    # Clear timestamp due to parse_date limitations
    for key in ('time', 'start_time', 'end_time'):
        data[key] = None
    for i in range(len(data['forecast'])):
        for key in ('start_time', 'end_time'):
            data['forecast'][i][key] = None
    return {
        'data': data,
        'translations': asdict(t.translations),
        'summary': t.summary,
        'speech': t.speech,
        'station_info': asdict(t.station_info)
    }

if __name__ == '__main__':
    for station in ('KJFK', 'KMCO', 'PHNL', 'EGLL'):
        func = make_metar_test
        # func = make_taf_test
        json.dump(func(station), open(station+'.json', 'w'), indent=4, sort_keys=True)
