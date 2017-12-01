"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/core.py

Contains the core parsing and indent functions of avwx
"""

# stdlib
from copy import copy
from itertools import permutations
# module
from avwx.exceptions import BadStation
from avwx.static import CLOUD_LIST, CLOUD_TRANSLATIONS, METAR_RMK, \
    NA_REGIONS, IN_REGIONS, M_NA_REGIONS, M_IN_REGIONS, FLIGHT_RULES


def valid_station(station: str):
    """Checks the validity of station ident and aises BadStation exception if needed
    This function doesn't return anything. It merely raises a BadStation error if needed
    """
    station = station.strip()
    if len(station) != 4:
        raise BadStation('ICAO station idents must be four characters long')
    uses_na_format(station)


def uses_na_format(station: str) -> bool:
    """Returns True if the station uses the North American format,
    False if the International format
    """
    if station[0] in NA_REGIONS:
        return True
    elif station[0] in IN_REGIONS:
        return False
    elif station[:2] in M_NA_REGIONS:
        return True
    elif station[:2] in M_IN_REGIONS:
        return False
    raise BadStation("Station doesn't start with a recognized character set")


def is_unknown(val: str) -> bool:
    """Returns True if val contains only '/' characters"""
    return val == '/' * len(val)


def find_first_in_list(txt: str, str_list: [str]) -> int:
    """Returns the index of the earliest occurence of an item from a list in a string
    Ex: find_first_in_list('foobar', ['bar', 'fin']) -> 3
    """
    start = len(txt) + 1
    for item in str_list:
        if start > txt.find(item) > -1:
            start = txt.find(item)
    return start if len(txt) + 1 > start > -1 else -1


def get_remarks(txt) -> ([str], str):
    """Returns the report split into components and the remarks string
    Remarks can include items like RMK and on, NOSIG and on, and BECMG and on
    """
    txt = txt.replace('?', '').strip(' ')
    # First look for Altimeter in txt
    alt_index = len(txt) + 1
    for item in [' A2', ' A3', ' Q1', ' Q0', ' Q9']:
        index = txt.find(item)
        if len(txt) - 6 > index > -1 and txt[index + 2:index + 6].isdigit():
            alt_index = index
    # Then look for earliest remarks 'signifier'
    sig_index = find_first_in_list(txt, METAR_RMK)
    if sig_index == -1:
        sig_index = len(txt) + 1
    if sig_index > alt_index > -1:
        return txt[:alt_index + 6].strip().split(' '), txt[alt_index + 7:]
    elif alt_index > sig_index > -1:
        return txt[:sig_index].strip().split(' '), txt[sig_index + 1:]
    return txt.strip().split(' '), ''


STR_REPL = {' C A V O K ': ' CAVOK ', '?': ' '}


def sanitize_report_string(txt: str) -> str:
    """Provides sanitization for operations that work better when the report is a string
    Returns the first pass sanitized report string
    """
    if len(txt) < 4:
        return txt
    # Prevent changes to station ID
    stid, txt = txt[:4], txt[4:]
    # Replace invalid key-value pairs
    for key, rep in STR_REPL.items():
        txt = txt.replace(key, rep)
    # Check for missing spaces in front of cloud layers
    # Ex: TSFEW004SCT012FEW///CBBKN080
    for cloud in CLOUD_LIST:
        if cloud in txt and ' ' + cloud not in txt:
            start, counter = 0, 0
            while txt.count(cloud) != txt.count(' ' + cloud):
                cloud_index = start + txt[start:].find(cloud)
                if len(txt[cloud_index:]) >= 3:
                    target = txt[cloud_index + len(cloud):cloud_index + len(cloud) + 3]
                    if target.isdigit() or not target.strip('/'):
                        txt = txt[:cloud_index] + ' ' + txt[cloud_index:]
                start = cloud_index + len(cloud) + 1
                # Prevent infinite loops
                if counter > txt.count(cloud):
                    break
                counter += 1
    return stid + txt


LINE_FIXES = {'TEMP0': 'TEMPO', 'TEMP O': 'TEMPO', 'TMPO': 'TEMPO', 'TE MPO': 'TEMPO',
              'TEMP ': 'TEMPO ', ' EMPO': ' TEMPO', 'TEMO': 'TEMPO', 'T EMPO': 'TEMPO',
              'BECM G': 'BECMG', 'BEMCG': 'BECMG', 'BE CMG': 'BECMG', 'BEMG': 'BECMG',
              ' BEC ': ' BECMG ', 'BCEMG': 'BECMG', 'B ECMG': 'BECMG'}


def sanitize_line(txt: str) -> str:
    """Fixes common mistakes with 'new line' signifiers so that they can be recognized"""
    for key in LINE_FIXES:
        index = txt.find(key)
        if index > -1:
            txt = txt[:index] + LINE_FIXES[key] + txt[index + len(key):]
    #Fix when space is missing following new line signifiers
    for item in ['BECMG', 'TEMPO']:
        if item in txt and item + ' ' not in txt:
            index = txt.find(item) + len(item)
            txt = txt[:index] + ' ' + txt[index:]
    return txt


def extra_space_exists(str1: str, str2: str) -> bool:
    """Return True if a space shouldn't exist between two items"""
    ls1, ls2 = len(str1), len(str2)
    if str1.isdigit():
        # 10 SM
        if str2 in ['SM', '0SM']:
            return True
        # 12 /10
        if ls2 > 2 and str2[0] == '/' and str2[1:].isdigit():
            return True
    if str2.isdigit():
        # OVC 040
        if str1 in CLOUD_LIST:
            return True
        # 12/ 10
        if ls1 > 2 and str1.endswith('/') and str1[:-1].isdigit():
            return True
        # 12/1 0
        if ls2 == 1 and ls1 > 3 and str1[:2].isdigit() and '/' not in str1 and str1[3:].isdigit():
            return True
        # Q 1001
        if str1 in ['Q', 'A']:
            return True
    # 36010G20 KT
    if str2 == 'KT' and str1[-1].isdigit() \
        and (str1[:5].isdigit() or (str1.startswith('VRB') and str1[3:5].isdigit())):
        return True
    # 36010K T
    if str2 == 'T' and ls1 == 6 \
        and (str1[:5].isdigit() or (str1.startswith('VRB') and str1[3:5].isdigit())) and str1[5] == 'K':
        return True
    # OVC022 CB
    if str2 in CLOUD_TRANSLATIONS and str2 not in CLOUD_LIST and ls1 >= 3 and str1[:3] in CLOUD_LIST:
        return True
    # FM 122400
    if str1 in ['FM', 'TL'] and (str2.isdigit() or (str2.endswith('Z') and str2[:-1].isdigit())):
        return True
    # TX 20/10
    if str1 in ['TX', 'TN'] and str2.find('/') != -1:
        return True
    return False


