"""
Michael duPont - michael@mdupont.com
AVWX-Engine : setup.py

avwx package metadata
"""

from setuptools import setup

setup(
    name='avwx-engine',
    version='1.0.1',
    description='Aviation weather report parsing library',
    url='https://github.com/flyinactor91/AVWX-Engine',
    author='Michael duPont',
    author_email='michael@mdupont.com',
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires='>= 3.6',
    install_requires=[
        'dataclasses>=0.6;python_version<"3.7"',
        'python-dateutil~=2.7',
        'requests~=2.19',
        'xmltodict~=0.11',
    ],
    packages=['avwx'],
    package_data={'avwx': ['stations.json']}
)
