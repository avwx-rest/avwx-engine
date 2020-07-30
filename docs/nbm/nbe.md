# NBM NBE

The [NBE report](https://www.weather.gov/mdl/nbm_textcard_v32#nbe) is an extended-range forecast (24-192 hours) based on the [National Blend of Models](https://www.weather.gov/mdl/nbm_home) and is only valid for ICAO stations in the United States and Puerto Rico, and US Virgin Islands. Reports are in 12-hour increments and published near the top of every hour.

## class avwx.**Nbe**(*icao: str*)

Class to handle NBM NBE report data

Below is typical usage for fetching and pulling NBE data for KJFK.

```python
>>> from avwx import Nbe
>>> kjfk = Nbe('KJFK')
>>> kjfk.station.name
'John F Kennedy International Airport'
>>> kjfk.update()
True
>>> kjfk.last_updated
datetime.datetime(2020, 7, 28, 1, 23, 4, 909939, tzinfo=datetime.timezone.utc)
>>> print(kjfk.raw)
"""
KJFK    NBM V3.2 NBE GUIDANCE    7/28/2020  0000 UTC
       WED 29| THU 30| FRI 31| SAT 01| SUN 02| MON 03| TUE 04|WED CLIMO
UTC    00  12| 00  12| 00  12| 00  12| 00  12| 00  12| 00  12| 00
FHR    24  36| 48  60| 72  84| 96 108|120 132|144 156|168 180|192
X/N    93  76| 91  76| 90  74| 86  72| 87  73| 85  74| 86  72| 84 68 83
TMP    84  80| 83  80| 81  78| 78  76| 78  78| 78  78| 78  76| 76
DPT    72  69| 68  69| 71  68| 67  66| 68  69| 70  71| 70  68| 69
SKY    61  21| 23  47| 80  73| 47  31| 30  54| 68  65| 66  59| 32
WDR    25  35| 20  26| 20   2| 16   1| 16   7| 16  24| 22  34| 18
WSP     5   2|  6   3|  5   4|  3   5|  7   4|  6   4|  5   4|  4
GST    11   4| 13   6| 13  10|  9  10| 13   7| 13   9| 16   9| 12
P12    48  23|  8   1| 23  28| 28  16| 18  17| 30  41| 46  31| 32 19 18
Q12    10   0|  0   0|  0   0|  0   0|  0   0|  0  64| 77  81| 83
Q24          |  0    |  0    |  0    |  0    |  0    |141    |164
DUR     2   1|  0   0|  0   0|  0   0|  0   0|  2  12| 12  12| 12
T12    46  32|  6   8| 21  22| 17   5|  6   5| 25  23| 19  18| 18
PZR     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
PSN     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
PPL     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
PRA   100 100|100 100|100 100|100 100|100 100|100 100|100 100|100
S12     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
SLV   138 114|111 119|119 121|113 101|108 117|134 132|124 123|121
I12     0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0   0|  0
S24          |  0    |  0    |  0    |  0    |  0    |  0    |  0
SOL   100 320|190 230|270 250|360 290|370  30|190 260|250 230|450
"""
>>> len(kjfk.data.forecast)
25
>>> kjfk.data.forecast[0].wind_direction
Number(repr='25', value=250, spoken='two five zero')
>>> print(kjfk.data.forecast[1].precip_duration.value, kjfk.units.duration)
1 hour
```

The `parse` and `from_report` methods can parse a report string if you want to override the normal fetching process.

#### async **async_update**(*timeout: int = 10*) -> *bool*

Async updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

#### **data**: *avwx.structs.NbeData* = *None*

NbeData dataclass of parsed data values and units. Parsed on update()

#### **from_report**(*report: str*) -> *avwx.Nbe*

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

## class avwx.structs.**NbeData**

**forecast**: *List[avwx.structs.NbePeriod]*

**raw**: *str*

**station**: *str*

**time**: *avwx.structs.Timestamp*

## class avwx.structs.**NbePeriod**

**dewpoint**: *avwx.structs.Number*

**freezing_precip**: *avwx.structs.Number*

**icing_amount_12**: *avwx.structs.Number*

**precip_amount_12**: *avwx.structs.Number*

**precip_amount_24**: *avwx.structs.Number*

**precip_chance_12**: *avwx.structs.Number*

**precip_duration**: *avwx.structs.Number*

**rain**: *avwx.structs.Number*

**sky_cover**: *avwx.structs.Number*

**sleet**: *avwx.structs.Number*

**snow_amount_12**: *avwx.structs.Number*

**snow_amount_24**: *avwx.structs.Number*

**snow_level**: *avwx.structs.Number*

**snow**: *avwx.structs.Number*

**solar_radiation**: *avwx.structs.Number*

**temperature**: *avwx.structs.Number*

**thunderstorm_12**: *avwx.structs.Number*

**time**: *avwx.structs.Timestamp*

**wave_height**: *avwx.structs.Number*

**wind_direction**: *avwx.structs.Number*

**wind_gust**: *avwx.structs.Number*

**wind_speed**: *avwx.structs.Number*
