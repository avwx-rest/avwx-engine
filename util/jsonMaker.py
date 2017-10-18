#!/usr/bin/python3

"""
Michael duPont - michael@mdupont.com
AVWX-Engine : Utils/jsonMaker.py
Creates the station json from csv
"""

import csv
import json

station_hash = {}
with open('stationList.csv') as fin:
    stations = csv.reader(fin, delimiter=',', quotechar='|')
    for station in stations:
        icao = station.pop(0)
        station_hash[icao] = station
json.dump(station_hash, open('stations.json', 'w'))
