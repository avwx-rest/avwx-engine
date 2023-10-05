# AVWX Changelog

Parsing and sanitization improvements are always ongoing and non-breaking

## 1.8.20

- Updated wind sanitization to ensure Station ID is protected.
- Updated unit test to validate fix.

## 1.8.19

- Updated `wx_code()` to parse tokens without translations end up in `other` rather than `wx_codes`.

## 1.8.18

- Added function `fix_report_header()`. Provides additional sanitization of report string to handle cases where the ICAO code is out of order.
- Updated unit tests to reflect changes.

## 1.8.17

- Added optional `m_minus` parameter (bool, defaults to `True`) to `make_number()`, as well as logic changes, to allow for generic parsing of prefixes 'M' as "less than" and 'P' as "greater than" without breaking existing 'M' as "-" logic.
- Added optional `speak_prefix` parameter (str, defaults to "")  to `make_fraction()` to allow `make_number()` to determine "greater than" or "less than" prefix on a fractional value.
- Removes static mappings for strings that utilize "P"/"M" prefixes.
- Updates `get_wind()` and `get_visibility()` to set `m_minus=False` in calls to `make_number()`.
- Updates unit tests to reflect changes.

## 1.8.15

- Added support for TAF forecast times that use a space rather than a forward slash

## 1.8.14

- Added support for `wind_variable_direction` to TAF report forcasts

## 1.8.x

- Added `Notams` report class
- Added `FAA_NOTAM` service class
- Replace `lat, lon` on `Pireps` and service search with `Coord`

## 1.7.x

- Added `AirSigmet` report class and managers
- Added `data` module to update station info client side
- Added `flight_path` module for resolving station and navaid coords
- Added `coord`, `gps`, `local`, `from_code`, `from_gps`, `nearby` to `Station`
- Split `AVWXBase` some functionality into `ManagedReport`
- Dropped 3.7 support

## 1.6.x

- Added station text-based search at `station.search(text)`
- Added `from_iata` class method to `Station`
- Added `relative_humidity`, `pressure_altitude`, and `density_altitude` to `Metar`
- Expanded `RemarksData` parsing scope
- Submodule structure for station
- Mypy type compliance

## 1.5.x

- Added NBM `Nbh`, `Nbs`, and `Nbe` report classes
- Added `ScrapeService`, `FileService`, and `NOAA_NBM` service classes
- Submodule structure for service
- Simplified service API when lat, lon are not used

## 1.4.x

- Added GFS MOS `Mav` and `Mex` report classes
- Added `AVWXBase` and `Code` classes
- Added station ICAO list as `avwx.station.station_list`
- Added `transition_start` to `TafLineData`
- Added `surface` and `lights` to `Runway`
- Added `issued` and `sanitize` to `AVWXBase` classes
- Sub module structure for reports, parsing, and static
- Dropped Python 3.6 support

## 1.3.x

- Added Australian service as `avwx.service.AUBOM`
- Added country code param to `avwx.service.get_service`
- Nearest searches default to airports only

## 1.2.x

- Added `nearest(lat, lon)` and `sends_reports` to `Station`
- Added `nearest(lat, lon, n)` to `station`
- Added lazy loading handling
- Moved `Station`, `uses_na_format`, `valid_station` to `avwx.station`

## 1.1.x

- Added `Pireps` class, module
- Added new fields to `Station`
- Added `from_report(report)` method to `Report`
- Added `Aircraft`, `Turbulence`, `Icing`, `Location`, `PirepData` dataclasses in `avwx.structs`
- Removed `priority` from `Station`

## 1.0.x

- `Metar` and `Taf` classes fully implemented
- Added `Station` class
