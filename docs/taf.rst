===
TAF
===

.. toctree::
   :maxdepth: 2
   :caption: Contents:

A TAF (Terminal Aerodrome Forecast) is a 24-hour weather forecast for the area 5 statute miles from the reporting station. They are update once every three or six hours or when significant changes warrent an update, and the observations are valid for six hours or until the next report is issued

Taf Class
---------

The Taf class offers an object-oriented approach to managing TAF data for a single station.

.. autoclass:: avwx.Taf
  :members: update

  .. attribute:: data: {str: object}

    Dictionary of parsed data values and units. Parsed on update()

  .. attribute:: last_updated: datetime.datetime

    UTC Datetime object when the report was last updated

  .. attribute:: raw: str

    The unparsed report string. Fetched on update()

  .. attribute:: station: str

    4-character ICAO station ident code the report was initialized with

  .. attribute:: service: avwx.service.Service

    Service object used to fetch the report string

  .. attribute:: station_info: {str: object}

    Provide basic station info. Raises a BadStation exception if the station's info cannot be found

  .. attribute:: summary: str

    Condensed report summary created from translations

  .. attribute:: translations: {str: object}

    Dictionary of translation strings from data. Parsed on update()

Standalone Functions
--------------------

If you don't need or want the object-oriented handling provided by the Taf class, you can use the core TAF functions directly.

.. automodule:: avwx.taf
   :members: