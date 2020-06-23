# AVWX

[![CircleCI](https://circleci.com/gh/avwx-rest/avwx-engine.svg?style=svg)](https://circleci.com/gh/avwx-rest/avwx-engine)
[![PyPI version](https://badge.fury.io/py/avwx-engine.svg)](https://badge.fury.io/py/avwx-engine)
[![Requirements Status](https://requires.io/github/avwx-rest/avwx-engine/requirements.svg?branch=master)](https://requires.io/github/avwx-rest/avwx-engine/requirements/?branch=master)
[![Documentation Status](https://readthedocs.org/projects/avwx-engine/badge/?version=latest)](http://avwx-engine.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/pypi/l/avwx-engine.svg)](https://pypi.org/project/avwx-engine/)

![AVWX logo](https://avwx.rest/static/favicons/apple-icon-76x76.png)

Aviation Weather for Humans

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

### Model Forecasts

* [GFS MOS MAV](gfs/mav.md)
* [GFS MOS MEX](gfs/mex.md)

### Utilities

* [Station](util/station.md)
* [Service](util/service.md)
* [Other Data Structures](util/structs.md)
* [Static Values](util/static.md)
* [Exceptions](util/exceptions.md)
