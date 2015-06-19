# AVWX-Engine
Aviation Weather parsing engine. METAR &amp; TAF

##Documentation
Function usage and examples can be found inside avwx.py

##Setup
Run dbMaker.py to create the station database. The resulting stations.db file doesn't have to be in the same directory as avwx.py, but the path should be changed at the top of avwx.py

##Testing
The repo contains a utility called AutoTester.py which runs tests on the avwx library. It runs a full check on about 8000 stations found in stationList.csv and takes about three hours to complete a single loop (depending on network and hardware speed). The file will send a status update every third loop.