ITEM_REMV = ['AUTO', 'COR', 'NSC', 'NCD', '$', 'KT', 'M', '.', 'RTD', 'SPECI', 'METAR', 'CORR']
ITEM_REPL = {'CALM': '00000KT'}
VIS_PERMUTATIONS = [''.join(p) for p in permutations('P6SM')]
VIS_PERMUTATIONS.remove('6MPS')


def sanitize_report_list(wxdata: [str], remove_clr_and_skc: bool=True) -> ([str], [str], str):
    """Sanitize wxData
    We can remove and identify "one-off" elements and fix other issues before parsing a line
    We also return the runway visibility and wind shear since they are very easy to recognize
    and their location in the report is non-standard
    """
    shear = ''
    runway_vis = []
    for i, item in reversed(list(enumerate(wxdata))):
        ilen = len(item)
        # Remove elements containing only '/'
        if is_unknown(item):
            wxdata.pop(i)
        # Identify Runway Visibility
        elif ilen > 4 and item[0] == 'R' \
            and (item[3] == '/' or item[4] == '/') and item[1:3].isdigit():
            runway_vis.append(wxdata.pop(i))
        # Remove RE from wx codes, REVCTS -> VCTS
        elif ilen in [4, 6] and item.startswith('RE'):
            wxdata[i] = item[2:]
        # Fix a slew of easily identifiable conditions where a space does not belong
        elif i and extra_space_exists(wxdata[i - 1], item):
            wxdata[i - 1] += wxdata.pop(i)
        # Remove spurious elements
        elif item in ITEM_REMV:
            wxdata.pop(i)
        # Remove 'Sky Clear' from METAR but not TAF
        elif remove_clr_and_skc and item in ['CLR', 'SKC']:
            wxdata.pop(i)
        # Replace certain items
        elif item in ITEM_REPL:
            wxdata[i] = ITEM_REPL[item]
        # Remove ammend signifier from start of report ('CCA', 'CCB',etc)
        elif ilen == 3 and item.startswith('CC') and item[2].isalpha():
            wxdata.pop(i)
        # Identify Wind Shear
        elif ilen > 6 and item.startswith('WS') and item[5] == '/':
            shear = wxdata.pop(i).replace('KT', '')
        # Fix inconsistant 'P6SM' Ex: TP6SM or 6PSM -> P6SM
        elif ilen > 3 and item[-4:] in VIS_PERMUTATIONS:
            wxdata[i] = 'P6SM'
        # Fix wind T
        elif (ilen == 6 and item[5] in ['K', 'T'] and (item[:5].isdigit() or item.startswith('VRB'))) \
            or (ilen == 9 and item[8] in ['K', 'T'] and item[5] == 'G' and (item[:5].isdigit() or item.startswith('VRB'))):
            wxdata[i] = item[:-1] + 'KT'
        # Fix joined TX-TN
        elif ilen > 16 and len(item.split('/')) == 3:
            if item.startswith('TX') and 'TN' not in item:
                tn_index = item.find('TN')
                wxdata.insert(i + 1, item[:tn_index])
                wxdata[i] = item[tn_index:]
            elif item.startswith('TN') and item.find('TX') != -1:
                tx_index = item.find('TX')
                wxdata.insert(i + 1, item[:tx_index])
                wxdata[i] = item[tx_index:]
    return wxdata, runway_vis, shear


