# Static Values

Contains static objects for internal and external use

## Station Identification

METAR and TAF reports come in two variants depending on the station's location: North American & International. This affects both element parsing and inferred units of measurement. AVWX determines this by looking at the station's ICAO value.

### avwx.static.**NA_REGIONS**: *[str]*

Prefix indicating station uses North American formatting

### avwx.static.**IN_REGIONS**: *[str]*

Prefix indicating station uses International formatting

### avwx.static.**M_NA_REGIONS**: *[str]*

Two-character prefix indication Central American station uses North American formatting

### avwx.static.**M_IN_REGIONS**: *[str]*

Two-character prefix indication Central American station uses International formatting

## Translations

Static values used to translate report data

### avwx.static.**CLOUD_TRANSLATIONS**: *{str: str}*

Dictionary associating cloud layer and cloud codes with descriptions

### avwx.static.**ICING_CONDITIONS**: *{str: str}*

Dictionary associating icing report IDs with descriptions

### avwx.static.**PRESSURE_TENDENCIES**: *{str: str}*

Dictionary associating pressure change IDs with descriptions

### avwx.static.**REMARKS_ELEMENTS**: *{str: str}*

Static remarks translation elements

### avwx.static.**REMARKS_GROUPS**: *{str: str}*

Static remarks translation group strings

### avwx.static.**TURBULENCE_CONDITIONS**: *{str: str}*

Dictionary associating turbulence report IDs with descriptions

### avwx.static.**WX_TRANSLATIONS**: *{str: str}*

Dictionary associating WX codes with descriptions

## Units

Static values involving units of measure

### avwx.static.**CARDINALS**: *{str: int}*

Dictionary of cardinal direction values

### avwx.static.**CLOUD_LIST**: *[str]*

List of cloud layer abbreviations

### avwx.static.**FLIGHT_RULES**: *[str]*

List of flight rules abbreviations

### avwx.static.**FRACTIONS**: *{str: str}*

Dictionary associating fraction strings with their spoken version

### avwx.static.**IN_UNITS**: *{str: str}*

International variant units

### avwx.static.**NA_UNITS**: *{str: str}*

North American variant units

### avwx.static.**NUMBER_REPL**: *{str: str}*

Dictionary associating algebraic signs with their spoken version

### avwx.static.**SPECIAL_NUMBERS**: *{str: tuple}*

Dictionary associating special number values with their spoken version

### avwx.static.**SPOKEN_UNITS**: *{str: str}*

Units required to be translated in order to be spoken properly
