"""
"""

from avwx import core
from avwx.structs import Cloud, Number, PirepData, Timestamp

def _time(item: str) -> Timestamp:
    """
    Convert a time element to a Timestamp
    """
    item = item[2:].strip()
    return core.make_timestamp(item, time_only=True)


def _altitude(item: str) -> Number:
    """
    """
    item = item[2:].strip()
    return core.make_number(item)


def _aircraft(item: str) -> str:
    """
    """
    item = item[2:].strip()
    return item


def _clouds(item: str) -> [Cloud]:
    """
    """
    item = item[2:].strip()
    return [core.make_cloud(cloud) for cloud in item.split()]


def _number(item: str) -> Number:
    """
    """
    item = item[2:].strip()
    return core.make_number(item)

def _turbulance(item: str) -> str:
    item = item[2:].strip()
    return item

_handlers = {
    'OV': ('location', None),
    'TM': ('time', _time),
    'FL': ('altitude', _altitude),
    'TP': ('aircraft', _aircraft),
    'SK': ('clouds', _clouds),
    'WX': ('wx', None),
    'TA': ('temperature', _number),
    'TB': ('turbulance', _turbulance),
}

def parse(report: str) -> PirepData:
    """
    """
    clean = core.sanitize_report_string(report)
    wxdata, *_ = core.sanitize_report_list(clean.split())
    sanitized = ' '.join(wxdata)
    wxresp = {'raw': report, 'sanitized': sanitized}
    wxdata = sanitized.split('/')
    print(wxdata)
    for item in wxdata:
        if not item or len(item) < 2:
            continue
        try:
            key, handler = _handlers[item[:2]]
        except KeyError:
            continue
        if handler:
            wxresp[key] = handler(item)
    print(wxresp)
    return None
