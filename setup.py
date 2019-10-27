"""
avwx Package Setup
"""

from pathlib import Path
from setuptools import setup

meta = {}
with Path("avwx", "_meta.py").open() as fin:
    exec(fin.read(), meta)

setup(
    name="avwx-engine",
    version=meta["__version__"],
    description=meta["__doc__"],
    url="https://github.com/avwx-rest/AVWX-Engine",
    author=meta["__author__"],
    author_email=meta["__email__"],
    license=meta["__license__"],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">= 3.6",
    install_requires=[
        'dataclasses>=0.7;python_version<"3.7"',
        "geopy~=1.20",
        "httpx==0.7.5",
        "python-dateutil~=2.8",
        "xmltodict~=0.12",
    ],
    packages=["avwx"],
    package_data={"avwx": ["aircraft.json", "stations.json"]},
    tests_require=["pytest-asyncio~=0.10"],
    extras_require={
        "scipy": ["scipy~=1.3"],
        "dev": ["nox==2019.8.20", "pre-commit~=1.18", "pytest~=5.1"],
        "docs": ["mkdocs~=1.0"],
    },
)
