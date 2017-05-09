FLIGHT_RULES = ['VFR', 'MVFR', 'IFR', 'LIFR']
CLOUD_LIST = ['FEW', 'SCT', 'BKN', 'OVC']
WX_TRANSLATIONS = {
    'BC': 'Patchy',
    'BL': 'Blowing',
    'BR': 'Mist',
    'DS': 'Duststorm',
    'DU': 'Wide Dust',
    'DZ': 'Drizzle',
    'FC': 'Funnel Cloud',
    'FG': 'Fog',
    'FU': 'Smoke',
    'FZ': 'Freezing',
    'GR': 'Hail',
    'GS': 'Small Hail',
    'HZ': 'Haze',
    'IC': 'Ice Crystals',
    'MI': 'Shallow',
    'PL': 'Ice Pellets',
    'PO': 'Dust Whirls',
    'PR': 'Partial',
    'RA': 'Rain',
    'SA': 'Sand',
    'SG': 'Snow Grains',
    'SH': 'Showers',
    'SN': 'Snow',
    'SQ': 'Squall',
    'SS': 'Sandstorm',
    'SY': 'Spray',
    'TS': 'Thunderstorm',
    'UP': 'Unknown Precip',
    'VA': 'Volcanic Ash',
    'VC': 'Vicinity'
}

# Station Location Identifiers
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

CLOUD_TRANSLATIONS = {
    'OVC': 'Overcast layer at {0}{1}',
    'BKN': 'Broken layer at {0}{1}',
    'SCT': 'Scattered clouds at {0}{1}',
    'FEW': 'Few clouds at {0}{1}',
    'VV': 'Vertical visibility up to {0}{1}',
    'CLR': 'Sky Clear',
    'SKC': 'Sky Clear',
    'AC': 'Altocumulus',
    'ACC': 'Altocumulus Castellanus',
    'AS': 'Altostratus',
    'CB': 'Cumulonimbus',
    'CC': 'Cirrocumulus',
    'CI': 'Cirrus',
    'CS': 'Cirrostratus',
    'CU': 'Cumulus',
    'FC': 'Fractocumulus',
    'FS': 'Fractostratus',
    'NS': 'Nimbostratus',
    'SC': 'Stratocumulus',
    'ST': 'Stratus',
    'TCU': 'Towering Cumulus'
}

METAR_RMK = [' BLU', ' BLU+', ' WHT', ' GRN', ' YLO', ' AMB', ' RED', ' BECMG', ' TEMPO',
             ' INTER', ' NOSIG', ' RMK', ' WIND', ' QFE', ' QFF', ' INFO', ' RWY', ' CHECK']

REQUEST_URL = """https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource={0}s&requestType=retrieve&format=XML&stationString={1}&hoursBeforeNow=2"""

TURBULANCE_CONDITIONS = {
    '0': 'None',
    '1': 'Light turbulence',
    '2': 'Occasional moderate turbulence in clear air',
    '3': 'Frequent moderate turbulence in clear air',
    '4': 'Occasional moderate turbulence in clouds',
    '5': 'Frequent moderate turbulence in clouds',
    '6': 'Occasional severe turbulence in clear air',
    '7': 'Frequent severe turbulence in clear air',
    '8': 'Occasional severe turbulence in clouds',
    '9': 'Frequent severe turbulence in clouds',
    'X': 'Extreme turbulence'
}

ICING_CONDITIONS = {
    '0': 'No icing',
    '1': 'Light icing',
    '2': 'Light icing in clouds',
    '3': 'Light icing in precipitation',
    '4': 'Moderate icing',
    '5': 'Moderate icing in clouds',
    '6': 'Moderate icing in precipitation',
    '7': 'Severe icing',
    '8': 'Severe icing in clouds',
    '9': 'Severe icing in precipitation'
}