#!/usr/bin/python3

"""
Michael duPont - michael@mdupont.com
AVWX-Engine : Utils/dbMaker.py
Creates the station db from csv
"""

import csv
import sqlite3

fin = open('stationList.csv', 'r')
stations = csv.reader(fin, delimiter=',', quotechar='|')
conn = sqlite3.connect('../avwx/stations.sqlite')
conn.text_factory = str
curs = conn.cursor()
curs.execute('CREATE TABLE Stations (icao,country,state,city,name,iata,elevation,latitude,longitude,priority)')
curs.executemany('INSERT INTO Stations VALUES (?,?,?,?,?,?,?,?,?,?)', stations)
conn.commit()
