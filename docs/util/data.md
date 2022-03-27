# Data Updates

Certain components of AVWX rely on data files compiled from remote sources that should be kept up to date. This includes:

- Station information database
- Navigation aids
- Aircraft codes

While these are updated on a regular basis with point updates, you may wish to update them on a more frequent basis. As of version 1.7 of the library, you can do this manually with the `data` module.

```python
>>> from avwx.data import update_all
>>> update_all()
True
```

This updates all package data files and `avwx.station.meta.__STATIONS_UPDATED__` date. Due to how this data is managed, you should only run updates prior to starting your primary Python application. Doing so during an existing run may still use old data depending on the architecture of your program.

## avwx.data.**update_all() -> *bool*

Update all local data. Requires a reimport to guarentee update

## avwx.data.**update_aircraft() -> *bool*

Builds the aircraft code dict

## avwx.data.**update_navaids() -> *bool*

Builds the navaid coordinate map

## avwx.data.**update_stations() -> *bool*

Builds the station information database
