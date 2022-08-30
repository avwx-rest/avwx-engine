# Station

This module contains station/airport dataclasses and search functions.

For the purposes of AVWX, a station is any physical location that has an ICAO or GPS identification code. These are usually airports, but smaller locations might not generate certain report types or defer to larger stations nearby. For example, small airports with an AWOS system might not send the report to NOAA or other local authority. They also include remote weather observation stations not associated with airports like weather buouys.

## class avwx.Station

The Station dataclass stores basic info about the desired station and available Runways.

The easiest way to get a station is to supply the ICAO, IATA, or GPS code. The example below uses `from_code` which checks against all three types, but you can also use `from_icao`, `from_iata`, or `from_gps` if you know what type of code you are using. This can be important if you may be using a code used by more than one station depending on the context. ICAO and IATA codes are guarenteed unique, but not all airports have them. That said, all stations available in AVWX have either an ICAO or GPS code.

```python
>>> from avwx import Station
>>> klex = Station.from_code("KLEX")
>>> f"{klex.name} in {klex.city}, {klex.state}"
'Blue Grass Airport in Lexington, KY'
>>> coord = round(klex.latitude, 3), round(klex.longitude, 3)
>>> f"Located at {coord} at {klex.elevation_ft} feet ({klex.elevation_m} meters)"
'Located at (38.036, -84.606) at 979 feet (298 meters)'
>>> rw = max(klex.runways, key=lambda r: r.length_ft)
>>> f"Its longest runway is {rw.ident1}/{rw.ident2} at {rw.length_ft} feet"
'Its longest runway is 04/22 at 7003 feet'
```

This is also the same information you'd get from calling Report.station.

```python
>>> from avwx import Metar
>>> klex = Metar('KLEX')
>>> klex.station.name
'Blue Grass Airport'
```

#### **city**: *str*

#### **coord**: *avwx.structs.Coord*

#### **country**: *str*

#### **distance**(*lat: float, lon: float*) -> *(float, float)*:

Returns the distance in miles and kilometers from a given lat,lon

#### **elevation_ft**: *int*

Elevation in feet

#### **elevation_m**: *int*

Elevation in meters

#### **from_code**(*ident: str*) -> *Station*

Load a Station from an ICAO, GPS, or IATA code in that order

#### **from_gps**(*ident: str*) -> *Station*

Load a Station from a GPS code

#### **from_icao**(*ident: str*) -> *Station*

Load a Station from an ICAO station ident

#### **from_iata**(*ident: str*) -> *Station*

Load a Station from an IATA code

#### **gps**: *Optional[str]*

Station's code for GPS navigation

#### **iata**: *Optional[str]*

Station's 3-char IATA ident

#### **icao**: *Optional[str]*

Station's 4-char ICAO ident

#### **latitude**: *float*

#### **local**: Optional[str]*

Station's code assigned by its local authority

#### **longitude**: *float*

#### **lookup_code**: *str*

Returns the ICAO or GPS code for report fetch

#### **name**: *str*

Station / airport name

#### **nearby**(*is_airport: bool = False, sends_reports: bool = True, max_coord_distance: float = 10*) -> *[(T, dict)]*:

Returns Stations nearest to current station and their distances

NOTE: Becomes less accurate toward poles and doesn't cross +/-180

#### **nearest**(*lat: float = None, lon: float = None, is_airport: bool = False, sends_reports: bool = True max_distance: float = 50*) -> *(avwx.Station, dict)*

Load the Station nearest to your location or a lat,lon coordinate pair

Returns the Station and distances from source

NOTE: Becomes less accurate toward poles and doesn't cross +/-180

#### **note**: *str*

Location notes like nearby landmarks

#### **runways**: *[avwx.station.Runway]*

List of available Runway objects sorted longest to shortest

#### **sends_reports**: *bool*

Returns whether or not a Station likely sends weather reports

#### **state**: *str*

#### **type**: *str*

Station / airport type like `"large_airport"`

#### **website**: *str*

Station / airport primary website

#### **wiki**: *str*

Station Wikipedia page

## class avwx.station.Runway

Represents a runway at an airport

#### **length_ft**: *int*

Runway length in feet

#### **width_ft**: *int*

Runway width in feet

#### **ident1**: str

Runway number 01-18 with modifiers. Ex: `"17L"`

#### **ident2**: str

Runway number 19-36 with modifiers. Ex: `"35R"`

## avwx.station.**station_list**(*reporting: bool = True*) -> *[str]*:

Returns a list of station idents matching the search criteria

## avwx.station.**nearest**(*lat: float, lon: float, n: int = 1, is_airport: bool = False, sends_reports: bool = True, max_distance: float = 10*) -> *[dict]*

Finds the nearest n Stations to a lat,lon coordinate pair

Returns the Station and coordinate distance from source

NOTE: Becomes less accurate toward poles and doesn't cross +/-180
