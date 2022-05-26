# NOTAM

A NOTAM (Notice to Air Missions) is a report detailing special events or conditions affecting airport and flight operations. These can include, but are in no way limitted to:

- Runway closures
- Lack of radar services
- Rocket launches
- Hazard locations
- Airspace restrictions
- Construction updates
- Unusual aircraft activity

NOTAMs have varius classifications and apply to certain types or size of aircraft. Some apply only to IFR operations, like when an ILS is out of service. Others apply only to airport operations the en route aircraft can ignore.

Every NOTAM has a start and end date and time. Additional NOTAMs may be issued to update, replace, or cancel existing NOTAMs as well. Some NOTAMs may still be served up to 10 days after the end date, so it's up to the developer to include or filter these reports.

## class avwx.**Notams**()

The Notams class provides two ways of requesting all applicable NOTAMs in an area: airport code and coordinate. The service will fetch all reports within 10 nautical miles of the desired center point. You can change the distance by updating the `Notams.radius` member before calling `update()`.

```python
>>> from pprint import pprint
>>> from avwx import Notams
>>> from avwx.structs import Coord
>>>
>>> kjfk = Notams("KJFK")
>>> kjfk.update()
True
>>> kjfk.last_updated
datetime.datetime(2022, 5, 26, 0, 43, 22, 44753, tzinfo=datetime.timezone.utc)
>>> print(kjfk.data[0].raw)
01/113 NOTAMN 
Q) ZNY/QMXLC/IV/NBO/A/000/999/4038N07346W005 
A) KJFK 
B) 2101081328 
C) 2209301100 

E) TWY TB BTN TERMINAL 8 RAMP AND TWY A CLSD
>>> pprint(kjfk.data[0].qualifiers)
Qualifiers(repr='ZNY/QMXLC/IV/NBO/A/000/999/4038N07346W005',
           fir='ZNY',
           subject=Code(repr='MX', value='Taxiway'),
           condition=Code(repr='LC', value='Closed'),
           traffic=Code(repr='IV', value='IFR and VFR'),
           purpose=[Code(repr='N', value='Immediate'),
                    Code(repr='B', value='Briefing'),
                    Code(repr='O', value='Flight Operations')],
           scope=[Code(repr='A', value='Aerodrome')],
           lower=Number(repr='000', value=0, spoken='zero'),
           upper=Number(repr='999', value=999, spoken='nine nine nine'),
           coord=Coord(lat=40.38, lon=-73.46, repr='4038N07346W'),
           radius=Number(repr='005', value=5, spoken='five'))
>>>
>>> coord = Notams(coord=Coord(lat=52, lon=-0.23))
>>> coord.update()
True
>>> coord.data[0].station
'EGSS'
>>> print(coord.data[0].body)
LONDON STANSTED ATC SURVEILLANCE MINIMUM ALTITUDE CHART - IN 
FREQUENCY BOX RENAME ESSEX RADAR TO STANSTED RADAR.
UK AIP AD 2.EGSS-5-1 REFERS
```

The `parse` and `from_report` methods can parse a report string if you want to override the normal fetching process.

```python
>>> from avwx import Notams
>>> report = """
05/295 NOTAMR 
Q) ZNY/QMNHW/IV/NBO/A/000/999/4038N07346W005 
A) KJFK 
B) 2205201527 
C) 2205271100 

E) APRON TERMINAL 4 RAMP CONST WIP S SIDE TAXILANE G LGTD AND BARRICADED
"""
>>> kjfk = Notams.from_report(report)
>>> kjfk.data[0].type
Code(repr='NOTAMR', value='Replace')
>>> kjfk.data[0].start_time
Timestamp(repr='2205201527', dt=datetime.datetime(2022, 5, 20, 15, 27, tzinfo=datetime.timezone.utc))
```

#### async **async_update**(*timeout: int = 10*) -> *bool*

Async updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

#### **code**: *Optional[str]*

Station ident code the report was initialized with

#### **data**: *List[avwx.structs.NotamData]* = *None*

List of NotamData dataclasses of parsed data values and units. Parsed on update()

#### **last_updated**: *datetime.datetime* = *None*

UTC Datetime object when the reports were last updated

#### **coord**: *avwx.structs.Coord*

Coordinate of the radial center

#### **parse**(*reports: Union[str, List[str]]*) -> *bool*

Updates report data by parsing a given report

#### **radius**: *int* = *10*

Distance from the airport or coordinate location to filter fetched reports

#### **raw**: *List[str]* = *None*

The unparsed report strings. Fetched on update()

#### **service**: *avwx.service.Service*

Service object used to fetch the report strings

#### **source**: *str* = *None*

Source URL root used to pull the current report data

#### **station**: *avwx.Station* = *None*

Provides basic station info

#### **units**: *avwx.structs.Units*

Units inferred from the station location and report contents

#### **update**(*timeout: int = 10*) -> *bool*

Updates report data by fetching and parsing recent aircraft reports

Returns `True` if a new report is available, else `False`

## class avwx.structs.**NotamData**

**raw**: *str*

**sanitized**: *str*

**station**: *Optional[str]*

**time**: *Optional[avwx.structs.Timestamp]*

**remarks**: *Optional[str]*

**number**: *Optional[str]*

**replaces**: *Optional[str]*

**type**: *Optional[avwx.structs.Code]*

**qualifiers**: *Optional[avwx.structs.Qualifiers]*

**start_time**: *Optional[avwx.structs.Timestamp]*

**end_time**: *Optional[avwx.structs.Timestamp]*

**schedule**: *Optional[str]*

**body**: *str*

**lower**: *Optional[avwx.structs.Number]*

**upper**: *Optional[avwx.structs.Number]*

## class avwx.structs.**Qualifiers**

**repr**: *str*

**fir**: *str*

**subject**: *Optional[avwx.structs.Code]*

**condition**: *Optional[avwx.structs.Code]*

**traffic**: *Optional[avwx.structs.Code]*

**purpose**: *List[avwx.structs.Code]*

**scope**: *List[avwx.structs.Code]*

**lower**: *Optional[avwx.structs.Number]*

**upper**: *Optional[avwx.structs.Number]*

**coord**: *Coord*

**radius**: *Optional[avwx.structs.Number]*
