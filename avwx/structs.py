"""
Contains dataclasses to hold report data
"""

# pylint: disable=missing-class-docstring,missing-function-docstring,too-many-instance-attributes

# stdlib
import json
from collections.abc import KeysView, ValuesView
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Union


class _LazyLoad:

    source: Path
    data: Optional[dict] = None

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

    def __iter__(self) -> Iterable[str]:
        if not self.data:
            self._load()
        for key in self.data:
            yield key

    def items(self) -> KeysView:
        if not self.data:
            self._load()
        return self.data.items()

    def values(self) -> ValuesView:
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
    value: Union[int, float]
    spoken: str


@dataclass
class Fraction(Number):
    numerator: int
    denominator: int
    normalized: str


@dataclass
class Timestamp:
    # pylint: disable=invalid-name
    repr: str
    dt: datetime


@dataclass
class Code:
    repr: str
    value: str


@dataclass
class Cloud:
    repr: str
    type: Optional[str] = None
    base: Optional[int] = None
    top: Optional[int] = None
    modifier: Optional[str] = None
    direction: Optional[str] = None


@dataclass
class Location:
    repr: str
    station: str
    direction: Number
    distance: Number


@dataclass
class RemarksData:
    dewpoint_decimal: Optional[float] = None
    temperature_decimal: Optional[float] = None


@dataclass
class ReportData:
    raw: str
    station: str
    time: Timestamp
    remarks: str


@dataclass
class SharedData:
    altimeter: Number
    clouds: List[Cloud]
    flight_rules: str
    other: List[str]
    sanitized: str
    visibility: Number
    wind_direction: Number
    wind_gust: Number
    wind_speed: Number
    wx_codes: List[Code]


@dataclass
class MetarData(ReportData, SharedData):
    dewpoint: Number
    remarks_info: RemarksData
    runway_visibility: List[str]
    temperature: Number
    wind_variable_direction: List[Number]


@dataclass
class TafLineData(SharedData):
    end_time: Timestamp
    icing: List[str]
    probability: Number
    raw: str
    start_time: Timestamp
    transition_start: Timestamp
    turbulence: List[str]
    type: str
    wind_shear: str


@dataclass
class TafData(ReportData):
    forecast: List[TafLineData]
    start_time: Timestamp
    end_time: Timestamp
    max_temp: Optional[float] = None
    min_temp: Optional[float] = None
    alts: Optional[List[str]] = None
    temps: Optional[List[str]] = None


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
    forecast: List[TafLineTrans]
    max_temp: str
    min_temp: str
    remarks: dict


@dataclass
class Turbulence:
    severity: str
    floor: Optional[Number] = None
    ceiling: Optional[Number] = None


@dataclass
class Icing(Turbulence):
    type: Optional[str] = None


@dataclass
class PirepData(ReportData):
    # pylint: disable=invalid-name
    aircraft: Optional[Aircraft] = None
    altitude: Optional[Number] = None
    clouds: Optional[List[Cloud]] = None
    flight_visibility: Optional[Number] = None
    icing: Optional[Icing] = None
    location: Optional[Location] = None
    sanitized: Optional[str] = None
    temperature: Optional[Number] = None
    turbulence: Optional[Turbulence] = None
    type: Optional[str] = None
    wx: Optional[List[str]] = None


@dataclass
class AirepData(ReportData):
    pass


@dataclass
class GfsPeriod:
    time: Timestamp
    temperature: Number
    dewpoint: Number
    cloud: Code
    precip_chance_12: Optional[Number] = None
    precip_amount_12: Optional[Code] = None
    thunderstorm_12: Optional[Number] = None
    severe_storm_12: Optional[Number] = None
    freezing_precip: Optional[Number] = None
    precip_type: Optional[Code] = None
    snow: Optional[Number] = None


