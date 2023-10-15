# Report Source Services

AVWX fetches the raw weather reports from third-party services via REST API calls or file downloads. We use Service objects to handle the request and extraction for us.

## Basic Module Use

METARs and TAFs are the most widely-supported report types, so an effort has been made to localize some of these services to a regional source. The `get_service` function was introduced to determine the best service for a given station.

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

Other report types require specific service classes which are found in their respective submodules. However, you can normally let the report type classes handle these services for you.

## Adding a New Service

If the existing services are not supplying the report(s) you need, adding a new service is easy. First, you'll need to determine if your source can be scraped or you need to download a file.

### ScrapeService

For web scraping sources, you'll need to do the following things:

- Add the base URL and method (if not `"GET"`)
- Implement the `ScrapeService._make_url` to return the source URL and query parameters
- Implement the `ScrapeService._extract` function to return just the report string (starting at the station ID) from the response

Let's look at the MAC service as an example:

```python
class MAC(StationScrape):
    """Requests data from Meteorologia Aeronautica Civil for Columbian stations"""

    _url = "http://meteorologia.aerocivil.gov.co/expert_text_query/parse"
    method = "POST"

    def _make_url(self, station: str) -> tuple[str, dict]:
        """Returns a formatted URL and parameters"""
        return self._url, {"query": f"{self.report_type} {station}"}

    def _extract(self, raw: str, station: str) -> str:
        """Extracts the report message using string finding"""
        return self._simple_extract(raw, f"{station.upper()} ", "=")
```

Our URL and query parameters are returned using `_make_url` so `fetch` knows how to request the report. The result of this query is given to `_extract` which returns the report or list of reports.

Once your service is created, it can optionally be added to `avwx.service.scrape.PREFERRED` if the service covers all stations with a known ICAO prefix or `avwx.service.scrape.BY_COUNTRY` if the service covers all stations in a single country. This is how `avwx.service.get_service` determines the preferred service. For example, the MAC service is preferred over NOAA for all ICAOs starting with "SK" while AUBOM is better for all Australian stations.

### FileService

For file-based sources, you'll need to do the following things:

- Add the base URL and valid report types
- Implement the `FileService._urls` to iterate through source URLs
- Implement the `FileService._extract` function to return just the report string (starting at the station ID) from the response

Let's look at the NOAA_NBM service as an example:

```python
class NOAA_NBM(FileService):
    """Requests forecast data from NOAA NBM FTP servers"""

    _url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/blend.{}/{}/text/blend_{}tx.t{}z"
    _valid_types = ("nbh", "nbs", "nbe")

    @property
    def _urls(self) -> Iterator[str]:
        """Iterates through hourly updates no older than two days"""
        date = dt.datetime.now(tz=dt.timezone.utc)
        cutoff = date - dt.timedelta(days=1)
        while date > cutoff:
            timestamp = date.strftime(r"%Y%m%d")
            hour = str(date.hour).zfill(2)
            yield self.url.format(timestamp, hour, self.report_type, hour)
            date -= dt.timedelta(hours=1)

    def _extract(self, station: str, source: TextIO) -> Optional[str]:
        """Returns report pulled from the saved file"""
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
