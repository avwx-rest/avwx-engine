# AVWX Changelog

Parsing and sanitization improvements are always ongoing and non-breaking

## 1.6

- Added station text-based search at `station.search(text)`
- Submodule structure for station

## 1.5

- Added NBM `Nbh`, `Nbs`, and `Nbe` report classes
- Added `ScrapeService`, `FileService`, and `NOAA_NBM` service classes
- Submodule structure for service
- Simplified service API when lat, lon are not used

## 1.4

- Added GFS MOS `Mav` and `Mex` report classes
- Added `AVWXBase` and `Code` classes
- Added station ICAO list as `avwx.station.station_list`
- Added `transition_start` to `TafLineData`
- Added `surface` and `lights` to `Runway`
- Added `issued` and `sanitize` to `AVWXBase` classes
- Sub module structure for reports, parsing, and static
- Dropped Python 3.6 support

## 1.3

- Added Australian service as `avwx.service.AUBOM`
- Added country code param to `avwx.service.get_service`
- Nearest searches default to airports only

## 1.2

- Added `nearest(lat, lon)` and `sends_reports` to `Station`
- Added `nearest(lat, lon, n)` to `station`
- Added lazy loading handling
- Moved `Station`, `uses_na_format`, `valid_station` to `avwx.station`

## 1.1

- Added `Pireps` class, module
- Added new fields to `Station`
- Added `from_report(report)` method to `Report`
- Added `Aircraft`, `Turbulence`, `Icing`, `Location`, `PirepData` dataclasses in `avwx.structs`
- Removed `priority` from `Station`

## 1.0

- `Metar` and `Taf` classes fully implemented
- Added `Station` class
