# NBM NBS

The [NBS report](https://www.weather.gov/mdl/nbm_textcard_v32#nbs) is a short-range forecast (6-72 hours) based on the [National Blend of Models](https://www.weather.gov/mdl/nbm_home) and is only valid for ICAO stations in the United States and Puerto Rico, and US Virgin Islands. Reports are in 3-hour increments and published near the top of every hour.

## class avwx.**Nbs**(*icao: str*)

Class to handle NBM NBS report data

Below is typical usage for fetching and pulling Nbs data for KJFK.

```python
>>> from avwx import Nbs
>>> kjfk = Nbs('KJFK')
>>> kjfk.station.name
'John F Kennedy International Airport'
>>> kjfk.update()
True
>>> kjfk.last_updated
datetime.datetime(2020, 7, 28, 1, 3, 46, 447635, tzinfo=datetime.timezone.utc)
>>> print(kjfk.raw)
"""
KJFK    NBM V3.2 NBS GUIDANCE    7/27/2020  2300 UTC
DT /JULY 28               /JULY 29                /JULY 30
UTC  03 06 09 12 15 18 21 00 03 06 09 12 15 18 21 00 03 06 09 12 15 18 21
FHR  04 07 10 13 16 19 22 25 28 31 34 37 40 43 46 49 52 55 58 61 64 67 70
N/X           79          93          76          91          76
TMP  85 82 80 83 89 91 89 84 81 79 77 80 85 89 87 83 81 79 77 80 86 88 86
DPT  70 70 71 72 72 72 73 72 72 71 69 69 68 67 68 69 68 67 68 69 68 69 70
SKY   4 10  2  4 12 23 38 61 53 62 51 26 19  9 21 24 25 34 32 45 57 70 79
WDR  23 24 23 24 24 22 23 27 28 28 34 35 21 20 19 22 23 25 26 26 23 20 20
WSP   8  8  5  6  8  9  7  5  3  2  1  2  3  6  9  7  4  4  3  3  4  7  8
GST  16 15 11 11 13 15 15 11  9  5  4  4  6 12 15 13 11 11  8  6  7 13 15
P06      0     1    15    48    17    11     8     8     1     0     5
P12            1          48          17           8           1
Q06      0     0     0    11     0     0     0     0     0     0     0
Q12            0          11           0           0           0
DUR            0           2           0           0           0
T03   2  3  1  1  2 10 27 30 21 13  8  5  1  0  2  3  4  3  2  3  1  3  7
T12            4          48          33           6           8
PZR   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
PSN   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
PPL   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
PRA 100100100100100100100100100100100100100100100100100100100100100100100
S06      0     0     0     0     0     0     0     0     0     0     0
SLV 108112113133135139141139137134124113102 99107115114118118119118118118
I06      0     0     0     0     0     0     0     0     0     0     0
CIG 888888888888888888888170888150888888888888888888888888888888888888888
VIS 120120110120130130130110110110110130110110110120120120110110110110110
LCB  60 70999 90 90999 50 60 60 60 60 60 22999999200230 70 80 60 60150 60
MHT   7  6  5 13 30 46 19 15  7  7 10 16 40 35 13  4  4  4  9 18 31 27 13
TWD  23 24 23 27 25 24 27 27 28 21 34  6 26 23 20 19 26 23 27 29 24 20 18
TWS  17 16  9 11 13 16 12  9  5  5  4  3  4  8 11 10  8 10 10  6  6  9 13
HID      4     4     4     4     3     4     4     5     5     3     4
SOL   0  0  0320700760360100  0  0  0320720830620190  0  0  0230480570540
"""
>>> len(kjfk.data.forecast)
23
>>> kjfk.data.forecast[0].ceiling
Number(repr='888', value=None, spoken='unlimited')
>>> print(kjfk.data.forecast[7].precip_amount_12.value, kjfk.units.accumulation)
0.11 in
```

The `parse` and `from_report` methods can parse a report string if you want to override the normal fetching process.

#### async **async_update**(*timeout: int = 10*) -> *bool*

Async updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

#### **data**: *avwx.structs.NbsData* = *None*

NbsData dataclass of parsed data values and units. Parsed on update()

#### **from_report**(*report: str*) -> *avwx.Nbs*

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

## class avwx.structs.**NbsData**

**forecast**: *List[avwx.structs.NbsPeriod]*

**raw**: *str*

**station**: *str*

**time**: *avwx.structs.Timestamp*

## class avwx.structs.**NbsPeriod**

**ceiling**: *avwx.structs.Number*

**cloud_base**: *avwx.structs.Number*

**dewpoint**: *avwx.structs.Number*

**freezing_precip**: *avwx.structs.Number*

**haines**: *List[avwx.structs.Number]*

**icing_amount_6**: *avwx.structs.Number*

**mixing_height**: *avwx.structs.Number*

**precip_amount_12**: *avwx.structs.Number*

**precip_amount_6**: *avwx.structs.Number*

**precip_chance_12**: *avwx.structs.Number*

**precip_chance_6**: *avwx.structs.Number*

**precip_duration**: *avwx.structs.Number*

**rain**: *avwx.structs.Number*

**sky_cover**: *avwx.structs.Number*

**sleet**: *avwx.structs.Number*

**snow_amount_6**: *avwx.structs.Number*

**snow_level**: *avwx.structs.Number*

**snow**: *avwx.structs.Number*

**solar_radiation**: *avwx.structs.Number*

**temperature**: *avwx.structs.Number*

**thunderstorm_12**: *avwx.structs.Number*

**thunderstorm_3**: *avwx.structs.Number*

**time**: *avwx.structs.Timestamp*

**transport_wind_direction**: *avwx.structs.Number*

**transport_wind_speed**: *avwx.structs.Number*

**visibility**: *avwx.structs.Number*

**wave_height**: *avwx.structs.Number*

**wind_direction**: *avwx.structs.Number*

**wind_gust**: *avwx.structs.Number*

**wind_speed**: *avwx.structs.Number*
