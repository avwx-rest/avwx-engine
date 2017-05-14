# AVWX-Engine
Aviation Weather parsing engine. METAR &amp; TAF

# Install

The easiest way to get started is to download the library from pypi using pip

```bash
pip install avwx-engine
```

# Basic Usage

Reports use ICAO idents when specifying the desired station. Exceptions are thrown if a potentially invalid ident is given.

```python
>>> import avwx
>>> 
>>> metar = avwx.Metar('KJFK')
>>> metar.station_info['Name']
'John F Kennedy International Airport'
>>> metar.update()
True
>>> metar.data['Flight-Rules']
'IFR'
```

# METAR

Meteorological Aerodrome Reports (METAR) contain current surface conditions at an airport or other reporting location that updates every hour or earlier.

### avwx.Metar.\_\_init\_\_(station: str)

- Metar objects are initialized with the desired ICAO ident

### avwx.Metar.update() -> bool`

- Fetches the current report from NOAA ADDS and parses the result. Populates the `data` and `translations` attributes

### avwx.Metar.station_info -> dict`

- Basic information about the station including name, elevation, and coordinates

- Available without needing to call `.update()`

### avwx.Metar.data -> dict

- The original report, raw parsed data, and unit values

### avwx.Metar.translations -> dict

- Translation strings for each primary attribute of the report

### avwx.Metar.summary -> str

- A summary string created from translations and designed to be read

### avwx.Metar.speech -> str

- A summary string created from translations and designed to be spoken by a text-to-speech program

### Example Metar Usage

```python
>>> import avwx
>>> 
>>> metar = avwx.Metar('KJFK')
>>> metar.station_info['Name']
'John F Kennedy International Airport'
>>> metar.update()
True
>>> metar.data['Flight-Rules']
'IFR'
>>> metar.data['Units']['Wind-Speed']
'kt'
>>> metar.translations['Wind']
'NNE-030 at 17kt gusting to 26kt'
>>> metar.summary
'Winds NNE-030 at 17kt gusting to 26kt, Vis 2sm, Temp 9C, Dew 8C, Alt 29.79inHg, Rain, Mist, Scattered clouds at 1000ft'
>>> metar.speech
'Winds zero three zero at 17kt gusting to 26kt. Visibility two miles. Temperature nine degrees Celsius. Dew point eight degrees Celsius. Altimeter two nine point seven nine. Rain. Mist. Scattered clouds at 700ft. Broken layer at 1000ft. Overcast layer at 2500ft'
```

# TAF

Terminal Area Forecasts (TAF) are in-flight 24-hour forecasts for an area within 5nm of an airport or other reporting station that updates every six hours. Parsed reports are broken out into time periods.

### avwx.TAF.\_\_init\_\_(station: str)

- TAF objects are initialized with the desired ICAO ident

### avwx.TAF.update() -> bool`

- Fetches the current report from NOAA ADDS and parses the result. Populates the `data` and `translations` attributes

### avwx.TAF.station_info -> dict`

- Basic information about the station including name, elevation, and coordinates

- Available without needing to call `.update()`

### avwx.TAF.data -> dict

- The original report, raw parsed data, and unit values

### avwx.TAF.translations -> dict

- Translation strings for each forecast's primary attributes

### avwx.TAF.summary -> [str]

- A list of forecast summary strings created from translations and designed to be read

### Example Taf Usage

```python
>>> import avwx
>>> 
>>> taf = avwx.Taf('KJFK')
>>> taf.update()
True
>>> taf.data['Forecast'][0]['Raw-Line']
'1400/1506 02017G25KT 3SM -RA OVC008'
>>> taf.summary[0]
'Winds NNE-020 at 17kt gusting to 25kt, Vis 3sm, Light Rain, Overcast layer at 800ft'
```

# Advanced Usuage

Developers can access the fetch and parse functionality directly using the functions below

### avwx.metar.fetch(station: str) -> str

- Returns the current METAR report from NOAA ADDS for a given station ident

### avwx.metar.parse(station: str, txt: str) -> dict

- Returns the parsed data for a given station ident and the raw  METAR report

### avwx.taf.fetch(station: str) -> str

- Returns the current TAF report from NOAA ADDS for a given station ident

### avwx.taf.parse(station: str, txt: str) -> dict

- Returns the parsed data for a given station ident and the raw  TAF report
