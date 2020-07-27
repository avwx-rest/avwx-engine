# PIREP

A PIREP (Pilot Report) is an observation made by pilots inflight meant to aid controllers and pilots routing around adverse conditions and other conditions of note. They typically contain icing, turbulence, cloud types/bases/tops, and other info at a known distance and radial from a ground station. They are released as they come in.

## class avwx.**Pireps**(*station_ident: str = None, lat: float = None, lon: float = None*)

The Pireps class offers an object-oriented approach to managing multiple PIREP reports for a single station.

Below is typical usage for fetching and pulling PIREP data for KJFK.

```python
>>> from avwx import Pireps
>>> kmco = Pireps('KMCO')
>>> kmco.station.name
'Orlando International Airport'
>>> kmco.update()
True
>>> kmco.last_updated
datetime.datetime(2019, 5, 24, 13, 31, 46, 561732)
>>> kmco.raw[0]
'FLL UA /OV KFLL275015/TM 1241/FL020/TP B737/SK TOP020/RM DURD RY10L'
>>> kmco.data[0].location
Location(repr='KFLL275015', station='KFLL', direction=Number(repr='275', value=275, spoken='two seven five'), distance=Number(repr='015', value=15, spoken='one five'))
```

The `parse` and `from_report` methods can parse a report string if you want to override the normal fetching process. Here's an example of a really bad day.

```python
>>> from avwx import Metar
>>> ksfo = Metar.from_report(report)
True
>>> ksfo.station.city
'San Francisco'
>>> ksfo.last_updated
datetime.datetime(2018, 3, 4, 23, 54, 4, 353757)
>>> ksfo.data.flight_rules
'LIFR'
>>> ksfo.translations.clouds
'Broken layer at 4000ft (Towering Cumulus), Overcast layer at 5000ft - Reported AGL'
>>> ksfo.summary
'Winds N-360 (variable 320 to 040) at 24kt gusting to 55kt, Vis 0.125sm, Temp 14C, Dew 10C, Alt 29.78inHg, Heavy Thunderstorm, Vicinity Funnel Cloud, Broken layer at 4000ft (Towering Cumulus), Overcast layer at 5000ft'
```

#### **async_update**(*timeout: int = 10*) -> *bool*

Async updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

#### **data**: *List[avwx.structs.PirepData]* = *None*

List of PirepData dataclasses of parsed data values and units. Parsed on update()

#### **issued**: *date* = *None*

UTC date object when the report was issued

#### **last_updated**: *datetime.datetime* = *None*

UTC Datetime object when the reports were last updated

#### **lat**: *float*

Latitude of the radial center. This is supplied by the user or loaded from the station

#### **lon**: *float*

Longitude of the radial center. This is supplied by the user or loaded from the station

#### **parse**(*reports: Union[str, List[str]]*, *issued: Optional[date] = None*) -> *bool*

Updates report data by parsing a given report

Can accept a report issue date if not a recent report string

#### **raw**: *List[str]* = *None*

The unparsed report strings. Fetched on update()

#### **service**: *avwx.service.Service*

Service object used to fetch the report strings

#### **station**: *avwx.Station* = *None*

Provides basic station info

#### **units**: *avwx.structs.Units*

Units inferred from the station location and report contents

#### **update**(*timeout: int = 10*) -> *bool*

Updates report data by fetching and parsing recent aircraft reports

Returns `True` if a new report is available, else `False`

## class avwx.structs.**PirepData**

**aircraft**: *avwx.structs.Aircraft* = *None*

**altitude**: *avwx.structs.Number* = *None*

**clouds**: *List[avwx.structs.Cloud]*

**flight_visibility**: *avwx.structs.Number* = *None*

**icing**: *avwx.structs.Icing* = *None*

**location**: *avwx.structs.Location* = *None*

**raw**: *str*

**remarks**: *str*

**sanitized**: *str*

**icao**: *str*

**temperature**: *avwx.structs.Number* = *None*

**time**: *avwx.structs.Timestamp*

**turbulence**: *avwx.structs.Turbulence* = *None*

**type**: *str*

**wx**: *List[str]*
