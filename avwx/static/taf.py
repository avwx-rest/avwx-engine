"""
TAF static values
"""

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
