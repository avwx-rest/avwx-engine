"""
Add run data to station info

Sourced from http://ourairports.com/data/
"""

import csv
import json

stations = json.load(open('stations.json'))

# Add runway data subset to station data
with open('runways.csv') as fin:
    runways = csv.reader(fin)
    header = True
    for runway in runways:
        # Skip header row
        if header:
            header = False
            continue
        data = {
            'length': int(runway[3]) if runway[3] else 0,
            'width': int(runway[4]) if runway[4] else 0,
            'ident1': runway[8],
            'ident2': runway[14],
        }
        station = runway[2]
        if station in stations:
            if 'runways' in stations[station]:
                stations[station]['runways'].append(data)
            else:
                stations[station]['runways'] = [data]

# Sort runways by longest length and add missing nulls
for station in stations:
    if 'runways' in stations[station]:
        stations[station]['runways'].sort(key=lambda x: x['length'], reverse=True)
    else:
        stations[station]['runways'] = None

json.dump(stations, open('stations.1.json', 'w'))