def is_not_tempo_or_prob(report_type: str) -> bool:
    """Returns True if report type is TEMPO or PROB__"""
    return report_type != 'TEMPO' and not (len(report_type) == 6 and report_type.startswith('PROB'))


def get_altimeter(wxdata: [str], units: {str: str}, version: str='NA') -> ([str], {str: str}, str):
    """Returns the report list and the removed altimeter item
    Version is 'NA' (North American / default) or 'IN' (International)
    """
    if not wxdata:
        return wxdata, units, ''
    altimeter = ''
    if version == 'NA':
        if wxdata[-1][0] == 'A':
            altimeter = wxdata.pop()[1:]
        elif wxdata[-1][0] == 'Q':
            units['Altimeter'] = 'hPa'
            altimeter = wxdata.pop()[1:].lstrip('.')
        elif len(wxdata[-1]) == 4 and wxdata[-1].isdigit():
            altimeter = wxdata.pop()
    elif version == 'IN':
        if wxdata[-1][0] == 'Q':
            altimeter = wxdata.pop()[1:].lstrip('.')
            if altimeter.find('/') != -1:
                altimeter = altimeter[:altimeter.find('/')]
        elif wxdata[-1][0] == 'A':
            units['Altimeter'] = 'inHg'
            altimeter = wxdata.pop()[1:]
    #Some stations report both, but we only need one
    if wxdata and (wxdata[-1][0] == 'A' or wxdata[-1][0] == 'Q'):
        wxdata.pop()
    return wxdata, units, altimeter


