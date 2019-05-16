# AVWX-Engine

### Master

[![PyPI version](https://badge.fury.io/py/avwx-engine.svg)](https://badge.fury.io/py/avwx-engine)
[![Code Health](https://landscape.io/github/avwx-rest/AVWX-Engine/master/landscape.svg?style=flat)](https://landscape.io/github/avwx-rest/AVWX-Engine/master)
[![Requirements Status](https://requires.io/github/avwx-rest/AVWX-Engine/requirements.svg?branch=master)](https://requires.io/github/avwx-rest/AVWX-Engine/requirements/?branch=master)
[![Documentation Status](https://readthedocs.org/projects/avwx-engine/badge/?version=latest)](http://avwx-engine.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/pypi/l/avwx-engine.svg)](https://pypi.org/project/avwx-engine/)

Aviation Weather parsing engine. METAR &amp; TAF

# Install

The easiest way to get started is to download the library from pypi using pip

```bash
pip install avwx-engine
```

# Basic Usage

Reports use ICAO idents when specifying the desired station. Exceptions are thrown if a potentially invalid ident is given.

```python
>>> import avwx
>>> 
>>> metar = avwx.Metar('KJFK')
>>> metar.station_info.name
'John F Kennedy International Airport'
>>> metar.update()
True
>>> metar.data.flight_rules
'IFR'
```

You can learn more by reading the [project documentation](https://avwx-engine.readthedocs.io/en/latest/)

**Note**: This library requires Python 3.6 or above

# Develop

Download and install the source code and its dependencies:

```bash
git clone github.com/flyinactor91/AVWX-Engine
cd AVWX-Engine
pip install -U .
```

Code checked into this repository is expected to be run through the `black` code formatter first.

```bash
# Install black
pip install black

# Format py package files
find avwx -iname "*.py" | xargs black
```

# Test

The easiest way to test the package is using `nox`. It will manage all tests, sessions, supported versions (when available), and cleanup. The tests will pick up the local version of `avwx`.

```bash
# Install
pip install nox

# Run all tests
nox
```

If you want to run the tests directly, the test suite was built while using the `pytest` library.

```bash
# Install
pip install pytest

# Run all unit tests
pytest
```

The end-to-end test files were generated using `utils/testMaker.py` and placed into `tests/metar` and `tests/taf` respectively. Because Timestamp generation interprets the text based on the current date, Timestamp objects are nullified in the end-to-end tests.

# Docs

AVWX uses Sphinx to build its documentation. It's just another install:

```bash
pip install sphinx
```

To build the docs:

```bash
cd docs
make html
```