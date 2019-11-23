# AVWX Changelog

Parsing and sanitization improvements are always ongoing and non-breaking

## 1.3

- Add Australian service as `avwx.service.AUBOM`
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