def get_taf_alt_ice_turb(wxdata: [str]) -> ([str], str, [str], [str]):
    """Returns the report list and removed: Altimeter string, Icing list, Turbulance list
    """
    altimeter = ''
    icing, turbulence = [], []
    for i, item in reversed(list(enumerate(wxdata))):
        if len(item) > 6 and item.startswith('QNH') and item[3:7].isdigit():
            altimeter = wxdata.pop(i)[3:7]
        elif item.isdigit():
            if item[0] == '6':
                icing.append(wxdata.pop(i))
            elif item[0] == '5':
                turbulence.append(wxdata.pop(i))
    return wxdata, altimeter, icing, turbulence


def is_possible_temp(temp: str) -> bool:
    """Returns True if all characters are digits or 'M' (for minus)"""
    for char in temp:
        if not (char.isdigit() or char == 'M'):
            return False
    return True


def get_temp_and_dew(wxdata: str) -> ([str], str, str):
    """Returns the report list and removed temperature and dewpoint strings"""
    for i, item in reversed(list(enumerate(wxdata))):
        if '/' in item:
            #///07
            if item[0] == '/':
                item = '/' + item.strip('/')
            #07///
            elif item[-1] == '/':
                item = item.strip('/') + '/'
            tempdew = item.split('/')
            if len(tempdew) != 2:
                continue
            valid = True
            for j, temp in enumerate(tempdew):
                if temp in ['MM', 'XX']:
                    tempdew[j] = ''
                elif not is_possible_temp(temp):
                    valid = False
                    break
            if valid:
                wxdata.pop(i)
                return wxdata, tempdew[0], tempdew[1]
    return wxdata, '', ''


def get_station_and_time(wxdata: [str]) -> ([str], str, str):
    """Returns the report list and removed station ident and time strings"""
    station = wxdata.pop(0)
    if wxdata and wxdata[0].endswith('Z') and wxdata[0][:-1].isdigit():
        rtime = wxdata.pop(0)
    elif wxdata and len(wxdata[0]) == 6 and wxdata[0].isdigit():
        rtime = wxdata.pop(0) + 'Z'
    else:
        rtime = ''
    return wxdata, station, rtime


def get_wind(wxdata: [str], units: {str: str}) -> ([str], {str: str}, str, str, str, [str]):
    """Returns the report list and removed:
    Direction string, speed string, gust string, variable direction list"""
    direction, speed, gust = '', '', ''
    variable = []
    if wxdata:
        item = copy(wxdata[0])
        for rep in ['(E)']:
            item = item.replace(rep, '')
        item = item.replace('O', '0')
        #09010KT, 09010G15KT
        if item.endswith('KT') \
            or item.endswith('KTS') \
            or item.endswith('MPS') \
            or item.endswith('KMH') \
            or ((len(item) == 5 or (len(item) >= 8 and item.find('G') != -1) and item.find('/') == -1)
            and (item[:5].isdigit() or (item.startswith('VRB') and item[3:5].isdigit()))):
            #In order of frequency
            if item.endswith('KT'):
                item = item.replace('KT', '')
            elif item.endswith('KTS'):
                item = item.replace('KTS', '')
            elif item.endswith('MPS'):
                units['Wind-Speed'] = 'm/s'
                item = item.replace('MPS', '')
            elif item.endswith('KMH'):
                units['Wind-Speed'] = 'km/h'
                item = item.replace('KMH', '')
            direction = item[:3]
            if 'G' in item:
                g_index = item.find('G')
                gust = item[g_index + 1:]
                speed = item[3:g_index]
            else:
                speed = item[3:]
            wxdata.pop(0)
        # elif len(item) > 5 and item[3] == '/' and item[:3].isdigit() and item[4:6].isdigit():
        #     direction = item[:3]
        #     if item.find('G') != -1:
        #         print('Found second G: {0}'.format(item))
        #         gIndex = item.find('G')
        #         gust = item[gIndex+1:gIndex+3]
        #         speed = item[4:item.find('G')]
        #     else:
        #         speed = item[4:]
        #     wxdata.pop(0)
    #Separated Gust
    if wxdata and 1 < len(wxdata[0]) < 4 and wxdata[0][0] == 'G' and wxdata[0][1:].isdigit():
        gust = wxdata.pop(0)[1:]
    #Variable Wind Direction
    if wxdata and len(wxdata[0]) == 7 and wxdata[0][:3].isdigit() \
        and wxdata[0][3] == 'V' and wxdata[0][4:].isdigit():
        variable = wxdata.pop(0).split('V')
    return wxdata, units, direction, speed, gust, variable


