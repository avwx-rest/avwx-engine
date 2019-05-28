=====
PIREP
=====

.. toctree::
   :maxdepth: 2
   :caption: Contents:

A PIREP (Pilot Report) is an observation made by pilots inflight meant to aid controllers and pilots routing around adverse conditions and other conditions of note. They typically contain icing, turbulance, cloud types/bases/tops, and other info at a known distance and radial from a ground station. They are released as they come in.

Pireps Class
------------

The Pireps class offers an object-oriented approach to managing multiple PIREP reports for a single station.

Below is typical usage for fetching and pulling PIREP data for KJFK.

.. code-block:: python

  >>> from avwx import Pireps
  >>> kmco = Pireps('KMCO')
  >>> kmco.station_info.name
  'Orlando International Airport'
  >>> kmco.update()
  True
  >>> kmco.last_updated
  datetime.datetime(2019, 5, 24, 13, 31, 46, 561732)
  >>> kmco.raw[0]
  'FLL UA /OV KFLL275015/TM 1241/FL020/TP B737/SK TOP020/RM DURD RY10L'
  >>> kmco.data[0].location
  Location(repr='KFLL275015', station='KFLL', direction=Number(repr='275', value=275, spoken='two seven five'), distance=Number(repr='015', value=15, spoken='one five'))

The update function can also accept a given report string if you want to override to normal fetching process. Here's an example of a really bad day.

.. code-block:: python

  >>> from avwx import Metar
  >>> ksfo = Metar('KSFO')
  >>> ksfo.station_info.city
  'San Francisco'
  >>> report = 'KSFO 031254Z 36024G55KT 320V040 1/8SM R06/0200D +TS VCFC OVC050 BKN040TCU 14/10 A2978 RMK AIRPORT CLOSED'
  >>> ksfo.update(report)
  True
  >>> ksfo.last_updated
  datetime.datetime(2018, 3, 4, 23, 54, 4, 353757)
  >>> ksfo.data.flight_rules
  'LIFR'
  >>> ksfo.translations.clouds
  'Broken layer at 4000ft (Towering Cumulus), Overcast layer at 5000ft - Reported AGL'
  >>> ksfo.summary
  'Winds N-360 (variable 320 to 040) at 24kt gusting to 55kt, Vis 0.125sm, Temp 14C, Dew 10C, Alt 29.78inHg, Heavy Thunderstorm, Vicinity Funnel Cloud, Broken layer at 4000ft (Towering Cumulus), Overcast layer at 5000ft'

.. autoclass:: avwx.Pireps
  :members: async_update, update

  .. attribute:: data: [avwx.structs.PirepData]

    List of PirepData dataclasses of parsed data values and units. Parsed on update()

  .. attribute:: last_updated: datetime.datetime

    UTC Datetime object when the reports were last updated

  .. attribute:: lat: float

    Latitude of the radial center. This is supplied by the user or loaded from the station

  .. attribute:: lon: float

    Longitude of the radial center. This is supplied by the user or loaded from the station

  .. attribute:: raw: [str]

    The unparsed report strings. Fetched on update()

  .. attribute:: station: str

    4-character ICAO station ident code the object was initialized with. Reports will fall within a certain radial distance of this station

  .. attribute:: service: avwx.service.Service

    Service object used to fetch the report strings

  .. attribute:: station_info: avwx.structs.StationInfo

    Provides basic station info. Raises a BadStation exception if the station's info cannot be found

Standalone Functions
--------------------

If you don't need or want the object-oriented handling provided by the Pireps class, you can use the core PIREP functions directly.

.. automodule:: avwx.pirep
   :members: