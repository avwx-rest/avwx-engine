"""Core static values for internal and external use.

METAR and TAF reports come in two variants depending on the station's
location: North American & International. This affects both element
parsing and inferred units of measurement. AVWX determines this by
looking at the station's ICAO value.
"""

NA_REGIONS = (
    "C",
    "K",
    "P",
    "T",
)
"""Station Location Identifiers - North American formatting"""

IN_REGIONS = (
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
)
"""Station Location Identifiers - International formatting"""

# The Central American region is split. Therefore we need to use the first two letters
M_NA_REGIONS = (
    "MB",
    "MM",
    "MT",
    "MY",
)
"""Central America Station Location Identifiers - North American formatting"""

M_IN_REGIONS = (
    "MD",
    "MG",
    "MH",
    "MK",
    "MN",
    "MP",
    "MR",
    "MS",
    "MU",
    "MW",
    "MZ",
)
"""Central America Station Location Identifiers - International formatting"""

NA_UNITS = {
    "altimeter": "inHg",
    "altitude": "ft",
    "accumulation": "in",
    "temperature": "C",
    "visibility": "sm",
    "wind_speed": "kt",
}
"""North American variant units"""

IN_UNITS = {
    "altimeter": "hPa",
    "altitude": "ft",
    "accumulation": "in",
    "temperature": "C",
    "visibility": "m",
    "wind_speed": "kt",
}
"""International variant units"""

WIND_UNITS = {
    "KT": "kt",
    "KTS": "kt",
    "MPS": "m/s",
    "KMH": "km/h",
    "MPH": "mi/h",
}
"""Expected unit postfixes for wind elements in order of frequency"""

FLIGHT_RULES = (
    "VFR",
    "MVFR",
    "IFR",
    "LIFR",
)
"""List of flight rules abbreviations"""

CLOUD_LIST = (
    "FEW",
    "SCT",
    "BKN",
    "OVC",
)
"""List of cloud layer abbreviations"""

CARDINALS = {
    "N": 360,
    "NORTH": 360,
    "NE": 45,
    "E": 90,
    "EAST": 90,
    "SE": 135,
    "S": 180,
    "SOUTH": 180,
    "SW": 225,
    "W": 270,
    "WEST": 270,
    "NW": 315,
}
"""Dictionary of cardinal direction values"""

CARDINAL_DEGREES = {
    "NNE": 22.5,
    "NE": 45,
    "ENE": 67.5,
    "E": 90,
    "ESE": 112.5,
    "SE": 135,
    "SSE": 157.5,
    "S": 180,
    "SSW": 202.5,
    "SW": 225,
    "WSW": 247.5,
    "W": 270,
    "WNW": 292.5,
    "NW": 315,
    "NNW": 337.5,
    "N": 0,
}
"""Dictionary of tertiary cardinal directions to degree values with North at 0"""

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
"""Dictionary associating WX codes with descriptions"""

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
    None: "Unknown",
}
"""Dictionary associating cloud layer and cloud codes with descriptions"""

SPOKEN_UNITS = {
    "sm": "mile",
    "mi": "mile",
    "km": "kilometer",
    "C": "Celsius",
    "F": "Fahrenheit",
    "kt": "knot",
}
"""Units required to be translated in order to be spoken properly"""

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
"""Dictionary associating algebraic signs with their spoken version"""

FRACTIONS = {"1/4": "one quarter", "1/2": "one half", "3/4": "three quarters"}
"""Dictionary associating fraction strings with their spoken version"""

SPECIAL_NUMBERS = {
    "CAVOK": (9999, "ceiling and visibility ok"),
    "VRB": (None, "variable"),
    "CLM": (0, "calm"),
    "SFC": (0, "surface"),
    "GND": (0, "ground"),
    "STNR": (0, "stationary"),
    "LTL": (0, "little"),
    "FRZLVL": (None, "freezing level"),
    "UNL": (999, "Unlimited"),
}
"""Dictionary associating special number values with their spoken version"""

REMARKS_ELEMENTS = {
    "$": "ASOS requires maintenance",
    "AO1": "Automated with no precipitation sensor",
    "AO2": "Automated with precipitation sensor",
    "ADVISORY": "Advisory only. Do not use for flight planning",
    "BINOVC": "Breaks in Overcast",
    "FZRANO": "Freezing rain information not available",
    "NOSPECI": "No SPECI reports taken",
    "P0000": "Trace amount of rain in the last hour",
    "PNO": "Precipitation amount not available",
    "PRESFR": "Pressure Falling Rapidly",
    "PRESRR": "Pressure Rising Rapidly",
    "PWINO": "Precipitation identifier information not available",
    "RVRNO": "Runway Visual Range missing",
    "SLPNO": "Sea level pressure not available",
    "SOG": "Snow on the ground",
    "TSNO": "Thunderstorm information not available",
}
"""Static remarks translation elements"""

REMARKS_GROUPS = {"ACFT MSHP": "Aircraft mishap"}
"""Static remarks translation groups"""
