# Report Source Services

AVWX fetches the raw weather reports from third-party services via REST API calls. We use Service objects to handle the request and extraction for us.

## Basic Module Use

### avwx.service.**get_service**(*station: str*) -> *avwx.service.Service*

Returns the preferred service for a given station

```python
station = 'KJFK'
# Get the station's preferred service and initialize to fetch METARs
service = avwx.service.get_service(station)('metar')
# Fetch the current METAR
report = service.fetch(station)
```

## Service Classes

Services are based off of the Service class and should all return the final report string with the fetch method.

### class avwx.service.**Service**(*request_type: str*)

Base Service class for fetching reports

#### **fetch**(*station: str = None, lat: float = None, lon: float = None*) -> *str*

Fetches a report string from the service

#### **async_fetch**(*station: str = None, lat: float = None, lon: float = None*) -> *str*

Asynchronously fetch a report string from the service

### class avwx.service.**NOAA**(*request_type: str*)

Requests data from NOAA ADDS

### avwx.service.**AMO**(*request_type: str*)

Requests data from AMO KMA for Korean stations

### avwx.service.**MAC**(*request_type: str*)

Requests data from Meteorologia Aeronautica Civil for Columbian stations

## Adding a New Service

If the existing services are not supplying the report(s) you need, adding a new service is easy. You'll need to do the following things:

- Add the base URL and method
- Implement the Service._make_url to return the source URL and query parameters
- Implement the Service._extract function to return just the report string (starting at the station ID) from the response

Let's look at the MAC service as an example:

```python
class MAC(Service):
"""
Requests data from Meteorologia Aeronautica Civil for Columbian stations
"""

url = "http://meteorologia.aerocivil.gov.co/expert_text_query/parse"
method = "POST"

def _make_url(self, station: str, lat: float, lon: float) -> (str, dict):
    """
    Returns a formatted URL and parameters
    """
    return self.url, {"query": f"{self.rtype} {station}"}

def _extract(self, raw: str, station: str) -> str:
    """
    Extracts the reports message using string finding
    """
    report = raw[raw.find(station.upper() + " ") :]
    report = report[: report.find(" =")]
    return report
```

Our URL and query parameters are returned using Service._make_url so Service.fetch knows how to request the report. The result of this query is given to Service._extract which returns the report or list of reports.

Once your service is created, it can optionally be added to the dictionary of preferred services, avwx.service.PREFERRED. This is how avwx.service.get_service determines the preferred service for a given station. This should only be done if it is the primary service for a group of station IDs with the same prefix. For example, the MAC service is better than NOAA for all ICAOs starting with "SK".
