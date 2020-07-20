"""
GFX service static values
"""

#:
UNITS = {
    "altimeter": "inHg",
    "altitude": "ft",
    "temperature": "F",
    "visibility": "sm",
    "wind_speed": "kt",
}

#: GFS coded ceiling values
CEILING_HEIGHT = {
    "1": "< 200 feet",
    "2": "200 - 400 feet",
    "3": "500 - 900 feet",
    "4": "1000 - 1900 feet",
    "5": "2000 - 3000 feet",
    "6": "3100 - 6500 feet",
    "7": "6600 - 12,000 feet",
    "8": "> 12,000 feet or unlimited ceiling",
}

#: GFS coded visibility values
VISIBILITY = {
    "1": "< 1/2 miles",
    "2": "1/2 - < 1 miles",
    "3": "1 - < 2 miles",
    "4": "2 - < 3 miles",
    "5": "3 - 5 miles",
    "6": "6 miles",
    "7": "> 6 miles",
}

#:
VISIBILITY_OBSTRUCTION = {
    "N": "none",
    "HZ": "haze, smoke, dust",
    "BR": "mist (fog with visibility >= 5/8 mile)",
    "FG": "fog or ground fog (visibility < 5/8 mile)",
    "BL": "blowing dust, sand, snow",
}

#:
CLOUD = {
    "CL": "clear",
    "FW": "few",
    "SC": "scattered",
    "PC": "partly cloudy",
    "BK": "broken",
    "OV": "overcast",
}

#:
PRECIPITATION_AMOUNT = {
    "0": "no precipitation",
    "1": "0.01 to 0.09 inches",
    "2": "0.10 to 0.24 inches",
    "3": "0.25 to 0.49 inches",
    "4": "0.50 to 0.99 inches",
    "5": "1.00 to 1.99 inches",
    "6": "2.00 inches or greater",
}

#:
PRECIPITATION_TYPE = {
    "S": "pure snow or snow grains",
    "Z": "freezing rain/drizzle, ice pellets, or anything mixed with freezing precipitation",
    "RS": "rain/drizzle and snow mixed",
    "R": "pure rain/drizzle",
}

#:
SNOWFALL_AMOUNT = {
    "0": "no snow or a trace expected",
    "1": "> a trace to < 2 inches",
    "2": "2 to < 4 inches",
    "4": "4 to < 6 inches",
    "6": "6 to < 8 inches",
    "8": ">= 8 inches",
}
