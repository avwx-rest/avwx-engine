# TAF

A TAF (Terminal Aerodrome Forecast) is a 24-hour weather forecast for the area 5 statute miles from the reporting station. They are update once every three or six hours or when significant changes warrant an update, and the observations are valid for six hours or until the next report is issued

## class avwx.**Taf**(*code: str*)

The Taf class offers an object-oriented approach to managing TAF data for a single station.

```python
>>> from avwx import Taf
>>> kjfk = Taf("KJFK")
>>> kjfk.station.name
'John F Kennedy International Airport'
>>> kjfk.update()
True
>>> kjfk.last_updated
datetime.datetime(2018, 3, 4, 23, 43, 26, 209644, tzinfo=datetime.timezone.utc)
>>> kjfk.raw
'KJFK 042030Z 0421/0524 33016G27KT P6SM BKN045 FM051600 36016G22KT P6SM BKN040 FM052100 35013KT P6SM SCT035'
>>> len(kjfk.data.forecast)
3
>>> kjfk.data.forecast[0].flight_rules
'VFR'
>>> kjfk.translations.forecast[0].wind
'NNW-330 at 16kt gusting to 27kt'
>>> kjfk.speech
'Starting on March 4th - From 21 to 16 zulu, Winds three three zero at 16kt gusting to 27kt. Visibility greater than six miles. Broken layer at 4500ft. From 16 to 21 zulu, Winds three six zero at 16kt gusting to 22kt. Visibility greater than six miles. Broken layer at 4000ft. From 21 to midnight zulu, Winds three five zero at 13kt. Visibility greater than six miles. Scattered clouds at 3500ft'
```

The `parse` and `from_report` methods can parse a report string if you want to override the normal fetching process.

```python
>>> from avwx import Taf
>>> report = "TAF ZYHB 082300Z 0823/0911 VRB03KT 9999 SCT018 BKN120 TX14/0907Z TN04/0921Z FM090100 09015KT 9999 -SHRA WS020/13045KT SCT018 BKN120 BECMG 0904/0906 34008KT PROB30 TEMPO 0906/0911 7000 -RA SCT020 650104 530804 RMK FCST BASED ON AUTO OBS. NXT FCST BY 090600Z"
>>> zyhb = Taf.from_report(report)
True
>>> zyhb.station.city
'Hulan'
>>> zyhb.data.remarks
'RMK FCST BASED ON AUTO OBS. NXT FCST BY 090600Z'
>>> zyhb.summary[-1]
'Vis 7km, Light Rain, Scattered clouds at 2000ft, Frequent moderate turbulence in clear air from 8000ft to 12000ft, Moderate icing in clouds from 1000ft to 5000ft'
```

#### async **async_update**(*timeout: int = 10*) -> *bool*

Async updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

#### **code**: *str*

Station ident code the report was initialized with

#### **data**: *avwx.structs.TafData* = *None*

TafData dataclass of parsed data values and units. Parsed on update()

#### **from_report**(*report: str*) -> *avwx.Taf*

Returns an updated report object based on an existing report

#### **issued**: *date* = *None*

UTC date object when the report was issued

#### **last_updated**: *datetime.datetime* = *None*

UTC Datetime object when the report was last updated

#### **parse**(*report: str*, *issued: Optional[date] = None*) -> *bool*

Updates report data by parsing a given report

Can accept a report issue date if not a recent report string

#### **raw**: *str* = *None*

The unparsed report string. Fetched on update()

#### **service**: *avwx.service.Service*

Service object used to fetch the report string

#### **source**: *str* = *None*

Source URL root used to pull the current report data

#### **speech**: *str*

Report summary designed to be read by a text-to-speech program

#### **station**: *avwx.Station*

Provides basic station info

#### **summary**: *[str]*

Condensed report summaries created from translations

#### **translations**: *avwx.structs.TafTrans*

TafTrans dataclass of translation strings from data. Parsed on update()

#### **units**: *avwx.structs.Units*

Units inferred from the station location and report contents

#### **update**(*timeout: int = 10*) -> *bool*

Updates report data by fetching and parsing the report

Returns `True` if a new report is available, else `False`

## class avwx.structs.**TafData**

**alts**: *str* = *None*

**end_time**: *avwx.structs.Timestamp*

**forecast**: *List[avwx.structs.TafLineData]*

**max_temp**: *float* = *None*

**min_temp**: *float* = *None*

**raw**: *str*

**remarks**: *str*

**start_time**: *avwx.structs.Timestamp*

**icao**: *str*

**temps**: *List[str]* = *None*

**time**: *avwx.structs.Timestamp*

## class avwx.structs.**TafTrans**

**forecast**: *List[avwx.structs.TafLineTrans]*

**max_temp**: *str*

**min_temp**: *str*

**remarks**: *dict*

## class avwx.structs.**TafLineData**

**altimeter**: *avwx.structs.Number*

**clouds**: *List[avwx.structs.Cloud]*

**end_time**: *avwx.structs.Timestamp*

**flight_rules**: *str*

**icing**: *List[str]*

**other**: *List[str]*

**probability**: *avwx.structs.Number*

**raw**: *str*

**sanitized**: *str*

**start_time**: *avwx.structs.Timestamp*

**transition_start**: *avwx.structs.Timestamp*

**turbulence**: *List[str]*

**type**: *str*

**visibility**: *avwx.structs.Number*

**wind_direction**: *avwx.structs.Number*

**wind_gust**: *avwx.structs.Number*

**wind_shear**: *str*

**wind_speed**: *avwx.structs.Number*

## class avwx.structs.**TafLineTrans**

**altimeter**: *str*

**clouds**: *str*

**icing**: *str*

**other**: *str*

**turbulence**: *str*

**visibility**: *str*

**wind**: *str*

**wind_shear**: *str*
