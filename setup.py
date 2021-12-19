"""
avwx Package Setup
"""

from setuptools import find_namespace_packages, setup

VERSION = "1.6.19"

dependencies = [
    "geopy~=2.2",
    "httpx~=0.21",
    "python-dateutil~=2.8",
    "rapidfuzz~=1.9",
    "xmltodict~=0.12",
]

test_dependencies = ["pytest-asyncio~=0.16", "time-machine~=2.5"]

extras = {
    "scipy": ["scipy~=1.7"],
    "docs": ["mkdocs~=1.2", "mkdocs-material~=8.1", "mkdocs-minify-plugin~=0.5"],
    "tests": test_dependencies,
}

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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">= 3.7",
    install_requires=dependencies,
    packages=find_namespace_packages(include=["avwx*"]),
    package_data={"avwx.data": ["aircraft.json", "stations.json"]},
    tests_require=test_dependencies,
    extras_require=extras,
)
