# Static Values

Contains static objects for internal and external use

## Glossary

AVWX includes a compiled glossary of common report abbreviations that are listed separate from any other parsing mechanism. This is provided just for you to assist in translating the original reports or any item left in the `other` element.

#### avwx.static.glossary.**GLOBAL**: *{str: str}

Glossary of abreviations found in reports. These should be treated as default values. OTher elements may overwrite in specific instances.

#### avwx.static.glossary.**METAR**: *{str: str}

Glossary conflicts used only in METARs

#### avwx.static.glossary.**NA_REGIONAL**: *{str: str}

Glossary items and conflicts used for reports referencing locations in North America

## Station Identification

METAR and TAF reports come in two variants depending on the station's location: North American & International. This affects both element parsing and inferred units of measurement. AVWX determines this by looking at the station's ICAO value.

#### avwx.static.core.**NA_REGIONS**: *[str]*

Prefix indicating station uses North American formatting

#### avwx.static.core.**IN_REGIONS**: *[str]*

Prefix indicating station uses International formatting

#### avwx.static.core.**M_NA_REGIONS**: *[str]*

Two-character prefix indication Central American station uses North American formatting

#### avwx.static.core.**M_IN_REGIONS**: *[str]*

Two-character prefix indication Central American station uses International formatting

## Translations

Static values used to translate report data

#### avwx.static.core.**CLOUD_TRANSLATIONS**: *{str: str}*

Dictionary associating cloud layer and cloud codes with descriptions

#### avwx.static.taf.**ICING_CONDITIONS**: *{str: str}*

Dictionary associating icing report IDs with descriptions

#### avwx.static.taf.**PRESSURE_TENDENCIES**: *{str: str}*

Dictionary associating pressure change IDs with descriptions

#### avwx.static.core.**REMARKS_ELEMENTS**: *{str: str}*

Static remarks translation elements

#### avwx.static.core.**REMARKS_GROUPS**: *{str: str}*

Static remarks translation group strings

#### avwx.static.taf.**TURBULENCE_CONDITIONS**: *{str: str}*

Dictionary associating turbulence report IDs with descriptions

#### avwx.static.core.**WX_TRANSLATIONS**: *{str: str}*

Dictionary associating WX codes with descriptions

## Units

Static values involving units of measure

#### avwx.static.core.**CARDINALS**: *{str: int}*

Dictionary of cardinal direction values

#### avwx.static.core.**CLOUD_LIST**: *[str]*

List of cloud layer abbreviations

#### avwx.static.core.**FLIGHT_RULES**: *[str]*

List of flight rules abbreviations

#### avwx.static.core.**FRACTIONS**: *{str: str}*

Dictionary associating fraction strings with their spoken version

#### avwx.static.core.**IN_UNITS**: *{str: str}*

International variant units

#### avwx.static.core.**NA_UNITS**: *{str: str}*

North American variant units

#### avwx.static.core.**NUMBER_REPL**: *{str: str}*

Dictionary associating algebraic signs with their spoken version

#### avwx.static.core.**SPECIAL_NUMBERS**: *{str: tuple}*

Dictionary associating special number values with their spoken version

#### avwx.static.core.**SPOKEN_UNITS**: *{str: str}*

Units required to be translated in order to be spoken properly
