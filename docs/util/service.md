# Report Source Services

AVWX fetches the raw weather reports from third-party services via REST API calls or file downloads. We use Service objects to handle the request and extraction for us.

## Basic Module Use

METARs and TAFs are the most widely-supported report types, so an effort has been made to localize some of these services to a regional source. The `get_service` function was introduced to determine the best service for a given station.

### avwx.service.**get_service**(*station: str, country: str*) -> *avwx.service.Service*

Returns the preferred scrape service for a given station

```python
# Fetch Australian reports
station = 'YWOL'
country = 'AU' # can source from avwx.Station.country
# Get the station's preferred service and initialize to fetch METARs
service = avwx.service.get_service(station, country)('metar')
# service is now avwx.service.AUBOM init'd to fetch METARs
# Fetch the current METAR
report = service.fetch(station)
```

Other report types require specific service classes which are detailed below.

## Base Service Class

Both web scrape and file-based services are based off of the Service class and should all return the final report string with the fetch method.

### class avwx.service.**Service**(*report_type: str*)

Base Service class for fetching reports

#### **fetch**(*station: str, timeout: int = 10*) -> *str*

Fetches a report string from the service

#### async **async_fetch**(*station: str, timeout: int = 10*) -> *str*

Asynchronously fetch a report string from the service

## Web Scrape Services

These services request reports via HTML scraping or direct API requests. Requests are ephemeral and will call the selected service each time.

### class.service.scrape.**ScrapeService**(*report_type: str*)

Service class for fetching reports via direct web requests

Unless overwritten, this class accepts `"metar"` and `"taf"` as valid report types

### class avwx.service.**NOAA**(*report_type: str*)

Requests data from NOAA

### class avwx.service.**NOAA_ADDS**(*report_type: str*)

Requests data from NOAA ADDS

This class accepts `"metar"`, `"taf"`, and `"aircraftreport"` as valid report types. It will also accept `lat` and `lon` as fetch parameters in addition to `station`.

### avwx.service.**AMO**(*report_type: str*)

Requests data from AMO KMA for Korean stations

### avwx.service.**MAC**(*report_type: str*)

Requests data from Meteorologia Aeronautica Civil for Columbian stations

### avwx.service.**AUBOM**(*report_type: str*)

Requests data from the Australian Bureau of Meteorology

## File Services

These services are directed at FTP servers to find the most recent file associated with the search criteria. Files are stored in a temporary directory which is deleted when the program ends. Fetch requests will extract reports from the downloaded file until an update interval has been exceeded, at which point the service will check for a newer file. You can also have direct access to all downloaded reports.

### avwx.service.files.FileService(*report_type*)

Service class for fetching reports via managed source files

#### **all**: *List[str]*

#### **is_outdated**: *bool*

#### **last_updated**: *Optional[datetime.datetime]*

#### **update_interval**: *datetime.timedelta = datetime.timedelta(minutes=10)*

#### async **update**(*wait: bool = False, timeout: int = 10*) -> *bool*

Update the stored file and returns success

If wait, this will block if the file is already being updated

#### **fetch**(*station: str, wait: bool = True, timeout: int = 10, force: bool = False*) -> Optional[str]

Fetch a report string from the source file

If wait, this will block if the file is already being updated

Can force the service to fetch a new file

#### async **async_fetch**(*station: str, wait: bool = True, timeout: int = 10, force: bool = False*) -> Optional[str]

Asynchronously fetch a report string from the source file

If wait, this will block if the file is already being updated

Can force the service to fetch a new file

### avwx.service.NOAA_NBM(*report_type*)

Requests forecast data from NOAA NBM FTP servers

This class accepts `"nbh"`, `"nbs"`, and `"nbe"` as valid report types

### avwx.service.NOAA_GFS(*report_type*)

Requests forecast data from NOAA GFS FTP servers

This class accepts `"mav"` and `"mex"` as valid report types

