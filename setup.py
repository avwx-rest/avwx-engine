"""
avwx Package Setup
"""

from setuptools import find_namespace_packages, setup

VERSION = "1.8.0"

dependencies = [
    "geopy~=2.2",
    "httpx~=0.23",
    "python-dateutil~=2.8",
    "xmltodict~=0.13",
]

test_dependencies = ["pytest-asyncio~=0.18", "time-machine~=2.7"]

extras = {
    "fuzz": ["rapidfuzz~=2.0"],
    "scipy": ["scipy~=1.8"],
    "shape": ["shapely~=1.8"],
    "docs": ["mkdocs~=1.3", "mkdocs-material~=8.2", "mkdocs-minify-plugin~=0.5"],
    "tests": test_dependencies,
}
extras["all"] = extras["fuzz"] + extras["scipy"] + extras["shape"]

setup(
    name="avwx-engine",
    version=VERSION,
    description="Aviation weather report parsing library",
    url="https://github.com/avwx-rest/avwx-engine",
    author="Michael duPont",
    author_email="michael@dupont.dev",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">= 3.8",
    install_requires=dependencies,
    packages=find_namespace_packages(include=["avwx*"]),
    package_data={
        "avwx.data.files": [
            "aircraft.json",
            "good_stations.txt",
            "navaids.json",
            "stations.json",
        ]
    },
    tests_require=test_dependencies,
    extras_require=extras,
)
