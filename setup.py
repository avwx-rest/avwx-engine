"""
Michael duPont - michael@mdupont.com
AVWX-Engine : setup.py

avwx package metadata
"""

from setuptools import setup

setup(
    name='avwx-engine',
    version='1.0.0',
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
        'dataclasses>=0.6.0', # Used for 3.6 backport
        'requests~=2.18.4',
        'xmltodict~=0.11.0'
    ],
    packages=['avwx'],
    package_data={'avwx': ['stations.json']}
)
