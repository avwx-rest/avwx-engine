=====
METAR
=====

.. toctree::
   :maxdepth: 2
   :caption: Contents:

A METAR (Meteorological Aerodrome Report) is the surface weather observed at most controlled (and some uncontrolled) airports. They are updated once per hour or when conditions change enough to warrant an update, and the observations are valid for one hour after the report was issued or until the next report is issued.

Metar Class
-----------

The Metar class offers an object-oriented approach to managing METAR data for a single station.

.. autoclass:: avwx.Metar
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

  .. attribute:: speech: str

    Report summary designed to be read by a text-to-speech program

  .. attribute:: station_info: {str: object}

    Provide basic station info. Raises a BadStation exception if the station's info cannot be found

  .. attribute:: summary: str

    Condensed report summary created from translations

  .. attribute:: translations: {str: object}

    Dictionary of translation strings from data. Parsed on update()

Standalone Functions
--------------------

If you don't need or want the object-oriented handling provided by the Metar class, you can use the core METAR functions directly.

.. automodule:: avwx.metar
   :members: