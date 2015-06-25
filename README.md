# AVWX-Engine
Aviation Weather parsing engine. METAR &amp; TAF

##Documentation
The library core is found in avwx.py, but most programmers will prefer using the object-oriented wrapper found in avwxoo.py. The bottom of both of these files includes usage examples that will run when the file is executed as main.

##Setup
Run Utils/dbMaker.py to create the station database. The resulting stations.db file doesn't have to be in the same directory as avwx.py, but the path should be changed at the top of avwx.py. If you won't use the getStationInfo functionality avwx, you can skip making the db.

##Testing
The repo contains a utility called AutoTester.py which runs tests on the avwx library. It runs a full check on about 8000 stations found in stationList.csv and takes about three hours to complete a single loop (depending on network and hardware speed). The file will send a status update every third loop.
