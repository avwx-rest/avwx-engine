"""
AIRMET / SIGMET static vales
"""

AIRMET_KEY = "airmet"

BULLETIN_TYPES = {
    "WS": "sigmet",
    "WV": "volcanic ash",
    "WC": "tropical cyclone",
    "WA": AIRMET_KEY,
}

INTENSITY = {
    "NC": "No change",
    "INTSF": "Intensifying",
    "WKN": "Weakening",
}

# More to less specific when overlapping
WEATHER_TYPES = {
    "DMSHG LINE TS": "Diminishing line of thunderstorms",
    "AREA TS": "Thunderstorms in the area",
    "LINE TS": "Line of thunderstorms",
    "OBSC TS": "Obscured thunderstorms",
    "EMBD TS": "Embedded thunderstorms",
    "FRQ TS": "Frequent thunderstorms",
    "SQL TS": "Squall line thunderstorms",
    "OBSC TSGR": "Obscured thunderstorms with hail",
    "EMBD TSGR": "Embedded thunderstorms with hail",
    "FRQ TSGR": "Frequent thunderstorms with hail",
    "SQL TSGR": "Squall line thunderstorms with hail",
    "MOD TURB": "Moderate Turbulence",
    "SEV TURB": "Severe turbulence",
    "TURB": "Turbulence",
    "MOD ICE (FZRA)": "Moderate icing due to freezing rain",
    "SEV ICE (FZRA)": "Severe icing due to freezing rain",
    "MOD ICE": "Moderate icing",
    "SEV ICE": "Severe icing",
    "SEV MTW": "Severe mountain wave",
    "HVY DS": "Heavy duststorm",
    "HVY SS": "Heavy sandstorm",
    "RDOACT CLD": "Radioactive cloud",
    "VA ERUPTION": "Volcanic eruption",
    "VA CLD": "Volcanic cloud",
    "MTNS OBSC": "Mountain Obscuration",
    "MTNS OBSCN": "Mountain Obscuration",
    "CB": "Cumulonimbus",
}
