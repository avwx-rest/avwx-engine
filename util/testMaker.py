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
    return {
        'data': asdict(m.data),
        'translations': asdict(m.translations),
        'summary': m.summary,
        'speech': m.speech,
        'station_info': asdict(m.station_info)
    }

def make_taf_test(station: str):
    """
    Builds TAF test files
    """
    t = avwx.Taf(station)
    t.update()
    return {
        'data': asdict(t.data),
        'translations': asdict(t.translations),
        'summary': t.summary,
        'station_info': asdict(t.station_info)
    }

if __name__ == '__main__':
    for station in ('KJFK', 'KMCO', 'PHNL', 'EGLL'):
        func = make_metar_test
        # func = make_taf_test
        json.dump(func(station), open(station+'.json', 'w'), indent=4, sort_keys=True)
