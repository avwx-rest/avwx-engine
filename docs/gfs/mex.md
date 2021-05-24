# GFS MOS MEX

The [MEX report](https://www.nws.noaa.gov/mdl/synop/mexcard.php) is an extended-range forecast (24-192 hours) based on the [Global Forecast System](https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/global-forcast-system-gfs) model output and is only valid for ICAO stations in the United States, Puerto Rico, and US Virgin Islands. Reports are published at 0000 and 1200 UTC.

## class avwx.**Mex**(*icao: str*)

The Mex class offers an object-oriented approach to managing MOS MEX data for a single station.

Below is typical usage for fetching and pulling MAV data for KJFK.

```python
>>> from avwx import Mex
>>> kjfk = Mex('KJFK')
>>> kjfk.station.name
'John F Kennedy International Airport'
>>> kjfk.update()
True
>>> kjfk.last_updated
datetime.datetime(2020, 4, 20, 12, 7, 7, 393270, tzinfo=datetime.timezone.utc)
>>> print(kjfk.raw)
"""
KJFK   GFSX MOS GUIDANCE   4/20/2020  0000 UTC
FHR  24| 36  48| 60  72| 84  96|108 120|132 144|156 168|180 192
MON  20| TUE 21| WED 22| THU 23| FRI 24| SAT 25| SUN 26| MON 27 CLIMO
X/N  57| 45  59| 37  56| 40  52| 49  58| 46  59| 48  59| 44  58 45 63
TMP  50| 49  48| 41  49| 45  48| 52  51| 50  53| 51  52| 48  51
DPT  31| 39  26| 17  17| 24  40| 46  43| 40  44| 43  40| 35  31
CLD  OV| OV  OV| CL  CL| OV  OV| OV  OV| PC  OV| OV  OV| OV  OV
WND  13| 14  26| 26  21| 16  13| 18  15| 16  12| 15  19| 19  11
P12   9|  1  73|  7   0|  9  43| 73  63| 27  51| 64  37| 35  32 24 23
P24    |     73|      7|     43|     77|     61|     73|     44    36
Q12   0|  0   2|  0   0|  0   1|  5   3|  0   2|  5    |
Q24    |      1|      0|      0|      5|      2|       |
T12   1|  0  12|  1   0|  4   4|  8  11|  3   3| 14   7|  5   9
T24    |  1    | 14    |  4    | 12    | 11    | 14    | 11
PZP   0|  0   1|  0   2|  4   1|  0   0|  0   0|  0   0|  0   0
PSN   0|  0   0| 37  25| 15   4|  0   0|  0   0|  2   0|  3   5
PRS   0|  2   1| 32  28| 19   4|  0   1|  1   1|  1   1|  8   9
TYP   R|  R   R| RS  RS|  R   R|  R   R|  R   R|  R   R|  R   R
SNW    |      0|      0|      0|      0|      0|       |
"""
>>> len(kjfk.data.forecast)
15
>>> kjfk.data.forecast[2].precip_chance_24
Number(repr='73', value=73, spoken='seven three')
```

The `parse` and `from_report` methods can parse a report string if you want to override the normal fetching process.

#### async **async_update**(*timeout: int = 10*) -> *bool*

Async updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

#### **data**: *avwx.structs.MexData* = *None*

MavData dataclass of parsed data values and units. Parsed on update()

#### **from_report**(*report: str*) -> *avwx.Mex*

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

#### **source**: *str* = *None*

Source URL root used to pull the current report data

#### **station**: *avwx.Station*

Provides basic station info

#### **units**: *avwx.structs.Units*

Units inferred from the station location and report contents

#### **update**(*timeout: int = 10*) -> *bool*

Updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

## class avwx.structs.**MexData**

**forecast**: *List[avwx.structs.MexPeriod]*

**raw**: *str*

**station**: *str*

**time**: *avwx.structs.Timestamp*

## class avwx.structs.**MexPeriod**

**cloud**: *avwx.structs.Code*

**dewpoint**: *avwx.structs.Number*

**freezing_precip**: *avwx.structs.Number*

**precip_amount_12**: *avwx.structs.Code*

**precip_amount_24**: *avwx.structs.Code*

**precip_chance_12**: *avwx.structs.Number*

**precip_chance_24**: *avwx.structs.Number*

**precip_type**: *avwx.structs.Code*

**rain_snow_mix**: *avwx.structs.Number*

**severe_storm_12**: *avwx.structs.Number*

**severe_storm_24**: *avwx.structs.Number*

**snow_amount_24**: *avwx.structs.Code*

**snow**: *avwx.structs.Number*

**temperature**: *avwx.structs.Number*

**thunderstorm_12**: *avwx.structs.Number*

**thunderstorm_24**: *avwx.structs.Number*

**time**: *avwx.structs.Timestamp*
