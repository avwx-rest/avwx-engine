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
    altimeter: float
    clouds: list
    flight_rules: str
    other: list
    sanitized: str
    visibility: int
    wind_direction: int
    wind_gust: int
    wind_speed: int


@dataclass
class MetarData(ReportData, SharedData):
    dewpoint: int
    remarks_info: RemarksData
    runway_visibility: list
    temperature: int
    wind_variable_direction: list


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
