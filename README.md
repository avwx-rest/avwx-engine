# AVWX

![AVWX logo](https://raw.githubusercontent.com/avwx-rest/avwx-engine/main/docs/assets/images/avwx-logo-color-200.png)

[![PyPI](https://img.shields.io/pypi/v/avwx-engine?style=flat)](https://pypi.python.org/pypi/avwx-engine/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/avwx-engine?style=flat)](https://pypi.python.org/pypi/avwx-engine/)
[![GitHub - Test Suite Status](https://github.com/avwx-rest/avwx-engine/actions/workflows/test.yml/badge.svg)](https://github.com/avwx-rest/avwx-engine/actions/workflows/test.yml)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

**Note**: This library requires Python 3.10 or above

## Development

Download and install the source code and its development dependencies:

* Clone this repository

```sh
git clone https://github.com/avwx-rest/avwx-engine
cd avwx-engine
```

* Requirements:
  * [Hatch](https://hatch.pypa.io/latest/)
  * Python 3.10+

* Create a virtual environment and install the dependencies

```sh
hatch env create
```

* Activate the virtual environment

```sh
hatch shell
```

### Formatting and Code Checks

`hatch` handles all of the formatting and linting for us. The library and test suite are fully typed and formatted. Make sure to run these checks before submitting PRs because the workflows will fail if errors are found.

Typing with `mypy`:

```bash
hatch run types:check
```

Code formatting and linting:

```bash
hatch fmt
```

### Testing

Testing is managed by `hatch` which uses `pytest` and coverage under the hood.

```bash
hatch test
```

The end-to-end test files were generated using `util/build_tests.py` and placed into `tests/{report}/data`. Because Timestamp generation interprets the text based on the current date, Timestamp objects are nullified in the end-to-end tests.

### Documentation

The documentation is automatically generated from the content of the [docs directory](./docs) and from the docstrings of the public signatures of the source code. The documentation is updated and published to [engine.avwx.rest](https://engine.avwx.rest) automatically as part each release.

You can also preview local changes during development:

```sh
hatch run docs:serve
```

### Releasing

Trigger the [Draft release workflow](https://github.com/avwx-rest/avwx-engine/actions/workflows/draft_release.yml) (press _Run workflow_). This will update the changelog & version and create a GitHub release which is in _Draft_ state.

Find the draft release from the [GitHub releases](https://github.com/avwx-rest/avwx-engine/releases) and publish it. When a release is published, it'll trigger [release](https://github.com/avwx-rest/avwx-engine/blob/main/.github/workflows/release.yml) workflow which creates PyPI release and deploys updated documentation.
