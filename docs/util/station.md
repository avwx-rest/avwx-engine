# Station

This module contains station/airport dataclasses and search functions.

For the purposes of AVWX, a station is any location that has an ICAO identification code. These are usually airports, but smaller locations might not generate certain report types or defer to larger stations nearby. For example, small airports with an AWOS system might not send the report to NOAA. They also include remote weather observation stations not associated with airports.

## class avwx.Station

The Station dataclass stores basic info about the desired station and available Runways.

The easiest way to get a station is to supply the ICAO code. IATA codes will also work with `from_iata`.

```python
>>> from avwx import Station
>>> klex = Station.from_icao('KLEX')
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

#### **from_icao**(*ident: str*) -> *Station*

Load a Station from an ICAO station ident

#### **from_iata**(*ident: str*) -> *Station*

Load a Station from an IATA code

#### **iata**: *str*

Station's 3-char IATA ident

#### **icao**: *str*

Station's 4-char ICAO ident

#### **latitude**: *float*

#### **longitude**: *float*

#### **name**: *str*

Station / airport name

#### **nearest**(*lat: float, lon: float, is_airport: bool = False, sends_reports: bool = True max_distance: float = 50*) -> *(avwx.Station, dict)*

Load the Station nearest to a lat,lon coordinate pair

Returns the Station and coordinate distance from source

NOTE: Becomes less accurate toward poles and doesn't cross +/-180

#### **note**: *str*

Location notes like nearby landmarks

#### **runways**: *[avwx.station.Runway]*

List of available Runway objects sorted longest to shortest

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