def get_visibility(wxdata: [str], units: {str: str}) -> ([str], {str: str}, str):
    """Returns the report list and removed visibility string"""
    visibility = ''
    if wxdata:
        item = copy(wxdata[0])
        # Vis reported in statue miles
        if item.endswith('SM'):  # 10SM
            if item == 'P6SM':
                visibility = 'P6'
            elif item == 'M1/4SM':
                visibility = 'M1/4'
            elif '/' not in item:
                visibility = str(int(item[:item.find('SM')]))
            else:
                visibility = item[:item.find('SM')]  # 1/2SM
            wxdata.pop(0)
            units['Visibility'] = 'sm'
        # Vis reported in meters
        elif len(item) == 4 and item.isdigit():
            visibility = wxdata.pop(0)
            units['Visibility'] = 'm'
        elif 7 >= len(item) >= 5 and item[:4].isdigit() \
            and (item[4] in ['M', 'N', 'S', 'E', 'W'] or item[4:] == 'NDV'):
            visibility = wxdata.pop(0)[:4]
            units['Visibility'] = 'm'
        elif len(item) == 5 and item[1:5].isdigit() and item[0] in ['M', 'P', 'B']:
            visibility = wxdata.pop(0)[1:5]
            units['Visibility'] = 'm'
        elif item.endswith('KM') and item[:item.find('KM')].isdigit():
            visibility = item[:item.find('KM')] + '000'
            wxdata.pop(0)
            units['Visibility'] = 'm'
        # Vis statute miles but split Ex: 2 1/2SM
        elif len(wxdata) > 1 and wxdata[1].endswith('SM') and '/' in wxdata[1] and item.isdigit():
            vis1 = wxdata.pop(0)  # 2
            vis2 = wxdata.pop(0).replace('SM', '')  # 1/2
            visibility = str(int(vis1) * int(vis2[2]) + int(vis2[0])) + vis2[1:]  # 5/2
            units['Visibility'] = 'sm'
    return wxdata, units, visibility


# TAF line report type and start/end times
def get_type_and_times(wxdata: [str]) -> ([str], str, str, str):
    """Returns the report list and removed:
    Report type string, start time string, end time string
    """
    report_type, start_time, end_time = 'BASE', '', ''
    #TEMPO, BECMG, INTER
    if wxdata and wxdata[0] in ['TEMPO', 'BECMG', 'INTER']:
        report_type = wxdata.pop(0)
    #PROB[30,40]
    elif wxdata and len(wxdata[0]) == 6 and wxdata[0].startswith('PROB'):
        report_type = wxdata.pop(0)
    #1200/1306
    if wxdata and len(wxdata[0]) == 9 and wxdata[0][4] == '/' \
        and wxdata[0][:4].isdigit() and wxdata[0][5:].isdigit():
        start_time, end_time = wxdata.pop(0).split('/')
    #FM120000
    elif wxdata and len(wxdata[0]) > 7 and wxdata[0].startswith('FM'):
        report_type = 'FROM'
        if '/' in wxdata[0] and wxdata[0][2:].split('/')[0].isdigit() \
            and wxdata[0][2:].split('/')[1].isdigit():
            start_time, end_time = wxdata.pop(0)[2:].split('/')
        elif wxdata[0][2:8].isdigit():
            start_time = wxdata.pop(0)[2:6]
        #TL120600
        if wxdata and len(wxdata[0]) > 7 and wxdata[0].startswith('TL') \
            and wxdata[0][2:8].isdigit():
            end_time = wxdata.pop(0)[2:6]
    return wxdata, report_type, start_time, end_time


