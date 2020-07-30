# NBM NBH

The [NBH report](https://www.weather.gov/mdl/nbm_textcard_v32#nbh) is a 25-hour forecast based on the [National Blend of Models](https://www.weather.gov/mdl/nbm_home) and is only valid for ICAO stations in the United States and Puerto Rico, and US Virgin Islands. Reports are in 1-hour increments and are published near the top of every hour.

## class avwx.**Nbh**(*icao: str*)

Class to handle NBM NBH report data

Below is typical usage for fetching and pulling NBH data for KJFK.

```python
>>> from avwx import Nbh
>>> kjfk = Nbh('KJFK')
>>> kjfk.station.name
'John F Kennedy International Airport'
>>> kjfk.update()
True
>>> kjfk.last_updated
datetime.datetime(2020, 7, 26, 20, 37, 42, 352220, tzinfo=datetime.timezone.utc)
>>> print(kjfk.raw)
"""
KJFK   NBM V3.2 NBH GUIDANCE    7/26/2020  1900 UTC
UTC  20 21 22 23 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20
TMP  90 89 88 87 85 84 82 81 81 80 79 78 77 76 76 78 81 84 87 89 90 91 92 92 93
DPT  69 68 66 66 65 65 65 66 66 66 66 67 67 66 67 67 67 67 67 68 67 67 67 67 67
SKY   9 14 41 58 61 71 66 55 39 37 39 43 40 38 29 21 19 26 24 27 22 14 22 26 26
WDR  22 22 23 24 25 25 25 25 25 25 25 26 26 26 26 26 26 26 25 24 24 23 23 22 23
WSP  10  9  9  8  7  6  5  5  5  6  5  5  5  5  4  4  5  5  7  8  8  9 10 10 10
GST  17 16 16 15 14 12 11 12 12 12 12 11 11  9  9  9  9 10 11 13 14 15 16 17 17
P01   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
P06                                 0                 0                 0
Q01   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
DUR                                                   0
T01   1  1  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
PZR   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
PSN   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
PPL   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
PRA 100100100100100100100100100100100100100100100100100100100100100100100100100
S01   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
SLV  99101102103105105105106105104106104104104104103102100 99 98 98 99100101102
I01   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
CIG 888888888360360350340888888888888888888888888888888888888888888888888888888
VIS 110120120140140130120120120120110110110110110120130140150150150150150150150
LCB  80 60999999999999999999999999999999999999999999999999999999999999999999999
MHT  26 26 20 19  8  7  6  4  4  5  5  5  6  4  5  6  6 11 20 27 37 39 43 39 31
TWD  24 26 26 27 26 26 24 23 24 26 26 26 27 27 28 27 27 27 27 26 26 26 25 25 24
TWS  15 14 14 13 11 11 11 10 11 11 10 11 10  8  8  7  8  9 12 13 14 15 17 17 16
HID                                 6                 5                 6
SOL 710500430250110  0 30  0  0  0  0  0  0  0 30160330500650760830870870850720
"""
>>> len(kjfk.data.forecast)
25
>>> kjfk.data.forecast[0].snow_level
Number(repr='99', value=9900, spoken='nine nine hundred')
>>> print(kjfk.data.forecast[0].solar_radiation.value, kjfk.units.solar_radiation)
710 W/m2
```

The `parse` and `from_report` methods can parse a report string if you want to override the normal fetching process.

#### async **async_update**(*timeout: int = 10*) -> *bool*

Async updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

#### **data**: *avwx.structs.NbhData* = *None*

NbhData dataclass of parsed data values and units. Parsed on update()

#### **from_report**(*report: str*) -> *avwx.Nbh*

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

## class avwx.structs.**NbhData**

**forecast**: *List[avwx.structs.NbhPeriod]*

**raw**: *str*

**station**: *str*

**time**: *avwx.structs.Timestamp*

## class avwx.structs.**NbhPeriod**

**ceiling**: *avwx.structs.Number*

**cloud_base**: *avwx.structs.Number*

**dewpoint**: *avwx.structs.Number*

**freezing_precip**: *avwx.structs.Number*

**haines**: *List[avwx.structs.Number]*

**icing_amount_1**: *avwx.structs.Number*

**mixing_height**: *avwx.structs.Number*

**precip_amount_1**: *avwx.structs.Number*

**precip_chance_1**: *avwx.structs.Number*

**precip_chance_6**: *avwx.structs.Number*

**precip_duration**: *avwx.structs.Number*

**rain**: *avwx.structs.Number*

**sky_cover**: *avwx.structs.Number*

**sleet**: *avwx.structs.Number*

**snow_amount_1**: *avwx.structs.Number*

**snow_level**: *avwx.structs.Number*

**snow**: *avwx.structs.Number*

**solar_radiation**: *avwx.structs.Number*

**temperature**: *avwx.structs.Number*

**thunderstorm_1**: *avwx.structs.Number*

**time**: *avwx.structs.Timestamp*

**transport_wind_direction**: *avwx.structs.Number*

**transport_wind_speed**: *avwx.structs.Number*

**visibility**: *avwx.structs.Number*

**wave_height**: *avwx.structs.Number*

**wind_direction**: *avwx.structs.Number*

**wind_gust**: *avwx.structs.Number*

**wind_speed**: *avwx.structs.Number*
