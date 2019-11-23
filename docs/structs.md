# Data Structures

## class avwx.structs.**Aircraft**

### **code**: *str*

### **from_icao**(*code: str*) -> *avwx.structs.Aircraft*

Load an Aircraft from an ICAO aircraft code

### **type**: *str*

## class avwx.structs.**Cloud**

### **base**: *int* = *None*

### **direction**: *str* = *None*

### **modifier**: *str* = *None*

### **repr**: *str*

### **top**: *int* = *None*

### **type**: *str* = *str*

## class avwx.structs.**Fraction**

### **denominator**: *int*

### **normalized**: *str*

### **numerator**: *int*

## class avwx.structs.**Icing**

### **ceiling**: *avwx.structs.Number* = *None*

### **floor**: *avwx.structs.Number* = *None*

### **severity**: *str*

### **type**: *str* = *None*

## class avwx.structs.**Location**

### **direction**: *avwx.structs.Number*

### **distance**: *avwx.structs.Number*

### **repr**: *str*

### **station**: *str*

## class avwx.structs.**MetarData**

### **altimeter**: *avwx.structs.Number*

### **clouds**: *[avwx.structs.Cloud]*

### **dewpoint**: *avwx.structs.Number*

### **flight_rules**: *str*

### **other**: *[str]*

### **raw**: *str*

### **remarks**: *str*

### **remarks_info**: *avwx.structs.RemarksData*

### **runway_visibility**: *[str]*

### **sanitized**: *str*

### **station**: *str*

### **temperature**: *avwx.structs.Number*

### **time**: *avwx.structs.Timestamp*

### **visibility**: *avwx.structs.Number*

### **wind_direction**: *avwx.structs.Number*

### **wind_gust**: *avwx.structs.Number*

### **wind_speed**: *avwx.structs.Number*

### **wind_variable_direction**: *avwx.structs.Number*

## class avwx.structs.**MetarTrans**

### **altimeter**: *str*

### **clouds**: *str*

### **dewpoint**: *str*

### **other**: *str*

### **remarks**: *dict*

### **temperature**: *str*

### **visibility**: *str*

### **wind**: *str*

## class avwx.structs.**Number**

### **repr**: *str*

### **spoken**: *str*

### **value**: *float*

## class avwx.structs.**PirepData**

### **aircraft**: *avwx.structs.Aircraft* = *None*

### **altitude**: *avwx.structs.Number* = *None*

### **clouds**: *[avwx.structs.Cloud]*

### **flight_visibility**: *avwx.structs.Number* = *None*

### **icing**: *avwx.structs.Icing* = *None*

### **location**: *avwx.structs.Location* = *None*

### **raw**: *str*

### **remarks**: *str*

### **sanitized**: *str*

### **station**: *str*

### **temperature**: *avwx.structs.Number* = *None*

### **time**: *avwx.structs.Timestamp*

### **turbulence**: *avwx.structs.Turbulence* = *None*

### **type**: *str*

### **wx**: *[str]*

## class avwx.structs.**RemarksData**

### **dewpoint_decimal**: *float* = *None*

### **temperature_decimal**: *float* = *None*

## class avwx.structs.**TafData**

### **alts**: *str* = *None*

### **end_time**: *avwx.structs.Timestamp*

### **forecast**: *[avwx.structs.TafLineData]*

### **max_temp**: *float* = *None*

### **min_temp**: *float* = *None*

### **raw**: *str*

### **remarks**: *str*

### **start_time**: *avwx.structs.Timestamp*

### **station**: *str*

### **temps**: *[str]* = *None*

### **time**: *avwx.structs.Timestamp*

## class avwx.structs.**TafLineData**

### **altimeter**: *avwx.structs.Number*

### **clouds**: *[avwx.structs.Cloud]*

### **end_time**: *avwx.structs.Timestamp*

### **flight_rules**: *str*

### **icing**: *[str]*

### **other**: *[str]*

### **probability**: *avwx.structs.Number*

### **raw**: *str*

### **sanitized**: *str*

### **start_time**: *avwx.structs.Timestamp*

### **turbulence**: *[str]*

### **type**: *str*

### **visibility**: *avwx.structs.Number*

### **wind_direction**: *avwx.structs.Number*

### **wind_gust**: *avwx.structs.Number*

### **wind_shear**: *str*

### **wind_speed**: *avwx.structs.Number*

## class avwx.structs.**TafLineTrans**

### **altimeter**: *str*

### **clouds**: *str*

### **icing**: *str*

### **other**: *str*

### **turbulence**: *str*

### **visibility**: *str*

### **wind**: *str*

### **wind_shear**: *str*

## class avwx.structs.**TafTrans**

### **forecast**: *[avwx.structs.TafLineTrans]*

### **max_temp**: *str*

### **min_temp**: *str*

### **remarks**: *dict*

## class avwx.structs.**Timestamp**

### **dt**: *datetime.datetime*

### **repr**: *str*

## class avwx.structs.**Turbulence**

### **ceiling**: *avwx.structs.Number* = *None*

### **floor**: *avwx.structs.Number* = *None*

### **severity**: *str*

## class avwx.structs.**Units**

### **altimeter**: *str*

### **altitude**: *str*

### **temperature**: *str*

### **visibility**: *str*

### **wind_speed**: *str*
