=======
Station
=======

.. toctree::
   :maxdepth: 2
   :caption: Contents:

For the purposes of AVWX, a station is any location with an ICAO code. These are usually airports, but smaller locations might not generate certain report types or defer to larger stations nearby. For example, small airports with an AWOS system might not send the report to NOAA.

Station Class
-------------

The Station data class stores basic info about the desired station and available Runways.

The easiest way to get a station is to supply the ICAO code.

.. code-block:: python

  >>> from avwx import Station
  >>> klex = Station.from_icao('KLEX')
  >>> f"{klex.name} in {klex.city}, {klex.state}"
  'Blue Grass Airport in Lexington, KY'
  >>> coord = round(klex.latitude, 3), round(klex.longitude, 3)
  >>> f"Located at {coord} at {klex.elevation_ft} feet ({klex.elevation_m} meters)"
  'Located at (38.036, -84.606) at 979 feet (298 meters)'
  >>> rw = max(klex.runways, key=lambda r: r.length_ft)
  >>> f"Its longest runway is {rw.ident1}/{rw.ident2} at {rw.length_ft} feet"
  'Its longest runway is 04/22 at 7003 feet'

This is also the same information you'd get from calling Report.station_info.

.. code-block:: python

  >>> from avwx import Metar
  >>> klex = Metar('KLEX')
  >>> klex.station_info.name
  'Blue Grass Airport'

.. autoclass:: avwx.Station
   :members: from_icao, nearest, sends_reports

   .. attribute:: city: str
   .. attribute:: country: str
   .. attribute:: elevation_ft: int
   .. attribute:: elevation_m: int
   .. attribute:: iata: str
   .. attribute:: icao: str
   .. attribute:: latitude: float
   .. attribute:: longitude: float
   .. attribute:: name: str
   .. attribute:: note: str
   .. attribute:: runways: [avwx.structs.Runway]
   .. attribute:: state: str
   .. attribute:: type: str
   .. attribute:: website: str
   .. attribute:: wiki: str

Standalone Functions
--------------------

.. automodule:: avwx.station
   :members: nearest, uses_na_format, valid_station
