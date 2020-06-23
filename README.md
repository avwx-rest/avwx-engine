# AVWX: Aviation Weather for Humans

[![CircleCI](https://circleci.com/gh/avwx-rest/avwx-engine.svg?style=svg)](https://circleci.com/gh/avwx-rest/avwx-engine)
[![PyPI version](https://badge.fury.io/py/avwx-engine.svg)](https://badge.fury.io/py/avwx-engine)
[![Requirements Status](https://requires.io/github/avwx-rest/avwx-engine/requirements.svg?branch=master)](https://requires.io/github/avwx-rest/avwx-engine/requirements/?branch=master)
[![Documentation Status](https://readthedocs.org/projects/avwx-engine/badge/?version=latest)](http://avwx-engine.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/pypi/l/avwx-engine.svg)](https://pypi.org/project/avwx-engine/)

![AVWX logo](https://avwx.rest/static/favicons/apple-icon-76x76.png)

## Install

The easiest way to get started is to download the library from pypi using pip:

```bash
python -m pip install avwx-engine
```

## Basic Usage

Reports use ICAO idents when specifying the desired station. Exceptions are thrown if a potentially invalid ident is given.

```python
>>> import avwx
>>>
>>> metar = avwx.Metar('KJFK')
>>> metar.station.name
'John F Kennedy International Airport'
>>> metar.update()
True
>>> metar.data.flight_rules
'IFR'
```

You can learn more by reading the [project documentation](https://avwx-engine.readthedocs.io/en/latest/)

**Note**: This library requires Python 3.7 or above

## Develop

Download and install the source code and its development dependencies:

```bash
git clone https://github.com/avwx-rest/avwx-engine
cd avwx-engine
python -m pip install -Ur requirements.txt
python -m pip install -e .
```

Code formatting should be handled by hooks in pre-commit. Before committing any code, be should to install pre-commit into the local git project:

```bash
pre-commit install
```

## Test

The easiest way to test the package is using the `nox` library, which is installed as a dev dependency. It will manage all tests, sessions, supported versions (when available), and cleanup. The tests will pick up the local version of `avwx`.

```bash
nox
```

If you want to run the tests directly, the test suite was built while using the `pytest` library, which is also installed as a dev dependency.

```bash
pytest
```

The end-to-end test files were generated using `util/build_tests.py` and placed into `tests/{report}`. Because Timestamp generation interprets the text based on the current date, Timestamp objects are nullified in the end-to-end tests.

## Docs

AVWX uses `mkdocs` to build its documentation. It's just another install:

```bash
python -m pip install .[docs]
```

To serve the docs during development:

```bash
cd docs
mkdocs serve
```
