"""
Contains dataclasses to hold report data
"""

# stdlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class _LazyLoad:

    source: Path
    data: dict = None

    def __init__(self, fname: str):
        self.source = Path(__file__).parent.joinpath(f"{fname}.json")

    def __getitem__(self, key: str) -> object:
        if not self.data:
            self.data = json.load(self.source.open())
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        if not self.data:
            self.data = json.load(self.source.open())
        return key in self.data

    def values(self) -> list:
        if not self.data:
            self.data = json.load(self.source.open())
        return self.data.values()


AIRCRAFT = _LazyLoad("aircraft")


@dataclass
class Aircraft(object):
    code: str
    type: str

    @classmethod
    def from_icao(cls, code: str) -> "Aircraft":
        """
        Load an Aircraft from an ICAO aircraft code
        """
        try:
            return cls(code=code, type=AIRCRAFT[code])
        except KeyError:
            raise ValueError(code + " is not a known aircraft code")


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
    type: str = None
    base: int = None
    top: int = None
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


# @dataclass
# class AirepData(ReportData):
#     pass
