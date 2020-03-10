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

    def __init__(self, filename: str):
        self.source = Path(__file__).parent.joinpath("data", f"{filename}.json")

    def _load(self):
        self.data = json.load(self.source.open())

    def __getitem__(self, key: str) -> object:
        if not self.data:
            self._load()
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        if not self.data:
            self._load()
        return key in self.data

    def __len__(self) -> int:
        if not self.data:
            self._load()
        return len(self.data)

    def __iter__(self):
        if not self.data:
            self._load()
        for key in self.data:
            yield key

    def values(self) -> list:
        if not self.data:
            self._load()
        return self.data.values()


AIRCRAFT = _LazyLoad("aircraft")


@dataclass
class Aircraft:
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
class Units:
    altimeter: str
    altitude: str
    temperature: str
    visibility: str
    wind_speed: str


@dataclass
class Number:
    repr: str
    value: float
    spoken: str


@dataclass
class Fraction(Number):
    numerator: int
    denominator: int
    normalized: str


@dataclass
class Timestamp:
    repr: str
    dt: datetime


@dataclass
class Code:
    repr: str
    value: str


@dataclass
class Cloud:
    repr: str
    type: str = None
    base: int = None
    top: int = None
    modifier: str = None
    direction: str = None


@dataclass
class Location:
    repr: str
    station: str
    direction: Number
    distance: Number


@dataclass
class RemarksData:
    dewpoint_decimal: float = None
    temperature_decimal: float = None


@dataclass
class ReportData:
    raw: str
    station: str
    time: Timestamp
    remarks: str


@dataclass
class SharedData:
    altimeter: Number
    clouds: [Cloud]
    flight_rules: str
    other: [str]
    sanitized: str
    visibility: Number
    wind_direction: Number
    wind_gust: Number
    wind_speed: Number
    wx_codes: [Code]


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
    turbulence: [str]
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
class ReportTrans:
    altimeter: str
    clouds: str
    wx_codes: str
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
    turbulence: str
    wind: str
    wind_shear: str


@dataclass
class TafTrans:
    forecast: [TafLineTrans]
    max_temp: str
    min_temp: str
    remarks: dict


@dataclass
class Turbulence:
    severity: str
    floor: Number = None
    ceiling: Number = None


@dataclass
class Icing(Turbulence):
    type: str = None


@dataclass
class PirepData(ReportData):
    aircraft: Aircraft = None
    altitude: Number = None
    clouds: [Cloud] = None
    flight_visibility: Number = None
    icing: Icing = None
    location: Location = None
    sanitized: str = None
    temperature: Number = None
    turbulence: Turbulence = None
    type: str = None
    wx: [str] = None


@dataclass
class AirepData(ReportData):
    pass


@dataclass
class GfsPeriod:
    time: Timestamp
    temperature: Number
    dewpoint: Number
    cloud: Code
    precip_chance_12: Number = None
    precip_amount_12: Code = None
    thunder_storm_12: Number = None
    severe_storm_12: Number = None
    freezing_precip: Number = None
    precip_type: Code = None
    snow: Number = None


@dataclass
class MavPeriod(GfsPeriod):
    wind_direction: Number = None
    wind_speed: Number = None
    precip_chance_6: Number = None
    precip_amount_6: Code = None
    thunder_storm_6: Number = None
    severe_storm_6: Number = None
    ceiling: Code = None
    visibility: Code = None
    vis_obstruction: Code = None


@dataclass
class MexPeriod(GfsPeriod):
    precip_chance_24: Number = None
    precip_amount_24: Code = None
    thunder_storm_24: Number = None
    severe_storm_24: Number = None
    rain_snow_mix: Number = None
    snow_amount_24: Code = None


@dataclass
class MavData(ReportData):
    forecast: [MavPeriod]


@dataclass
class MexData(ReportData):
    forecast: [MexPeriod]


# @dataclass
# class GfsPeriodTrans:
#     temperature: str
#     dewpoint: str
#     cloud: str
#     precip_chance_12: str
#     precip_amount_12: str
#     thunder_storm_12: str
#     severe_storm_12: str
#     freezing_precip: str
#     precip_type: str
#     snow: str


# @dataclass
# class MavPeriodTrans(GfsPeriodTrans):
#     wind_direction: str
#     wind_speed: str
#     precip_chance_6: str
#     precip_amount_6: str
#     thunder_storm_6: str
#     severe_storm_6: str
#     ceiling: str
#     visibility: str
#     vis_obstruction: str


# @dataclass
# class MexPeriodTrans(GfsPeriodTrans):
#     precip_chance_24: str
#     precip_amount_24: str
#     thunder_storm_24: str
#     severe_storm_24: str
#     rain_snow_mix: str
#     snow_amount_24: str
