# METAR

A METAR (Meteorological Aerodrome Report) is the surface weather observed at most controlled (and some uncontrolled) airports. They are updated once per hour or when conditions change enough to warrant an update, and the observations are valid for one hour after the report was issued or until the next report is issued.

## class avwx.**Metar**(*station_ident: str*)

The Metar class offers an object-oriented approach to managing METAR data for a single station.

Below is typical usage for fetching and pulling METAR data for KJFK.

```python
>>> from avwx import Metar
>>> kjfk = Metar('KJFK')
>>> kjfk.station.name
'John F Kennedy International Airport'
>>> kjfk.update()
True
>>> kjfk.last_updated
datetime.datetime(2018, 3, 4, 23, 36, 6, 62376)
>>> kjfk.raw
'KJFK 042251Z 32023G32KT 10SM BKN060 04/M08 A3008 RMK AO2 PK WND 32032/2251 SLP184 T00441078'
>>> kjfk.data.flight_rules
'VFR'
>>> kjfk.translations.remarks
{'AO2': 'Automated with precipitation sensor', 'SLP184': 'Sea level pressure: 1018.4 hPa', 'T00441078': 'Temperature 4.4°C and dewpoint -7.8°C'}
```

The update function can also accept a given report string if you want to override to normal fetching process. Here's an example of a really bad day.

```python
>>> from avwx import Metar
>>> ksfo = Metar('KSFO')
>>> ksfo.station.city
'San Francisco'
>>> report = 'KSFO 031254Z 36024G55KT 320V040 1/8SM R06/0200D +TS VCFC OVC050 BKN040TCU 14/10 A2978 RMK AIRPORT CLOSED'
>>> ksfo.update(report)
True
>>> ksfo.last_updated
datetime.datetime(2018, 3, 4, 23, 54, 4, 353757)
>>> ksfo.data.flight_rules
'LIFR'
>>> ksfo.translations.clouds
'Broken layer at 4000ft (Towering Cumulus), Overcast layer at 5000ft - Reported AGL'
>>> ksfo.summary
'Winds N-360 (variable 320 to 040) at 24kt gusting to 55kt, Vis 0.125sm, Temp 14C, Dew 10C, Alt 29.78inHg, Heavy Thunderstorm, Vicinity Funnel Cloud, Broken layer at 4000ft (Towering Cumulus), Overcast layer at 5000ft'
```

#### **async_update**() -> *bool*

Async version of `update`

#### **data**: *avwx.structs.MetarData* = *None*

MetarData dataclass of parsed data values and units. Parsed on update()

#### **from_report**(*report: str*) -> *avwx.Metar*

Returns an updated report object based on an existing report

#### **icao**: *str*

4-character ICAO station ident code the report was initialized with

#### **last_updated**: *datetime.datetime* = *None*

UTC Datetime object when the report was last updated

#### **raw**: *str* = *None*

The unparsed report string. Fetched on update()

#### **service**: *avwx.service.Service*

Service object used to fetch the report string

#### **speech**: *str*

Report summary designed to be read by a text-to-speech program

#### **station**: *avwx.Station*

Provides basic station info

#### **summary**: *str*

Condensed report summary created from translations

#### **translations**: *avwx.structs.MetarTrans* = *None*

MetarTrans dataclass of translation strings from data. Parsed on update()

#### **units**: *avwx.structs.Units*

Units inferred from the station location and report contents

#### **update**(*report: str = None*) -> *bool*

Updates `raw`, `data`, and `translations` by fetching and parsing the report

Can accept a report string to parse instead

Returns `True` if a new report is available, else `False`

## class avwx.structs.**MetarData**

**altimeter**: *avwx.structs.Number*

**clouds**: *[avwx.structs.Cloud]*

**dewpoint**: *avwx.structs.Number*

**flight_rules**: *str*

**other**: *[str]*

**raw**: *str*

**remarks**: *str*

**remarks_info**: *avwx.structs.RemarksData*

**runway_visibility**: *[str]*

**sanitized**: *str*

**icao**: *str*

**temperature**: *avwx.structs.Number*

**time**: *avwx.structs.Timestamp*

**visibility**: *avwx.structs.Number*

**wind_direction**: *avwx.structs.Number*

**wind_gust**: *avwx.structs.Number*

**wind_speed**: *avwx.structs.Number*

**wind_variable_direction**: *avwx.structs.Number*

## class avwx.structs.**MetarTrans**

**altimeter**: *str*

**clouds**: *str*

**dewpoint**: *str*

**other**: *str*

**remarks**: *dict*

**temperature**: *str*

**visibility**: *str*

**wind**: *str*
