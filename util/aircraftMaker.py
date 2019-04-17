"""
Builds the aircraft code dict

Copy and paste the table from
https://en.wikipedia.org/wiki/List_of_ICAO_aircraft_type_designators
and place in aircraft.txt
"""

import json

with open('aircraft.txt') as fin:
    lines = fin.readlines()
craft = {}
for line in lines:
    code, _, name = line.strip().split('\t')
    if code not in craft:
        craft[code] = name
json.dump(craft, open('aircraft.json', 'w'))
