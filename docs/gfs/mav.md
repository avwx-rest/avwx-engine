# GFS MOS MAV

The [MAV report](https://www.nws.noaa.gov/mdl/synop/mavcard.php) is a short-range forecast (6-72 hours) based on the [Global Forecast System](https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/global-forcast-system-gfs) model output and is only valid for ICAO stations in the United States, Puerto Rico, and US Virgin Islands. Reports are published every six hours starting at 0000 UTC.

## class avwx.**Mav**(*icao: str*)

The Mav class offers an object-oriented approach to managing MOS MAV data for a single station.

Below is typical usage for fetching and pulling MAV data for KJFK.

```python
>>> from avwx import Mav
>>> kjfk = Mav('KJFK')
>>> kjfk.station.name
'John F Kennedy International Airport'
>>> kjfk.update()
True
>>> kjfk.last_updated
datetime.datetime(2020, 4, 20, 1, 7, 7, 393270, tzinfo=datetime.timezone.utc)
>>> print(kjfk.raw)
"""
KJFK   GFS MOS GUIDANCE    4/19/2020  1800 UTC
DT /APR  20                  /APR  21                /APR  22
HR   00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 12 18
N/X              46          58          44          58       37
TMP  53 52 50 48 48 50 54 56 51 49 47 46 49 53 55 52 47 45 43 41 54
DPT  43 41 37 35 33 30 28 27 28 30 32 34 37 39 37 32 26 23 22 18 14
CLD  OV OV OV OV OV OV OV SC FW CL CL FW BK OV OV OV BK FW CL FW SC
WDR  20 22 26 35 02 03 02 02 34 19 20 18 18 18 18 23 29 30 29 29 28
WSP  20 13 07 08 11 14 14 11 05 03 04 06 11 19 25 21 22 25 20 19 22
P06         0    12     9     1     0     1    29    68     8  2  0
P12              12           9           2          69       15
Q06         0     0     0     0     0     0     0     2     0  0  0
Q12               0           0           0           2        0
T06      0/ 4  1/ 0  1/ 0  0/ 0  0/ 0  0/ 0  5/ 3 13/13  0/ 0  0/ 8
T12                  1/ 2        0/ 0        9/ 6       14/13  1/ 8
POZ   0  1  1  0  0  0  0  0  0  0  0  0  0  0  0  1  0  0  0  0  0
POS   0  0  0  0  0  2  0  6  6  9  9  0 16  8  0  4  4 47 60 67 42
TYP   R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  R  S  S  R
SNW                                       0                    0
CIG   7  7  7  7  6  6  6  8  8  8  8  8  8  6  6  6  7  8  8  8  8
VIS   7  7  7  7  7  7  7  7  7  7  7  7  7  7  7  6  7  7  7  7  7
OBV   N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N  N
"""
>>> len(kjfk.data.forecast)
21
>>> kjfk.data.forecast[0].ceiling
Code(repr='7', value='6600 - 12,000 feet')
```

The `parse` and `from_report` methods can parse a report string if you want to override the normal fetching process.

#### **async_update**(*timeout: int = 10*) -> *bool*

Async updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

#### **data**: *avwx.structs.MavData* = *None*

MavData dataclass of parsed data values and units. Parsed on update()

#### **from_report**(*report: str*) -> *avwx.Mav*

Returns an updated report object based on an existing report

#### **icao**: *str*

4-character ICAO station ident code the report was initialized with

#### **issued**: *date* = *None*

UTC date object when the report was issued

#### **last_updated**: *datetime.datetime* = *None*

UTC Datetime object when the report was last updated

#### **parse**(*report: str*) -> *bool*

Updates report data by parsing a given report

#### **raw**: *str* = *None*

The unparsed report string. Fetched on update()

#### **service**: *avwx.service.Service*

Service object used to fetch the report string

#### **station**: *avwx.Station*

Provides basic station info

#### **units**: *avwx.structs.Units*

Units inferred from the station location and report contents

#### **update**(*timeout: int = 10*) -> *bool*

Updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

## class avwx.structs.**MavData**

**forecast**: *List[avwx.structs.MavPeriod]*

**raw**: *str*

**station**: *str*

**time**: *avwx.structs.Timestamp*

## class avwx.structs.**MavPeriod**

**ceiling**: *avwx.structs.Code*

**cloud**: *avwx.structs.Code*

**dewpoint**: *avwx.structs.Number*

**freezing_precip**: *avwx.structs.Number*

**precip_amount_6**: *avwx.structs.Code*

**precip_amount_12**: *avwx.structs.Code*

**precip_chance_6**: *avwx.structs.Number*

**precip_chance_12**: *avwx.structs.Number*

**precip_type**: *avwx.structs.Code*

**severe_storm_6**: *avwx.structs.Number*

**severe_storm_12**: *avwx.structs.Number*

**snow**: *avwx.structs.Number*

**temperature**: *avwx.structs.Number*

**thunderstorm_6**: *avwx.structs.Number*

**thunderstorm_12**: *avwx.structs.Number*

**time**: *avwx.structs.Timestamp*

**vis_obstruction**: *avwx.structs.Code*

**visibility**: *avwx.structs.Code*

**wind_direction**: *avwx.structs.Number*

**wind_speed**: *avwx.structs.Number*
