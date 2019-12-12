import re


# Reusable snippets

VISIBILTY_PATTERN = r"[\d/\s]{1,5}"
RUNWAY_PATTERN = r"RWY\d{2}[LCR]?"
SURFACE_LOCATION_PATTERN = rf"(?:TWR|{RUNWAY_PATTERN})"
DIRECTION_PATTERN = r"[NSEW]{1,3}"

# Compiled patterns

AIRCRAFT_MISHAP_RE = re.compile(r"\bACFT MSHP\b")

AUTOMATED_STATION_RE = re.compile(r"\bAO[12]\b")

"""
BEGINNING AND ENDING OF PRECIPITATION AND THUNDERSTORM
w'w'B(hh)mmE(hh)mm; TSB(hh)mmE(hh)mm
"""
# todo: Add other precip types
BEGINNING_ENDING_OF_PRECIP_AND_TS = re.compile(
    r"""
\b
(?P<precip>RA|TS)
(?P<first>
  (?P<first_type>[BE])
  (?P<first_time>\d{4}|\d{2})
)
(?P<second>
  (?#
    Do not match unless time ends word
  )
  (?:(?=[BE]\d{1,4}\b)
  (?P<second_type>[BE])
  (?P<second_time>\d{4}|\d{2})?
)
)?
""",
    re.VERBOSE,
)

CEILING_HEIGHT_AT_SECOND_LOCATION_RE = re.compile(
    r"""
    \bCIG
    \s
    (?P<height>\d{3})
    \s
    (?P<location>RWY\d{2}[LCR]?)\b
    """,
    re.VERBOSE,
)

LIGHTNING_RE = re.compile(
    rf"""
\b(?P<frequent>FRQ)?
\s?
\bLTG
(?:\s(?P<direction>{DIRECTION_PATTERN}))?
""",
    re.VERBOSE,
)

PEAK_WIND_RE = re.compile(
    r"""
    \bPK[_\s]WND[_\s]
    (?P<direction>\d{3})
    (?P<speed>\d{2,3})
    /
    (?P<hours>\d{2})?
    (?P<minutes>\d{2})
    \b
    """,
    re.VERBOSE,
)

PRESSURE_CHANGE_RE = re.compile(r"\bPRES(?P<direction>[FR])R\b")

REMARKS_IDENTIFIER_RE = re.compile(r"\bRMK\b")

SEA_LEVEL_PRESSURE_RE = re.compile(r"\bSLP(?P<pressure>\d{1,3})\b")

TORNADO_ACTIVITY_RE = re.compile(
    r"""
\b(?P<activity>TORNADO|FUNNEL\sCLOUD|WATERSPOUT)\b
\s?
(?P<began_ended>[BE])?
(?P<minutes>\d\d)?
\s?
(?P<location>[NSEW]{1,3})?
(?:\sMOV\s)?
(?P<movement>[NSEW]{1,3})?
""",
    re.VERBOSE,
)

TOWER_OR_SURFACE_VISIBILITY_RE = re.compile(
    fr"""
    \b(?P<location>TWR|SFC)
    \sVIS\s
    (?P<visibility>{VISIBILTY_PATTERN})
    \b
    """,
    re.VERBOSE,
)

VARIABLE_CEILING_HEIGHT_RE = re.compile(
    r"\bCIG\s(?P<lower>\d{1,3})V(?P<upper>\d{1,3})\b"
)

VARIABLE_PREVAILING_VISIBILITY_RE = re.compile(
    fr"""
    \bVIS\s
    (?P<lower>{VISIBILTY_PATTERN})
    V
    (?P<upper>{VISIBILTY_PATTERN})
    \b
    """,
    re.VERBOSE,
)

VIRGA_RE = re.compile(r"\bVIRGA\b")

"""
VISIBILITY AT SECOND LOCATION: VIS vvvvv [LOC] 
reported if different than the reported prevailing visibility in body of report.
ex: VIS 3/4 RWY11
"""
VISIBILITY_AT_SECOND_LOCATION_RE = re.compile(
    rf"""
\bVIS\s
(?P<visibility>{VISIBILTY_PATTERN})
\s
(?P<location>{SURFACE_LOCATION_PATTERN})\b
""",
    re.VERBOSE,
)

WIND_SHIFT_RE = re.compile(r"\bWSHFT\s(?P<hours>\d{2})?(?P<minutes>\d{2})")

# clean up namespace
del VISIBILTY_PATTERN
del RUNWAY_PATTERN
del SURFACE_LOCATION_PATTERN
del DIRECTION_PATTERN