@dataclass
class MavPeriod(GfsPeriod):
    wind_direction: Optional[Number] = None
    wind_speed: Optional[Number] = None
    precip_chance_6: Optional[Number] = None
    precip_amount_6: Optional[Code] = None
    thunderstorm_6: Optional[Number] = None
    severe_storm_6: Optional[Number] = None
    ceiling: Optional[Code] = None
    visibility: Optional[Code] = None
    vis_obstruction: Optional[Code] = None


@dataclass
class MexPeriod(GfsPeriod):
    precip_chance_24: Optional[Number] = None
    precip_amount_24: Optional[Code] = None
    thunderstorm_24: Optional[Number] = None
    severe_storm_24: Optional[Number] = None
    rain_snow_mix: Optional[Number] = None
    snow_amount_24: Optional[Code] = None


@dataclass
class MavData(ReportData):
    forecast: List[MavPeriod]


@dataclass
class MexData(ReportData):
    forecast: List[MexPeriod]


@dataclass
class NbmUnits(Units):
    accumulation: str
    duration: str
    solar_radiation: str
    wave_height: str


@dataclass
class NbmPeriod:
    time: Timestamp
    temperature: Optional[Number] = None
    dewpoint: Optional[Number] = None
    sky_cover: Optional[Number] = None
    wind_direction: Optional[Number] = None
    wind_speed: Optional[Number] = None
    wind_gust: Optional[Number] = None
    snow_level: Optional[Number] = None
    precip_duration: Optional[Number] = None
    freezing_precip: Optional[Number] = None
    snow: Optional[Number] = None
    sleet: Optional[Number] = None
    rain: Optional[Number] = None
    solar_radiation: Optional[Number] = None
    wave_height: Optional[Number] = None


@dataclass
class NbhsShared(NbmPeriod):
    ceiling: Optional[Number] = None
    visibility: Optional[Number] = None
    cloud_base: Optional[Number] = None
    mixing_height: Optional[Number] = None
    transport_wind_direction: Optional[Number] = None
    transport_wind_speed: Optional[Number] = None
    haines: List[Number] = None


@dataclass
class NbhPeriod(NbhsShared):
    precip_chance_1: Optional[Number] = None
    precip_chance_6: Optional[Number] = None
    precip_amount_1: Optional[Number] = None
    thunderstorm_1: Optional[Number] = None
    snow_amount_1: Optional[Number] = None
    icing_amount_1: Optional[Number] = None


@dataclass
class NbsPeriod(NbhsShared):
    precip_chance_6: Optional[Number] = None
    precip_chance_12: Optional[Number] = None
    precip_amount_6: Optional[Number] = None
    precip_amount_12: Optional[Number] = None
    precip_duration: Optional[Number] = None
    thunderstorm_3: Optional[Number] = None
    thunderstorm_12: Optional[Number] = None
    snow_amount_6: Optional[Number] = None
    icing_amount_6: Optional[Number] = None


@dataclass
class NbePeriod(NbmPeriod):
    precip_chance_12: Optional[Number] = None
    precip_amount_12: Optional[Number] = None
    precip_amount_24: Optional[Number] = None
    thunderstorm_12: Optional[Number] = None
    snow_amount_12: Optional[Number] = None
    snow_amount_24: Optional[Number] = None
    icing_amount_12: Optional[Number] = None


@dataclass
class NbhData(ReportData):
    forecast: List[NbhPeriod]


@dataclass
class NbsData(ReportData):
    forecast: List[NbsPeriod]


@dataclass
class NbeData(ReportData):
    forecast: List[NbePeriod]


# @dataclass
# class GfsPeriodTrans:
#     temperature: str
#     dewpoint: str
#     cloud: str
#     precip_chance_12: str
#     precip_amount_12: str
#     thunderstorm_12: str
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
#     thunderstorm_6: str
#     severe_storm_6: str
#     ceiling: str
#     visibility: str
#     vis_obstruction: str


# @dataclass
# class MexPeriodTrans(GfsPeriodTrans):
#     precip_chance_24: str
#     precip_amount_24: str
#     thunderstorm_24: str
#     severe_storm_24: str
#     rain_snow_mix: str
#     snow_amount_24: str
