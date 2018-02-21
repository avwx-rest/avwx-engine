======================
Report Source Services
======================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


AVWX fetches the raw weather reports from third-party services via REST API calls. We use Service objects to handle the request and extraction for us.

Basic Usage
-----------

.. autofunction:: avwx.service.get_service

Example:

.. code-block:: python

   station = 'KJFK'
   # Get the station's preferred service and initialize to fetch METARs
   service = avwx.service.get_service(station)('metar')
   # Fetch the current METAR
   report = service.fetch(station)

Service Classes
---------------

Services are based off of the Service class and should all return the final report string with the fetch method.

.. autoclass:: avwx.service.Service
   :members: fetch, make_err, _extract

.. autoclass:: avwx.service.NOAA

.. autoclass:: avwx.service.AMO


Adding a New Service
--------------------

If the existing services are not supplying the report(s) you need, adding a new service is easy. You'll need to do the following things:

- Create a URL which takes the report type and station strings
- Implement the _extract function to return just the report string (starting at the station ID) from the response

Let's look at the AMO service as an example:

.. code-block:: python

   class AMO(Service):
       """
       Requests data from AMO KMA for Korean stations
       """
   
       url = 'http://amoapi.kma.go.kr/amoApi/{0}?icao={1}'
   
       def _extract(self, raw: str) -> str:
           """
           Extracts the report message from XML response
           """
           resp = parsexml(raw)
           try:
               report = resp['response']['body']['items']['item'][self.rtype.lower() + 'Msg']
           except:
               raise self.make_err(raw)
           # Replace line breaks
           report = report.replace('\n', '')
           # Remove excess leading and trailing data
           report = report.lstrip(self.rtype.upper()).rstrip('=')
           # Make every element single-spaced and stripped
           return ' '.join(report.split())

Our URL will be formatted with the report type (0) and the station ID (1). The _extract function is given the raw response body, extracts the report string from the parsed XML, and removes the excess data that this particular API adds to the response.

Once your service is created, it can optionally be added to the dictionary of preferred services, avwx.service.PREFERRED. This is how avwx.service.get_service determines the preferred service for a given station. This should only be done if it is the primary service for a group of station IDs with the same prefix. For example, the AMO service is better than NOAA for all ICAOs starting with "RK".
