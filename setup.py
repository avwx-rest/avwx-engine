"""
Michael duPont - michael@mdupont.com
AVWX-Engine : setup.py

avwx package metadata
"""

from setuptools import setup

def list_requirements() -> [str]:
    """
    Read requirements from requirements.txt
    """
    with open('requirements.txt') as fin:
        return fin.readlines()

setup(
    name='avwx-engine',
    version='0.11.4',
    description='Aviation weather report parsing library',
    url='https://github.com/flyinactor91/AVWX-Engine',
    author='Michael duPont',
    author_email='michael@mdupont.com',
    license='MIT',
    install_requires=list_requirements(),
    packages=[
        'avwx'
    ],
    package_data={
        'avwx': [
            'stations.json'
        ]
    }
)
