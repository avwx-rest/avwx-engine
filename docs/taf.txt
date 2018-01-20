===
TAF
===

.. toctree::
   :maxdepth: 2
   :caption: Contents:

A TAF (Terminal Aerodrome Forecast) is a 24-hour weather forecast for the area 5 statute miles from 

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