def find_missing_taf_times(lines: [str]) -> [str]:
    """Fix any missing time issues (except for error/empty lines)"""
    last_fm_line = 0
    for i, line in enumerate(lines):
        if line['End-Time'] == '' and is_not_tempo_or_prob(line['Type']):
            last_fm_line = i
            if i < len(lines) - 1:
                for report in lines[i + 1:]:
                    if is_not_tempo_or_prob(report['Type']):
                        line['End-Time'] = report['Start-Time']
                        break
    #Special case for final forcast
    if last_fm_line > 0:
        lines[last_fm_line]['End-Time'] = lines[0]['End-Time']
    return lines


def get_temp_min_and_max(wxlist: [str]) -> ([str], str, str):
    """Pull out Max temp at time and Min temp at time items from wx list
    """
    temp_max, temp_min = '', ''
    for i, item in reversed(list(enumerate(wxlist))):
        if len(item) > 6 and item[0] == 'T' and '/' in item:
            # TX12/1316Z
            if item[1] == 'X':
                temp_max = wxlist.pop(i)
            # TNM03/1404Z
            elif item[1] == 'N':
                temp_min = wxlist.pop(i)
            # TM03/1404Z T12/1316Z -> Will fix TN/TX
            elif item[1] == 'M' or item[1].isdigit():
                if temp_min:
                    if int(temp_min[2:temp_min.find('/')].replace('M', '-')) \
                        > int(item[1:item.find('/')].replace('M', '-')):
                        temp_max = 'TX' + temp_min[2:]
                        temp_min = 'TN' + item[1:]
                    else:
                        temp_max = 'TX' + item[1:]
                else:
                    temp_min = 'TN' + item[1:]
                wxlist.pop(i)
    return wxlist, temp_max, temp_min


def get_digit_list(alist: [str], from_index: int) -> ([str], [str]):
    """Returns a list of items removed from a given list of strings
    that are all digits from 'from_index' until hitting a non-digit item
    """
    ret = []
    alist.pop(from_index)
    while len(alist) > from_index and alist[from_index].isdigit():
        ret.append(alist.pop(from_index))
    return alist, ret


def get_oceania_temp_and_alt(wxlist: [str]) -> ([str], [str], [str]):
    """Get Temperature and Altimeter lists for Oceania TAFs"""
    tlist, qlist = [], []
    if 'T' in wxlist:
        wxlist, tlist = get_digit_list(wxlist, wxlist.index('T'))
    if 'Q' in wxlist:
        wxlist, qlist = get_digit_list(wxlist, wxlist.index('Q'))
    return wxlist, tlist, qlist


def sanitize_cloud(cloud: str) -> str:
    """Fix rare cloud layer issues"""
    if len(cloud) < 4:
        return cloud
    if not cloud[3].isdigit() and cloud[3] != '/':
        if cloud[3] == 'O':
            cloud = cloud[:3] + '0' + cloud[4:]  # Bad "O": FEWO03 -> FEW003
        else:  # Move modifiers to end: BKNC015 -> BKN015C
            cloud = cloud[:3] + cloud[4:] + cloud[3]
    return cloud


def split_cloud(cloud: str, begins_with_vv: bool) -> [str]:
    """Transforms a cloud string into a list of strings: [Type, Height (, Optional Modifier)]"""
    split = []
    cloud = sanitize_cloud(cloud)
    if begins_with_vv:
        split.append(cloud[:2])
        cloud = cloud[2:]
    while len(cloud) >= 3:
        split.append(cloud[:3])
        cloud = cloud[3:]
    if cloud:
        split.append(cloud)
    if len(split) == 1:
        split.append('')
    return split


