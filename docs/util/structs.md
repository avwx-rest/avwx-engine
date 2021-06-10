# Other Data Structures

## class avwx.structs.**Aircraft**

#### **from_icao**(*code: str*) -> *avwx.structs.Aircraft*

Load an Aircraft from an ICAO aircraft code

**code**: *str*

**type**: *str*

## class avwx.structs.**Cloud**

**base**: *int* = *None*

**direction**: *str* = *None*

**modifier**: *str* = *None*

**repr**: *str*

**top**: *int* = *None*

**type**: *str* = *str*

## class avwx.structs.**Code**

**repr**: *str*

**value**: *str*

## class avwx.structs.**Fraction**

**denominator**: *int*

**normalized**: *str*

**numerator**: *int*

## class avwx.structs.**Icing**

**ceiling**: *avwx.structs.Number* = *None*

**floor**: *avwx.structs.Number* = *None*

**severity**: *str*

**type**: *str* = *None*

## class avwx.structs.**Location**

**direction**: *avwx.structs.Number*

**distance**: *avwx.structs.Number*

**repr**: *str*

**station**: *str*

## class avwx.structs.**Number**

**repr**: *str*

**spoken**: *str*

**value**: *float*

## class avwx.structs.**PressureTendency**

**repr**: *str*

**tendency**: *str*

**change**: *float*

## class avwx.structs.**RemarksData**

**codes**: *List[avwx.structs.Code]* = *[]*

**dewpoint_decimal**: *avwx.structs.Number* = *None*

**maximum_temperature_24**: *avwx.structs.Number* = *None*

**maximum_temperature_6**: *avwx.structs.Number* = *None*

**minimum_temperature_24**: *avwx.structs.Number* = *None*

**minimum_temperature_6**: *avwx.structs.Number* = *None*

**precip_24_hours**: *avwx.structs.Number* = *None*

**precip_36_hours**: *avwx.structs.Number* = *None*

**precip_hourly**: *avwx.structs.Number* = *None*

**pressure_tendency**: *avwx.structs.PressureTendency* = *None*

**sea_level_pressure**: *avwx.structs.Number* = *None*

**snow_depth**: *avwx.structs.Number* = *None*

**sunshine_minutes**: *avwx.structs.Number* = *None*

**temperature_decimal**: *avwx.structs.Number* = *None*

## class avwx.structs.**Timestamp**

**dt**: *datetime.datetime*

**repr**: *str*

## class avwx.structs.**Turbulence**

**ceiling**: *avwx.structs.Number* = *None*

**floor**: *avwx.structs.Number* = *None*

**severity**: *str*

## class avwx.structs.**Units**

**accumulation**: *str*

**altimeter**: *str*

**altitude**: *str*

**temperature**: *str*

**visibility**: *str*

**wind_speed**: *str*


## class avwx.structs.**NbmUnits**:

**accumulation**: *str*

**altimeter**: *str*

**altitude**: *str*

**duration**: *str*

**solar_radiation**: *str*

**temperature**: *str*

**visibility**: *str*

**wave_height**: *str*

**wind_speed**: *str*