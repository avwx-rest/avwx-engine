"""
avwx Package Setup
"""

from setuptools import setup

setup(
    name="avwx-engine",
    version="1.3.10",
    description="Aviation weather report parsing library",
    url="https://github.com/avwx-rest/avwx-engine",
    author="Michael duPont",
    author_email="michael@mdupont.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">= 3.6",
    install_requires=[
        'dataclasses>=0.7;python_version<"3.7"',
        "geopy~=1.20",
        "httpx~=0.7.8",
        "python-dateutil~=2.8",
        "xmltodict~=0.12",
    ],
    packages=["avwx"],
    package_data={"avwx": ["aircraft.json", "stations.json"]},
    tests_require=["pytest-asyncio~=0.10"],
    extras_require={
        "scipy": ["scipy~=1.3"],
        "dev": ["nox==2019.11.9", "pre-commit~=1.20", "pytest~=5.3"],
        "docs": ["mkdocs~=1.0"],
    },
)
