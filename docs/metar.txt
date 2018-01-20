=====
METAR
=====

.. toctree::
   :maxdepth: 2
   :caption: Contents:

A METAR (Meteorological Aerodrome Report) is the surface weather observed at most controlled (and some uncontrolled) airports. They are updated once per hour or when conditions change enough to warrant an update, and the observations are valid for one hour after the report was issued or until the next report is issued.

.. autoclass:: avwx.Metar
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