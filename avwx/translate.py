"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/translate.py

Contains functions for translating report data
"""

from avwx import core
from avwx.static import CLOUD_TRANSLATIONS, WX_TRANSLATIONS, TURBULANCE_CONDITIONS, ICING_CONDITIONS


def get_cardinal_direction(wdir: str) -> str:
    """Returns the cardinal direction (NSEW) for a degree direction
    Wind Direction - Cheat Sheet
    (360) -- 011/012 -- 033/034 -- (045) -- 056/057 -- 078/079 -- (090)
    (090) -- 101/102 -- 123/124 -- (135) -- 146/147 -- 168/169 -- (180)
    (180) -- 191/192 -- 213/214 -- (225) -- 236/237 -- 258/259 -- (270)
    (270) -- 281/282 -- 303/304 -- (315) -- 326/327 -- 348/349 -- (360)
    """
    ret = ''
    if not isinstance(wdir, int):
        wdir = int(wdir)
    if 304 <= wdir <= 360 or 0 <= wdir <= 56:
        ret += 'N'
        if 304 <= wdir <= 348:
            if 327 <= wdir <= 348:
                ret += 'N'
            ret += 'W'
        elif 11 <= wdir <= 56:
            if 11 <= wdir <= 33:
                ret += 'N'
            ret += 'E'
    elif 124 <= wdir <= 236:
        ret += 'S'
        if 124 <= wdir <= 168:
            if 147 <= wdir <= 168:
                ret += 'S'
            ret += 'E'
    elif 57 <= wdir <= 123:
        ret += 'E'
        if 57 <= wdir <= 78:
            ret += 'NE'
        elif 102 <= wdir <= 123:
            ret += 'SE'
    elif 237 <= wdir <= 303:
        ret += 'W'
        if 237 <= wdir <= 258:
            ret += 'SW'
        elif 282 <= wdir <= 303:
            ret += 'NW'
    return ret


def wind(wdir: str, wspd: str, wgst: str, wvar: [str]=None, unit: str='kt', cardinals=True) -> str:
    """Format wind elements into a readable sentence
    Returns the translation string
    Ex: NNE-020 (variable 010 to 040) at 14kt gusting to 20kt
    """
    ret = ''
    if wdir == '000':
        ret += 'Calm'
    elif wdir.isdigit():
        if cardinals:
            ret += get_cardinal_direction(wdir) + '-'
        ret += wdir
    elif wdir == 'VRB':
        ret += 'Variable'
    else:
        ret += wdir
    if wvar and isinstance(wvar, list):
        ret += ' (variable {low} to {high})'.format(low=wvar[0], high=wvar[1])
    if wspd and wspd not in ('0', '00'):
        ret += ' at {speed}{unit}'.format(speed=wspd, unit=unit)
    if wgst:
        ret += ' gusting to {speed}{unit}'.format(speed=wgst, unit=unit)
    return ret


def visibility(vis: str, unit: str='m') -> str:
    """Formats a visibility element into a string with both km and sm values
    Ex: 8km ( 5sm )
    """
    if vis == 'P6':
        return 'Greater than 6sm ( >9999m )'
    if vis == 'M1/4':
        return 'Less than .25sm ( <0400m )'
    if '/' in vis and not core.is_unknown(vis):
        vis = float(vis[:vis.find('/')]) / int(vis[vis.find('/') + 1:])
    try:
        float(vis)
    except ValueError:
        return ''
    if unit == 'm':
        converted = float(vis) * 0.000621371
        converted = str(round(converted, 1)).replace('.0', '') + 'sm'
        vis = str(round(int(vis) / 1000, 1)).replace('.0', '')
        unit = 'km'
    elif unit == 'sm':
        converted = float(vis) / 0.621371
        converted = str(round(converted, 1)).replace('.0', '') + 'km'
        vis = str(vis).replace('.0', '')
    else:
        return ''
    return vis + unit + ' (' + converted + ')'


def temperature(temp: str, unit: str='C') -> str:
    """Formats a temperature element into a string with both C and F values
    Used for both Temp and Dew
    Ex: 34C (93F)
    """
    temp = temp.replace('M', '-')
    try:
        int(temp)
    except ValueError:
        return ''
    unit = unit.upper()
    if unit == 'C':
        converted = int(temp) * 1.8 + 32
        converted = str(int(round(converted))) + 'F'
    elif unit == 'F':
        converted = (int(temp) - 32) / 1.8
        converted = str(int(round(converted))) + 'C'
    else:
        return ''
    return temp + unit + ' (' + converted + ')'


def altimeter(alt: str, unit: str='hPa') -> str:
    """Formats the altimter element into a string with hPa and inHg values
    Ex: 30.11 inHg (10.20 hPa)
    """
    if not alt.isdigit():
        if len(alt) == 5 and alt[1:].isdigit():
            alt = alt[1:]
        else:
            return ''
    if unit == 'hPa':
        converted = float(alt) / 33.8638866667
        converted = str(round(converted, 2)) + 'inHg'
    elif unit == 'inHg':
        alt = alt[:2] + '.' + alt[2:]
        converted = float(alt) * 33.8638866667
        converted = str(int(round(converted))) + 'hPa'
    else:
        return ''
    return alt + unit + ' (' + converted + ')'


def clouds(clds: [str], unit: str='ft') -> str:
    """Format cloud list into a readable sentence
    Returns the translation string
    Ex: Broken layer at 2200ft (Cumulonimbus), Overcast layer at 3600ft - Reported AGL
    """
    ret = []
    for cloud in clds:
        if len(cloud) == 2 and cloud[1].isdigit() and cloud[0] in CLOUD_TRANSLATIONS:
            ret.append(CLOUD_TRANSLATIONS[cloud[0]].format(int(cloud[1]) * 100, unit))
        elif len(cloud) == 3 and cloud[1].isdigit() \
            and cloud[0] in CLOUD_TRANSLATIONS and cloud[2] in CLOUD_TRANSLATIONS:
            cloudstr = CLOUD_TRANSLATIONS[cloud[0]] + ' (' + CLOUD_TRANSLATIONS[cloud[2]] + ')'
            ret.append(cloudstr.format(int(cloud[1]) * 100, unit))
    if ret:
        return ', '.join(ret) + ' - Reported AGL'
    return 'Sky clear'


def wxcode(wxstr: str) -> str:
    """Translates weather codes into readable strings
    Returns translated string of variable length
    """
    if wxstr[0] == '+':
        ret = 'Heavy '
        wxstr = wxstr[1:]
    elif wxstr[0] == '-':
        ret = 'Light '
        wxstr = wxstr[1:]
    else:
        ret = ''
    #Return wxstr if wxstr is not a code, ex R03/03002V03
    if len(wxstr) not in [2, 4, 6]:
        return wxstr
    for _ in range(len(wxstr) // 2):
        if wxstr[:2] in WX_TRANSLATIONS:
            ret += WX_TRANSLATIONS[wxstr[:2]] + ' '
        else:
            ret += wxstr[:2]
        wxstr = wxstr[2:]
    return ret.strip(' ')


def other_list(wxcodes: [str]) -> str:
    """Translate the list of wx codes (otherList) into a readable sentence
    Returns the translation string
    """
    ret = []
    for item in wxcodes:
        ret.append(wxcode(item))
    return ', '.join(ret)


def wind_shear(shear: str, unit_alt: str='ft', unit_wnd: str='kt') -> str:
    """Translate wind shear into a readable string
    Ex: Wind shear 2000ft from 140 at 30kt
    """
    if not shear or 'WS' not in shear or '/' not in shear:
        return ''
    shear = shear[2:].split('/')
    return 'Wind shear {alt}{unit_alt} from {winddir} at {speed}{unit_wind}'.format(
        alt=int(shear[0]) * 100, unit_alt=unit_alt, winddir=shear[1][:3],
        speed=shear[1][3:], unit_wind=unit_wnd)


def turb_ice(turbice: [str], unit: str='ft') -> str:
    """Translate the list of turbulance or icing into a readable sentence
    Ex: Occasional moderate turbulence in clouds from 3000ft to 14000ft
    """
    if not turbice:
        return ''
    #Determine turbulance or icing
    if turbice[0][0] == '5':
        conditions = TURBULANCE_CONDITIONS
    elif turbice[0][0] == '6':
        conditions = ICING_CONDITIONS
    else:
        return ''
    #Create list of split items (type, floor, height)
    split = []
    for item in turbice:
        if len(item) == 6:
            split.append([item[1:2], item[2:5], item[5:6]])
    #Combine items that cover a layer greater than 9000ft
    for i in reversed(range(len(split) - 1)):
        if split[i][2] == '9' and split[i][0] == split[i + 1][0] \
            and int(split[i + 1][1]) == (int(split[i][1]) + int(split[i][2]) * 10):
            split[i][2] = str(int(split[i][2]) + int(split[i + 1][2]))
            split.pop(i + 1)
    #Return joined, formatted string from split items
    return ', '.join(['{conditions} from {low_alt}{unit} to {high_alt}{unit}'.format(
        conditions=conditions[item[0]], low_alt=int(item[1]) * 100,
        high_alt=int(item[1]) * 100 + int(item[2]) * 1000, unit=unit) for item in split])


def min_max_temp(temp: str, unit: str='C') -> str:
    """Format the Min and Max temp elemets into a readable string
    Ex: Maximum temperature of 23C (73F) at 18-15:00Z
    """
    if not temp or len(temp) < 7:
        return ''
    if temp[:2] == 'TX':
        temp_type = 'Maximum'
    elif temp[:2] == 'TN':
        temp_type = 'Minimum'
    else:
        return ''
    temp = temp[2:].replace('M', '-').replace('Z', '').split('/')
    if len(temp[1]) > 2:
        temp[1] = temp[1][:2] + '-' + temp[1][2:]
    return '{temp_type} temperature of {temp} at {time}:00Z'.format(
        temp_type=temp_type, temp=temperature(temp[0], unit), time=temp[1])


def shared(wxdata: [str], units: {str: str}) -> {str: str}:
    """Translate Visibility, Altimeter, Clouds, and Other"""
    translations = {}
    translations['Visibility'] = visibility(wxdata['Visibility'], units['Visibility'])
    translations['Altimeter'] = altimeter(wxdata['Altimeter'], units['Altimeter'])
    translations['Clouds'] = clouds(wxdata['Cloud-List'], units['Altitude'])
    translations['Other'] = other_list(wxdata['Other-List'])
    return translations


def metar(wxdata: [str]) -> {str: str}:
    """Translate the results of metar.parse
    Keys: Wind, Visibility, Clouds, Temperature, Dewpoint, Altimeter, Other
    """
    units = wxdata['Units']
    translations = shared(wxdata, units)
    translations['Wind'] = wind(wxdata['Wind-Direction'], wxdata['Wind-Speed'],
                                wxdata['Wind-Gust'], wxdata['Wind-Variable-Dir'],
                                units['Wind-Speed'])
    translations['Temperature'] = temperature(wxdata['Temperature'], units['Temperature'])
    translations['Dewpoint'] = temperature(wxdata['Dewpoint'], units['Temperature'])
    return translations


def taf(wxdata: [str]) -> {str: str}:
    """Translate the results of taf.parse
    Keys: Forecast, Min-Temp, Max-Temp
    Forecast keys: Wind, Visibility, Clouds, Altimeter, Wind-Shear, Turbulance, Icing, Other
    """
    translations = {'Forecast': []}
    units = wxdata['Units']
    for line in wxdata['Forecast']:
        trans = shared(line, units)
        trans['Wind'] = wind(line['Wind-Direction'], line['Wind-Speed'],
                             line['Wind-Gust'], unit=units['Wind-Speed'])
        trans['Wind-Shear'] = wind_shear(line['Wind-Shear'],
                                         wxdata['Units']['Altitude'],
                                         units['Wind-Speed'])
        trans['Turbulance'] = turb_ice(line['Turb-List'], units['Altitude'])
        trans['Icing'] = turb_ice(line['Icing-List'], units['Altitude'])
        translations['Forecast'].append(trans)
    translations['Min-Temp'] = min_max_temp(wxdata['Min-Temp'], units['Temperature'])
    translations['Max-Temp'] = min_max_temp(wxdata['Max-Temp'], units['Temperature'])
    return translations
