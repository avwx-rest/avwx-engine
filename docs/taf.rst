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
  :inherited-members:

  .. method:: last_updated: datetime.datetime

    UTC Datetime object when the report was last updated

  .. method:: raw: str

    The unparsed report string

  .. method:: data: {str: object}

    Dictionary of parsed data values and units

  .. method:: translations: {str: object}

    Dictionary of element translations

  .. method:: station: str

    Station ICAO the report was initialized with

  .. method:: service: avwx.service.Service

    Service object used to fetch the report

  .. method:: summary: str

    Condensed report summary created from translations

  .. method:: speech: str

    Report summary designed to be read by a text-to-speech program

Standalone Functions
--------------------

If you don't need or want the object-oriented handling provided by the Taf class, you can use the core TAF functions directly.

.. automodule:: avwx.taf
   :members: