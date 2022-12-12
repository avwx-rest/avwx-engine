# AVWX

![AVWX logo](docs/assets/images/avwx-logo-color-200.png)

[![PyPI](https://img.shields.io/pypi/v/avwx-engine?style=flat)](https://pypi.python.org/pypi/avwx-engine/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/avwx-engine?style=flat)](https://pypi.python.org/pypi/avwx-engine/)
[![PyPI - License](https://img.shields.io/pypi/l/avwx-engine?style=flat)](https://pypi.python.org/pypi/avwx-engine/)
[![GitHub - Test Suite Status](https://github.com/avwx-rest/avwx-engine/actions/workflows/test.yml/badge.svg)]()

---

**Documentation**: [https://engine.avwx.rest](https://engine.avwx.rest)

**Source Code**: [https://github.com/avwx-rest/avwx-engine](https://github.com/avwx-rest/avwx-engine)

**PyPI**: [https://pypi.org/project/avwx-engine/](https://pypi.org/project/avwx-engine/)

---

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

## Install

The easiest way to get started is to download the library from pypi using pip:

```bash
python -m pip install avwx-engine
```

## Basic Usage

Reports use ICAO, IATA, or GPS idents when specifying the desired station. Exceptions are thrown if a potentially invalid ident is given.

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

You can learn more by reading the [project documentation](https://engine.avwx.rest)

**Note**: This library requires Python 3.8 or above

## Development

Download and install the source code and its development dependencies:

* Clone this repository

```sh
git clone https://github.com/avwx-rest/avwx-engine
cd avwx-engine
```

* Requirements:
  * [Poetry](https://python-poetry.org/)
  * Python 3.8+
* Create a virtual environment and install the dependencies

```sh
poetry install
```

* Activate the virtual environment

```sh
poetry shell
```

### Testing

The test suite was built while using the `pytest` library, which is also installed as a dev dependency.

```bash
pytest
```

The end-to-end test files were generated using `util/build_tests.py` and placed into `tests/{report}/data`. Because Timestamp generation interprets the text based on the current date, Timestamp objects are nullified in the end-to-end tests.

### Documentation

The documentation is automatically generated from the content of the [docs directory](./docs) and from the docstrings of the public signatures of the source code. The documentation is updated and published to [engine.avwx.rest](https://engine.avwx.rest) automatically as part each release.

 You can also preview local changes during development:

```sh
cd docs
mkdocs serve
```

### Releasing

Trigger the [Draft release workflow](https://github.com/avwx-rest/avwx-engine/actions/workflows/draft_release.yml) (press _Run workflow_). This will update the changelog & version and create a GitHub release which is in _Draft_ state.

Find the draft release from the
[GitHub releases](https://github.com/avwx-rest/avwx-engine/releases) and publish it. When a release is published, it'll trigger [release](https://github.com/avwx-rest/avwx-engine/blob/main/.github/workflows/release.yml) workflow which creates PyPI
 release and deploys updated documentation.

### Pre-commit

Pre-commit hooks run all the auto-formatters, linters, and other quality checks to make sure the changeset is in good shape before a commit/push happens.

You can install the hooks with (runs for each commit):

```sh
pre-commit install
```

Or if you want them to run only for each push:

```sh
pre-commit install -t pre-push
```

Or if you want e.g. want to run all checks manually for all files:

```sh
pre-commit run --all-files
```
