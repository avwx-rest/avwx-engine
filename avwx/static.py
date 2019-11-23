"""
Contains static objects for internal and external use
"""

#: Station Location Identifiers - North American formatting
NA_REGIONS = ["C", "K", "P", "T"]
#: Station Location Identifiers - International formatting
IN_REGIONS = [
    "A",
    "B",
    "D",
    "E",
    "F",
    "G",
    "H",
    "L",
    "N",
    "O",
    "R",
    "S",
    "U",
    "V",
    "W",
    "Y",
    "Z",
]

# The Central American region is split. Therefore we need to use the first two letters
#: Central America Station Location Identifiers - North American formatting
M_NA_REGIONS = ["MB", "MM", "MT", "MY"]
#: Central America Station Location Identifiers - International formatting
M_IN_REGIONS = ["MD", "MG", "MH", "MK", "MN", "MP", "MR", "MS", "MU", "MW", "MZ"]

#: North American variant units
NA_UNITS = {
    "altimeter": "inHg",
    "altitude": "ft",
    "temperature": "C",
    "visibility": "sm",
    "wind_speed": "kt",
}
#: International variant units
IN_UNITS = {
    "altimeter": "hPa",
    "altitude": "ft",
    "temperature": "C",
    "visibility": "m",
    "wind_speed": "kt",
}

#: List of flight rules abbreviations
FLIGHT_RULES = ["VFR", "MVFR", "IFR", "LIFR"]

#: List of cloud layer abbreviations
CLOUD_LIST = ["FEW", "SCT", "BKN", "OVC"]

#: Dictionary of cardinal direction values
CARDINALS = {
    "N": 360,
    "NE": 45,
    "E": 90,
    "SE": 135,
    "S": 180,
    "SW": 225,
    "W": 270,
    "NW": 315,
}

#: Dictionary associating WX codes with descriptions
WX_TRANSLATIONS = {
    "BC": "Patchy",
    "BL": "Blowing",
    "BR": "Mist",
    "DR": "Low Drifting",
    "DS": "Duststorm",
    "DU": "Wide Dust",
    "DZ": "Drizzle",
    "FC": "Funnel Cloud",
    "FG": "Fog",
    "FU": "Smoke",
    "FZ": "Freezing",
    "GR": "Hail",
    "GS": "Small Hail",
    "HZ": "Haze",
    "IC": "Ice Crystals",
    "MI": "Shallow",
    "PL": "Ice Pellets",
    "PO": "Dust Whirls",
    "PR": "Partial",
    "PY": "Spray",
    "RA": "Rain",
    "SA": "Sand",
    "SG": "Snow Grains",
    "SH": "Showers",
    "SN": "Snow",
    "SQ": "Squall",
    "SS": "Sandstorm",
    "SY": "Spray",
    "TS": "Thunderstorm",
    "UP": "Unknown Precip",
    "VA": "Volcanic Ash",
    "VC": "Vicinity",
}

#: Dictionary associating cloud layer and cloud codes with descriptions
CLOUD_TRANSLATIONS = {
    "OVC": "Overcast layer at {0}{1}",
    "BKN": "Broken layer at {0}{1}",
    "SCT": "Scattered clouds at {0}{1}",
    "FEW": "Few clouds at {0}{1}",
    "VV": "Vertical visibility up to {0}{1}",
    "CLR": "Sky Clear",
    "SKC": "Sky Clear",
    "AC": "Altocumulus",
    "ACC": "Altocumulus Castellanus",
    "AS": "Altostratus",
    "CB": "Cumulonimbus",
    "CC": "Cirrocumulus",
    "CI": "Cirrus",
    "CS": "Cirrostratus",
    "CU": "Cumulus",
    "FC": "Fractocumulus",
    "FS": "Fractostratus",
    "NS": "Nimbostratus",
    "SC": "Stratocumulus",
    "ST": "Stratus",
    "TCU": "Towering Cumulus",
}

#: Dictionary associating turbulence report IDs with descriptions
TURBULENCE_CONDITIONS = {
    "0": "None",
    "1": "Light turbulence",
    "2": "Occasional moderate turbulence in clear air",
    "3": "Frequent moderate turbulence in clear air",
    "4": "Occasional moderate turbulence in clouds",
    "5": "Frequent moderate turbulence in clouds",
    "6": "Occasional severe turbulence in clear air",
    "7": "Frequent severe turbulence in clear air",
    "8": "Occasional severe turbulence in clouds",
    "9": "Frequent severe turbulence in clouds",
    "X": "Extreme turbulence",
}

