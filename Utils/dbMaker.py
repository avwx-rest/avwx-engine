#!/usr/bin/python3

##--Michael duPont
##--AVWX-Engine : dbMaker.py
##--Creates the station db from csv
##--2015-06-15

import csv , sqlite3

fin = open('stationList.csv' , 'r')
stations = csv.reader(fin , delimiter=',' , quotechar='|')
conn = sqlite3.connect('stations.db')
conn.text_factory = str
curs = conn.cursor()
curs.execute('CREATE TABLE Stations (icao,country,state,city,name,iata,elevation,latitude,longitude,priority)')
curs.executemany('INSERT INTO Stations VALUES (?,?,?,?,?,?,?,?,?,?)' , stations)
conn.commit()
