# AVWX

[![PyPI version](https://badge.fury.io/py/avwx-engine.svg)](https://badge.fury.io/py/avwx-engine)
[![Requirements Status](https://requires.io/github/avwx-rest/AVWX-Engine/requirements.svg?branch=master)](https://requires.io/github/avwx-rest/AVWX-Engine/requirements/?branch=master)
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

These docs could use some love, and I am not a writer. You can help by making a pull request on [GitHub](https://github.com/avwx-rest/AVWX-Engine)

## Contents

* [Getting Started](getting-started.md)
* [Station](station.md)
* [METAR](metar.md)
* [TAF](taf.md)
* [PIREP](pirep.md)
* [Service](service.md)
* [Static Values](static.md)
* [Data Structures](structs.md)
* [Parsing](parsing.md)
* [Exceptions](exceptions.md)