#: Dictionary associating icing report IDs with descriptions
ICING_CONDITIONS = {
    "0": "No icing",
    "1": "Light icing",
    "2": "Light icing in clouds",
    "3": "Light icing in precipitation",
    "4": "Moderate icing",
    "5": "Moderate icing in clouds",
    "6": "Moderate icing in precipitation",
    "7": "Severe icing",
    "8": "Severe icing in clouds",
    "9": "Severe icing in precipitation",
}

#: Dictionary associating pressure change IDs with descriptions
PRESSURE_TENDENCIES = {
    "0": "Increasing, then decreasing",
    "1": "Increasing, then steady",
    "2": "Increasing steadily or unsteadily",
    "3": "Decreasing or steady, then increasing",
    "4": "Steady",
    "5": "Decreasing, then increasing",
    "6": "Decreasing, then steady",
    "7": "Decreasing steadily or unsteadily",
    "8": "Steady or increasing, then decreasing",
    "9": "Unknown",
}

#: Strings signifying the start of the remarks section of a METAR
METAR_RMK = [
    " BLU",
    " BLU+",
    " WHT",
    " GRN",
    " YLO",
    " AMB",
    " RED",
    " ALL",
    " BECMG",
    " TEMPO",
    " INTER",
    " NOSIG",
    " RMK",
    " WIND",
    " QFE",
    " QFF",
    " INFO",
    " RWY",
    " CHECK",
]
#: Strings signifying the start of the remarks section of a TAF
TAF_RMK = [
    "RMK ",
    "AUTOMATED ",
    "COR ",
    "AMD ",
    "LAST ",
    "FCST ",
    "CANCEL ",
    "CHECK ",
    "WND ",
    "MOD ",
    " BY",
    " QFE",
    " QFF",
]
#: Strings signifying the start of a new TAF time period
TAF_NEWLINE = ["INTER", "BECMG", "TEMPO"]
#: Addendum to TAF_NEWLINE but string startswith and the rest are only digits
TAF_NEWLINE_STARTSWITH = ["FM", "PROB"]

#: Units required to be translated in order to be spoken properly
SPOKEN_UNITS = {"sm": "mile", "km": "kilometer", "C": "Celsius", "F": "Fahrenheit"}

#: Dictionary associating algebraic signs with their spoken version
NUMBER_REPL = {
    ".": "point",
    "-": "minus",
    "M": "minus",
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}

#: Dictionary associating fraction strings with their spoken version
FRACTIONS = {"1/4": "one quarter", "1/2": "one half", "3/4": "three quarters"}

#: Dictionary associating special number values with their spoken version
SPECIAL_NUMBERS = {
    "CAVOK": (9999, "ceiling and visibility ok"),
    "M1/4": (None, "less than one quarter"),
    "M1/4SM": (None, "less than one quarter"),
    "M1/8": (None, "less than one eighth"),
    "M1/8SM": (None, "less than one eighth"),
    "P49": (None, "greater than four nine"),
    "P6": (None, "greater than six"),
    "P6SM": (None, "greater than six"),
    "P99": (None, "greater than nine nine"),
    "VRB": (None, "variable"),
}

#: Static remarks translation elements
REMARKS_ELEMENTS = {
    "$": "ASOS requires maintenance",
    "AO1": "Automated with no precipitation sensor",
    "AO2": "Automated with precipitation sensor",
    "BINOVC": "Breaks in Overcast",
    "FZRANO": "Freezing rain information not available",
    "NOSPECI": "No SPECI reports taken",
    "P0000": "Trace amount of rain in the last hour",
    "PNO": "Precipitation amount not available",
    "PRESFR": "Pressure Falling Rapidly",
    "PRESRR": "Pressure Rising Rapidly",
    "PWINO": "Precipitation identifier information not available",
    "RVRNO": "Runway Visual Range missing",
    "SOG": "Snow on the ground",
    "TSNO": "Thunderstorm information not available",
}

#: Static remarks translation groups
REMARKS_GROUPS = {" ACFT MSHP ": "Aircraft mishap"}
