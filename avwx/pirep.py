"""
"""

from avwx import core, static
from avwx.exceptions import BadStation
from avwx.structs import Cloud, Icing, Location, Number, PirepData, Timestamp, Turbulance, Units

_units = Units(**static.NA_UNITS)


def _root(item: str) -> dict:
    """
    """
    items = item.split()
    rtype = None
    station = None
    # Find valid station
    for item in items:
        try:
            core.valid_station(item)
            station = item
            break
        except BadStation:
            continue
    # Determine report type
    if 'UA' in items:
        rtype = 'routine'
    elif 'UUA' in items:
        rtype = 'urgent'
    return {
        'station': station,
        'type': rtype,
    }

def _location(item: str) -> Location:
    """
    """
    items = item.split()
    if not items or len(items) != 2:
        return
    # 10 WGON
    if items[0].isdigit():
        station = items[1][-3:]
        direction = core.make_number(items[1][:-3])
        distance = core.make_number(items[0])
    # GON 270010
    elif items[1].isdigit():
        station = items[0]
        direction = core.make_number(items[1][:3])
        distance = core.make_number(items[1][3:])
    return Location(item, station, direction, distance)

def _time(item: str) -> Timestamp:
    """
    Convert a time element to a Timestamp
    """
    return core.make_timestamp(item, time_only=True)


def _altitude(item: str) -> 'Number|str':
    """
    """
    if item.isdigit():
        return core.make_number(item)
    return item


def _aircraft(item: str) -> str:
    """
    """
    return item


def _clouds(item: str) -> [Cloud]:
    """
    """
    return [core.make_cloud(cloud) for cloud in item.split()]


def _number(item: str) -> Number:
    """
    """
    return core.make_number(item)

def _turbulance(item: str) -> Turbulance:
    """
    """
    items = item.split()
    ret = {'severity': items.pop(0), 'floor': None, 'ceiling': None}
    if items and '-' in items[0]:
        for key, val in zip(('floor', 'ceiling'), items[0].split('-')):
            ret[key] = core.make_number(val)
    return Turbulance(**ret)


def _icing(item: str) -> Icing:
    """
    """
    items = item.split()
    ret = {'severity': items.pop(0), 'type': None, 'floor': None, 'ceiling': None}
    for item in items:
        if '-' in item:
            for key, val in zip(('floor', 'ceiling'), item.split('-')):
                ret[key] = core.make_number(val)
        else:
            ret['type'] = item
    return Icing(**ret)


def _remarks(item: str) -> str:
    """
    """
    return item


def _wx(item: str) -> dict:
    """
    """
    ret = {'wx': []}
    items = item.split()
    for item in items:
        if len(item) < 3:
            ret['wx'].append(item)
        elif item.startswith('FV'):
            _, ret['flight_visibility'] = core.get_visibility([item[2:]], _units)
        else:
            ret['wx'].append(item)
    return ret


_handlers = {
    'OV': ('location', _location),
    'TM': ('time', _time),
    'FL': ('altitude', _altitude),
    'TP': ('aircraft', _aircraft),
    'SK': ('clouds', _clouds),
    'TA': ('temperature', _number),
    'TB': ('turbulance', _turbulance),
    'IC': ('icing', _icing),
    'RM': ('remarks', _remarks),
}


_dict_handlers = {
    'WX': _wx,
}


def parse(report: str) -> PirepData:
    """
    """
    clean = core.sanitize_report_string(report)
    wxdata, *_ = core.sanitize_report_list(clean.split())
    sanitized = ' '.join(wxdata)
    wxresp = {'raw': report, 'sanitized': sanitized, 'station': None, 'remarks': None}
    wxdata = sanitized.split('/')
    print(wxdata)
    wxresp.update(_root(wxdata.pop(0).strip()))
    for item in wxdata:
        if not item or len(item) < 2:
            continue
        tag = item[:2]
        item = item[2:].strip()
        if tag in _handlers:
            key, handler = _handlers[tag]
            wxresp[key] = handler(item)
        elif tag in _dict_handlers:
            wxresp.update(_dict_handlers[tag](item))
    print(wxresp)
    return PirepData(**wxresp)
