# AVWX Changelog

Parsing and sanitization improvements are always ongoing and non-breaking

## 1.1

- Added `Pireps` class, module
- Added new fields to `Station`
- Added `from_report` method to `Report`
- Added `Aircraft`, `Turbulance`, `Icing`, `Location`, `PirepData` dataclasses in `avwx.structs`
- Removed `priority` from `Station`

## 1.0

- `Metar` and `Taf` classes fully implemented
- Added `Station` class