def get_clouds(wxdata: [str]) -> ([str], list):
    """Returns the report list and removed list of split cloud layers"""
    clouds = []
    for i, item in reversed(list(enumerate(wxdata))):
        if item[:3] in CLOUD_LIST:
            clouds.append(split_cloud(wxdata.pop(i), False))
        elif item[:2] == 'VV':
            clouds.append(split_cloud(wxdata.pop(i), True))
    return wxdata, sorted(clouds, key=lambda pair: (pair[1], pair[0]))


def get_flight_rules(vis: str, cloud: [str]) -> int:
    """Returns int based on current flight rules from parsed METAR data
    0=VFR, 1=MVFR, 2=IFR, 3=LIFR
    Note: Common practice is to report IFR if visibility unavailable
    """
    # Parse visibility
    if not vis or is_unknown(vis):
        return 2
    elif vis == 'P6':
        vis = 10
    elif '/' in vis:
        vis = 0 if vis[0] == 'M' else int(vis.split('/')[0]) / int(vis.split('/')[1])
    # Convert meters to miles
    elif len(vis) == 4 and vis.isdigit():
        vis = int(vis) * 0.000621371
    else:
        vis = int(vis)
    # Parse ceiling
    cld = int(cloud[1]) if cloud else 99
    # Determine flight rules
    if (vis <= 5) or (cld <= 30):
        if (vis < 3) or (cld < 10):
            if (vis < 1) or (cld < 5):
                return 3  # LIFR
            return 2  # IFR
        return 1  # MVFR
    return 0  # VFR


def get_taf_flight_rules(lines: [str]) -> [str]:
    """Get flight rules by looking for missing data in prior reports"""
    for i, line in enumerate(lines):
        temp_vis, temp_cloud = line['Visibility'], line['Cloud-List']
        for report in reversed(lines[:i]):
            if is_not_tempo_or_prob(report['Type']):
                if temp_vis == '':
                    temp_vis = report['Visibility']
                if 'SKC' in report['Other-List'] or 'CLR' in report['Other-List']:
                    temp_cloud = 'tempClear'
                elif temp_cloud == []:
                    temp_cloud = report['Cloud-List']
                if temp_vis != '' and temp_cloud != []:
                    break
        if temp_cloud == 'tempClear':
            temp_cloud = []
        line['Flight-Rules'] = FLIGHT_RULES[get_flight_rules(temp_vis, get_ceiling(temp_cloud))]
    return lines


def get_ceiling(clouds: [[str]]) -> [str]:
    """Returns list of ceiling layer from Cloud-List or None if none found
    Assumes that the clouds are already sorted lowest to highest
    Only 'Broken', 'Overcast', and 'Vertical Visibility' are considdered ceilings
    Prevents errors due to lack of cloud information (eg. '' or 'FEW///')
    """
    for cloud in clouds:
        if len(cloud) > 1 and cloud[1].isdigit() and cloud[0] in ['OVC', 'BKN', 'VV']:
            return cloud
    return None


def parse_remarks(rmk: str) -> {str: str}:
    """Finds temperature and dewpoint decimal values from the remarks"""
    rmkdata = {}
    for item in rmk.split(' '):
        if len(item) in [5, 9] and item[0] == 'T' and item[1:].isdigit():
            if item[1] == '1':
                rmkdata['Temp-Decimal'] = '-' + item[2].replace('0', '') + item[3] + '.' + item[4]
            elif item[1] == '0':
                rmkdata['Temp-Decimal'] = item[2].replace('0', '') + item[3] + '.' + item[4]
            if len(item) == 9:
                if item[5] == '1':
                    rmkdata['Dew-Decimal'] = '-' + item[6].replace('0', '') + item[7] + '.' + item[8]
                elif item[5] == '0':
                    rmkdata['Dew-Decimal'] = item[6].replace('0', '') + item[7] + '.' + item[8]
    return rmkdata
