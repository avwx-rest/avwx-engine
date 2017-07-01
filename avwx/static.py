"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/static.py

Contains static objects for internal and external use
"""

# NOAA ADDS API endpoint for METAR and TAF reports
REQUEST_URL = "https://aviationweather.gov/adds/dataserver_current/httpparam"+\
              "?dataSource={0}s&requestType=retrieve&format=XML&stationString={1}&hoursBeforeNow=2"

# Station Location Identifiers (first character)
NA_REGIONS = ['C', 'K', 'P', 'T']
IN_REGIONS = ['A', 'B', 'D', 'E', 'F', 'G', 'H', 'L', 'N', 'O', 'R', 'S', 'U', 'V', 'W', 'Y', 'Z']
# The Central American region is split. Therefore we need to use the first two letters
M_NA_REGIONS = ['MB', 'MM', 'MT', 'MY']
M_IN_REGIONS = ['MD', 'MG', 'MH', 'MK', 'MN', 'MP', 'MR', 'MS', 'MU', 'MW', 'MZ']

# North American variant units
NA_UNITS = {
    'Wind-Speed': 'kt',
    'Visibility': 'sm',
    'Altitude': 'ft',
    'Temperature': 'C',
    'Altimeter': 'inHg'
}
# International variant units
IN_UNITS = {
    'Wind-Speed': 'kt',
    'Visibility': 'm',
    'Altitude': 'ft',
    'Temperature': 'C',
    'Altimeter': 'hPa'
}

# List of flight rules abreviations
FLIGHT_RULES = ['VFR', 'MVFR', 'IFR', 'LIFR']

# List of cloud layer abreviations
CLOUD_LIST = ['FEW', 'SCT', 'BKN', 'OVC']

# Dictionary associating WX codes with descriptions
WX_TRANSLATIONS = {
    'BC': _('Patchy'),
    'BL': _('Blowing'),
    'BR': _('Mist'),
    'DS': _('Duststorm'),
    'DU': _('Wide Dust'),
    'DZ': _('Drizzle'),
    'FC': _('Funnel Cloud'),
    'FG': _('Fog'),
    'FU': _('Smoke'),
    'FZ': _('Freezing'),
    'GR': _('Hail'),
    'GS': _('Small Hail'),
    'HZ': _('Haze'),
    'IC': _('Ice Crystals'),
    'MI': _('Shallow'),
    'PL': _('Ice Pellets'),
    'PO': _('Dust Whirls'),
    'PR': _('Partial'),
    'RA': _('Rain'),
    'SA': _('Sand'),
    'SG': _('Snow Grains'),
    'SH': _('Showers'),
    'SN': _('Snow'),
    'SQ': _('Squall'),
    'SS': _('Sandstorm'),
    'SY': _('Spray'),
    'TS': _('Thunderstorm'),
    'UP': _('Unknown Precip'),
    'VA': _('Volcanic Ash'),
    'VC': _('Vicinity')
}

# Dictionary associating cloud layer and cloud codes with descriptions
CLOUD_TRANSLATIONS = {
    'OVC': _('Overcast layer at {0}{1}'),
    'BKN': _('Broken layer at {0}{1}'),
    'SCT': _('Scattered clouds at {0}{1}'),
    'FEW': _('Few clouds at {0}{1}'),
    'VV': _('Vertical visibility up to {0}{1}'),
    'CLR': _('Sky Clear'),
    'SKC': _('Sky Clear'),
    'AC': _('Altocumulus'),
    'ACC': _('Altocumulus Castellanus'),
    'AS': _('Altostratus'),
    'CB': _('Cumulonimbus'),
    'CC': _('Cirrocumulus'),
    'CI': _('Cirrus'),
    'CS': _('Cirrostratus'),
    'CU': _('Cumulus'),
    'FC': _('Fractocumulus'),
    'FS': _('Fractostratus'),
    'NS': _('Nimbostratus'),
    'SC': _('Stratocumulus'),
    'ST': _('Stratus'),
    'TCU': _('Towering Cumulus')
}

# Dictionary associating turbulance report IDs with descriptions
TURBULANCE_CONDITIONS = {
    '0': _('None'),
    '1': _('Light turbulence'),
    '2': _('Occasional moderate turbulence in clear air'),
    '3': _('Frequent moderate turbulence in clear air'),
    '4': _('Occasional moderate turbulence in clouds'),
    '5': _('Frequent moderate turbulence in clouds'),
    '6': _('Occasional severe turbulence in clear air'),
    '7': _('Frequent severe turbulence in clear air'),
    '8': _('Occasional severe turbulence in clouds'),
    '9': _('Frequent severe turbulence in clouds'),
    'X': _('Extreme turbulence')
}

# Dictionary associating icing report IDs with descriptions
ICING_CONDITIONS = {
    '0': _('No icing'),
    '1': _('Light icing'),
    '2': _('Light icing in clouds'),
    '3': _('Light icing in precipitation'),
    '4': _('Moderate icing'),
    '5': _('Moderate icing in clouds'),
    '6': _('Moderate icing in precipitation'),
    '7': _('Severe icing'),
    '8': _('Severe icing in clouds'),
    '9': _('Severe icing in precipitation')
}

# Strings signifying the start of the remarks section of a new TAF time period
METAR_RMK = [' BLU', ' BLU+', ' WHT', ' GRN', ' YLO', ' AMB', ' RED', ' BECMG', ' TEMPO',
             ' INTER', ' NOSIG', ' RMK', ' WIND', ' QFE', ' QFF', ' INFO', ' RWY', ' CHECK']
TAF_RMK = ['RMK ', 'AUTOMATED ', 'COR ', 'AMD ', 'LAST ', 'FCST ',
           'CANCEL ', 'CHECK ', 'WND ', 'MOD ', ' BY', ' QFE', ' QFF']
TAF_NEWLINE = [' INTER ', ' FM', ' BECMG ', ' TEMPO ']

# Units required to be translated in order to be spoken properly
SPOKEN_UNITS = {
    'sm': _('mile'),
    'km': _('kilometer'),
    'C': _('Celsius'),
    'F': _('Fahrenheit')
}

# Dictionary associating algebraic signs with their spoken version
NUMBER_REPL = {
    '.': _('point'),
    '-': _('minus'),
    'M': _('minus'),
    '0': _('zero'),
    '1': _('one'),
    '2': _('two'),
    '3': _('three'),
    '4': _('four'),
    '5': _('five'),
    '6': _('six'),
    '7': _('seven'),
    '8': _('eight'),
    '9': _('nine')
}

# Dictionary associating fraction strings with their spoken version
FRACTIONS = {
    '1/4': _('one quarter of a'),
    '1/2': _('one half'),
    '3/4': _('three quarters of a')
}