## Bulk Services

These services are specifically for returning multiple reports at a time. For example, we'd want to know all SIGMETs currently in circulation. The sources can be FTP, scraping, or any other method. There is no need for specific stations or updating files behind the scenes.

The `fetch` and `async_fetch` methods are identical except they return `List[str]` instead.

### avwx.service.bulk.NOAA_Bulk(*report_type*)

Requests data from NOAA FTP file servers

This class accepts `"metar"`, `"taf"`, `"aircraftreport"`, and `"airsigmet"` as valid report types.

### avwx.service.bulk.NOAA_Bulk(*report_type*)

Scrapes international reports from NOAA. Designed to accompany `NOAA_Bulk` for AIRMET / SIGMET fetch.

Currently, this class only accepts `"airsigmet"` as a valid report type.

## Adding a New Service

If the existing services are not supplying the report(s) you need, adding a new service is easy. First, you'll need to determine if your source can be scraped or you need to download a file.

### ScrapeService

For web scraping sources, you'll need to do the following things:

- Add the base URL and method (if not `"GET"`)
- Implement the `ScrapeService._make_url` to return the source URL and query parameters
- Implement the `ScrapeService._extract` function to return just the report string (starting at the station ID) from the response

Let's look at the MAC service as an example:

```python
class MAC(ScrapeService):
"""
Requests data from Meteorologia Aeronautica Civil for Columbian stations
"""

url = "http://meteorologia.aerocivil.gov.co/expert_text_query/parse"
method = "POST"

def _make_url(self, station: str) -> (str, dict):
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

Our URL and query parameters are returned using `_make_url` so `fetch` knows how to request the report. The result of this query is given to `_extract` which returns the report or list of reports.

Once your service is created, it can optionally be added to `avwx.service.scrape.PREFERRED` if the service covers all stations with a known ICAO prefix or `avwx.service.scrape.BY_COUNTRY` if the service covers all stations in a single country. This is how `avwx.service.get_service` determines the preferred service. For example, the MAC service is preferred over NOAA for all ICAOs starting with "SK" while AUBOM is better for all Australian stations.

### FileService

For web scraping sources, you'll need to do the following things:

- Add the base URL and valid report types
- Implement the `FileService._urls` to iterate through source URLs
- Implement the `FileService._extract` function to return just the report string (starting at the station ID) from the 

Let's look at the NOAA_NBM service as an example:

```python
class NOAA_NBM(FileService):
    """
    Requests forecast data from NOAA NBM FTP servers
    """

    url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/blend.{}/{}/text/blend_{}tx.t{}z"
    _valid_types = ("nbh", "nbs", "nbe")

    @property
    def _urls(self) -> Iterator[str]:
        """
        Iterates through hourly updates no older than two days
        """
        date = dt.datetime.now(tz=dt.timezone.utc)
        cutoff = date - dt.timedelta(days=1)
        while date > cutoff:
            timestamp = date.strftime(r"%Y%m%d")
            hour = str(date.hour).zfill(2)
            yield self.url.format(timestamp, hour, self.report_type, hour)
            date -= dt.timedelta(hours=1)

    def _extract(self, station: str, source: TextIO) -> Optional[str]:
        """
        Returns report pulled from the saved file
        """
        start = station + "   "
        end = self.report_type.upper() + " GUIDANCE"
        txt = source.read()
        txt = txt[txt.find(start) :]
        txt = txt[: txt.find(end, 30)]
        lines = []
        for line in txt.split("\n"):
            if "CLIMO" not in line:
                line = line.strip()
            if not line:
                break
            lines.append(line)
        return "\n".join(lines) or None
```

In this example, we iterate through `_urls` looking for the most recent published file. URL iterators should always have a lower bound to stop iteration so the service can return a null response.

Once the file is downloaded, the requested station and file-like object are passed to the `_extract` method to find and return the report from the file. This method will not be called if the file doesn't exist.
