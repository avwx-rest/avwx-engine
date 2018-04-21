"""
Michael duPont - michael@mdupont.com
AVWX-Engine : setup.py

avwx package metadata
"""

from setuptools import setup

setup(
    name='avwx-engine',
    version='0.11.5',
    description='Aviation weather report parsing library',
    url='https://github.com/flyinactor91/AVWX-Engine',
    author='Michael duPont',
    author_email='michael@mdupont.com',
    license='MIT',
    install_requires=[
        'requests~=2.18.2',
        'xmltodict~=0.11.0'
    ],
    packages=[
        'avwx'
    ],
    package_data={
        'avwx': [
            'stations.json'
        ]
    }
)
