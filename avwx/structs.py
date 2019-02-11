"""
Contains dataclasses to hold report data
"""

# stdlib
import json
from copy import copy
from dataclasses import asdict, dataclass
from datetime import datetime
from os import path
# module
from avwx.exceptions import BadStation


_station_path = path.dirname(path.realpath(__file__)) + '/stations.json'
STATIONS = json.load(open(_station_path))


@dataclass
class Runway(object):
    length: int
    width: int
    ident1: str
    ident2: str


@dataclass
class Station(object):
    city: str
    country: str
    elevation: float
    iata: str
    icao: str
    latitude: float
    longitude: float
    name: str
    priority: int
    state: str
    runways: [Runway]

    @classmethod
    def from_icao(cls, ident: str) -> 'Station':
        """
        Load a Station from an ICAO station ident
        """
        if not ident in STATIONS:
            raise BadStation('Could not find station in the info dict. Check avwx.structs.STATIONS')
        info = copy(STATIONS[ident])
        if info['runways']:
            info['runways'] = [Runway(**r) for r in info['runways']]
        return cls(**info)


@dataclass
class Units(object):
    altimeter: str
    altitude: str
    temperature: str
    visibility: str
    wind_speed: str


@dataclass
class Number(object):
    repr: str
    value: float
    spoken: str


@dataclass
class Fraction(Number):
    numerator: int
    denominator: int
    normalized: str


@dataclass
class Timestamp(object):
    repr: str
    dt: datetime


@dataclass
class Cloud(object):
    repr: str
    type: str
    altitude: int
    modifier: str = None
    direction: str = None


@dataclass
class Location(object):
    repr: str
    station: str
    direction: Number
    distance: Number


@dataclass
class RemarksData(object):
    dewpoint_decimal: float = None
    temperature_decimal: float = None


@dataclass
class ReportData(object):
    raw: str
    station: str
    time: Timestamp
    remarks: str


@dataclass
class SharedData(object):
    altimeter: Number
    clouds: [Cloud]
    flight_rules: str
    other: [str]
    sanitized: str
    visibility: Number
    wind_direction: Number
    wind_gust: Number
    wind_speed: Number


@dataclass
class MetarData(ReportData, SharedData):
    dewpoint: Number
    remarks_info: RemarksData
    runway_visibility: [str]
    temperature: Number
    wind_variable_direction: [Number]


@dataclass
class TafLineData(SharedData):
    end_time: Timestamp
    icing: [str]
    probability: Number
    raw: str
    start_time: Timestamp
    turbulance: [str]
    type: str
    wind_shear: str


@dataclass
class TafData(ReportData):
    forecast: [TafLineData]
    start_time: Timestamp
    end_time: Timestamp
    max_temp: float = None
    min_temp: float = None
    alts: [str] = None
    temps: [str] = None


@dataclass
class ReportTrans(object):
    altimeter: str
    clouds: str
    other: str
    visibility: str


@dataclass
class MetarTrans(ReportTrans):
    dewpoint: str
    remarks: dict
    temperature: str
    wind: str


@dataclass
class TafLineTrans(ReportTrans):
    icing: str
    turbulance: str
    wind: str
    wind_shear: str


@dataclass
class TafTrans(object):
    forecast: [TafLineTrans]
    max_temp: str
    min_temp: str
    remarks: dict


@dataclass
class Turbulance(object):
    severity: str
    floor: Number = None
    ceiling: Number = None


@dataclass
class Icing(Turbulance):
    type: str = None


@dataclass
class PirepData(ReportData):
    aircraft: str = None
    altitude: Number = None
    clouds: [Cloud] = None
    flight_visibility: Number = None
    icing: Icing = None
    location: Location = None
    sanitized: str = None
    temperature: Number = None
    turbulance: Turbulance = None
    type: str = None
    wx: [str] = None


@dataclass
class AirepData(ReportData):
    pass
