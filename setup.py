"""
avwx package metadata
"""

from setuptools import setup
import avwx

setup(
    name="avwx-engine",
    version=avwx.__version__,
    description=avwx.__doc__,
    url="https://github.com/avwx-rest/AVWX-Engine",
    author=avwx.__author__,
    author_email=avwx.__email__,
    license=avwx.__license__,
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">= 3.6",
    install_requires=[
        "aiohttp~=3.5",
        'dataclasses>=0.6;python_version<"3.7"',
        "python-dateutil~=2.8",
        "xmltodict~=0.12",
    ],
    packages=["avwx"],
    package_data={"avwx": ["aircraft.json", "stations.json"]},
    tests_require=["pytest-asyncio~=0.10"],
    extras_require={"scipy": ["scipy~=1.3"]},
)
