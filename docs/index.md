# AVWX

![AVWX logo](assets/images/avwx-logo-color-200.png)

[![PyPI](https://img.shields.io/pypi/v/avwx-engine?style=flat)](https://pypi.python.org/pypi/avwx-engine/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/avwx-engine?style=flat)](https://pypi.python.org/pypi/avwx-engine/)
[![PyPI - License](https://img.shields.io/pypi/l/avwx-engine?style=flat)](https://pypi.python.org/pypi/avwx-engine/)
[![GitHub - Test Suite Status](https://github.com/avwx-rest/avwx-engine/actions/workflows/test.yml/badge.svg)]()

AVWX is a global aviation weather fetching and parsing engine. It sources reports from a variety of government sources, parses individual elements, and calculates additional information like flight rules and time range interpolation.

AVWX currently supports:

- Station data and search
- METAR
- TAF
- PIREP
- AIRMET / SIGMET
- NOTAM
- NBM (NBH, NBS, NBE)
- GFS (MAV, MEX)

```python
>>> import avwx
>>> jfk_metar = avwx.Metar('KJFK')
>>> jfk_metar.update()
True
>>> jfk_metar.data.flight_rules
'VFR'
```

These docs could use some love, and I am not a writer. You can help by making a pull request on [GitHub](https://github.com/avwx-rest/avwx-engine)

## Contents

* [Getting Started](getting-started.md)

### Aviation Reports

* [METAR](av/metar.md)
* [TAF](av/taf.md)
* [PIREP](av/pirep.md)
* [AIRMET / SIGMET](av/airsigmet.md)
* [NOTAM](av/notam.md)

### Model Forecasts

* [NBM NBH](nbm/nbh.md)
* [NBM NBS](nbm/nbs.md)
* [NBM NBE](nbm/nbe.md)
* [GFS MOS MAV](gfs/mav.md)
* [GFS MOS MEX](gfs/mex.md)

### Utilities

* [Station](util/station.md)
* [Service](util/service.md)
* [Data Updates](util/data.md)
* [Other Data Structures](util/structs.md)
* [Static Values](util/static.md)
* [Exceptions](util/exceptions.md)
