"""
Contains dataclasses to hold report data
"""

# stdlib
from dataclasses import asdict, dataclass

@dataclass
class StationInfo(object):
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


@dataclass
class Units(object):
    altimeter: str
    altitude: str
    temperature: str
    visibility: str
    wind_speed: str


@dataclass
class Number(object):
    value: float
    repr: str


@dataclass
class Fraction(Number):
    numerator: int
    denominator: int
    normalized: str


@dataclass
class Cloud(object):
    repr: str
    type: str
    altitude: int
    modifier: str = None


@dataclass
class RemarksData(object):
    dewpoint_decimal: float = None
    temperature_decimal: float = None


@dataclass
class ReportData(object):
    raw: str
    remarks: str
    station: str
    time: str


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
    end_time: str
    icing: [str]
    probability: str
    raw: str
    start_time: str
    turbulance: [str]
    type: str
    wind_shear: str


@dataclass
class TafData(ReportData):
    forecast: [TafLineData]
    start_time: str
    end_time: str
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
