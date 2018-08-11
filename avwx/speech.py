"""
Contains functions for converting translations into a speech string
Currently only supports METAR
"""

# stdlib
from copy import deepcopy
# module
from avwx import core, translate
from avwx.static import SPOKEN_UNITS, NUMBER_REPL, FRACTIONS
from avwx.structs import Cloud, MetarData, Number, Units


def wind(direction: Number,
         speed: Number,
         gust: Number,
         vardir: [Number] = None,
         unit: str = 'kt') -> str:
    """
    Format wind details into a spoken word string
    """
    unit = SPOKEN_UNITS.get(unit, unit)
    val = translate.wind(direction, speed, gust, vardir, unit,
                         cardinals=False, spoken=True)
    return 'Winds ' + (val or 'unknown')


def temperature(header: str, temp: Number, unit: str = 'C') -> str:
    """
    Format temperature details into a spoken word string
    """
    if not (temp and temp.value):
        return header + ' unknown'
    if unit in SPOKEN_UNITS:
        unit = SPOKEN_UNITS[unit]
    use_s = '' if temp.spoken in ('one', 'minus one') else 's'
    return ' '.join((header, temp.spoken, 'degree' + use_s, unit))


def visibility(vis: Number, unit: str = 'm') -> str:
    """
    Format visibility details into a spoken word string
    """
    if not vis:
        return 'Visibility unknown'
    if vis.value is None or '/' in vis.repr:
        ret_vis = vis.spoken
    else:
        ret_vis = translate.visibility(vis, unit=unit)
        if unit == 'm':
            unit = 'km'
        ret_vis = ret_vis[:ret_vis.find(' (')].lower().replace(unit, '').strip()
        ret_vis = core.spoken_number(core.remove_leading_zeros(ret_vis))
    ret = 'Visibility ' + ret_vis
    if unit in SPOKEN_UNITS:
        if '/' in vis.repr and 'half' not in ret:
            ret += ' of a'
        ret += ' ' + SPOKEN_UNITS[unit]
        if not (('one half' in ret and ' and ' not in ret) or 'of a' in ret):
            ret += 's'
    else:
        ret += unit
    return ret


def altimeter(alt: Number, unit: str = 'inHg') -> str:
    """
    Format altimeter details into a spoken word string
    """
    ret = 'Altimeter '
    if not alt:
        ret += 'unknown'
    elif unit == 'inHg':
        ret += core.spoken_number(alt.repr[:2]) + ' point ' + core.spoken_number(alt.repr[2:])
    elif unit == 'hPa':
        ret += core.spoken_number(alt.repr)
    return ret


def other(wxcodes: [str]) -> str:
    """
    Format wx codes into a spoken word string
    """
    ret = []
    for item in wxcodes:
        item = translate.wxcode(item)
        if item.startswith('Vicinity'):
            item = item.lstrip('Vicinity ') + ' in the Vicinity'
        ret.append(item)
    return '. '.join(ret)


def metar(wxdata: MetarData, units: Units) -> str:
    """
    Convert wxdata into a string for text-to-speech
    """
    # We make copies here because the functions may change the original values
    _data = deepcopy(wxdata)
    units = deepcopy(units)
    speech = []
    if _data.wind_direction and _data.wind_speed:
        speech.append(wind(_data.wind_direction, _data.wind_speed,
                           _data.wind_gust, _data.wind_variable_direction,
                           units.wind_speed))
    if _data.visibility:
        speech.append(visibility(_data.visibility, units.visibility))
    if _data.temperature:
        speech.append(temperature('Temperature', _data.temperature, units.temperature))
    if _data.dewpoint:
        speech.append(temperature('Dew point', _data.dewpoint, units.temperature))
    if _data.altimeter:
        speech.append(altimeter(_data.altimeter, units.altimeter))
    if _data.other:
        speech.append(other(_data.other))
    speech.append(translate.clouds(_data.clouds,
                                   units.altitude).replace(' - Reported AGL', ''))
    return ('. '.join([l for l in speech if l])).replace(',', '.')
