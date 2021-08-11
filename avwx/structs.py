"""
Contains dataclasses to hold report data
"""

# pylint: disable=missing-class-docstring,missing-function-docstring,too-many-instance-attributes

# stdlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Union

# module
from avwx.load_utils import LazyLoad


AIRCRAFT = LazyLoad("aircraft")


@dataclass
class Aircraft:
    code: str
    type: str

    @classmethod
    def from_icao(cls, code: str) -> "Aircraft":
        """Load an Aircraft from an ICAO aircraft code"""
        try:
            return cls(code=code, type=AIRCRAFT[code])
        except KeyError as key_error:
            raise ValueError(code + " is not a known aircraft code") from key_error


@dataclass
class Units:
    accumulation: str
    altimeter: str
    altitude: str
    temperature: str
    visibility: str
    wind_speed: str


@dataclass
class Number:
    repr: str
    value: Union[int, float, None]
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
    dt: Optional[datetime]


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
    station: Optional[str]
    direction: Optional[Number]
    distance: Optional[Number]


@dataclass
class PressureTendency:
    repr: str
    tendency: str
    change: float


@dataclass
class FiveDigitCodes:
    maximum_temperature_6: Optional[Number] = None  # 1
    minimum_temperature_6: Optional[Number] = None  # 2
    pressure_tendency: Optional[PressureTendency] = None  # 5
    precip_36_hours: Optional[Number] = None  # 6
    precip_24_hours: Optional[Number] = None  # 7
    sunshine_minutes: Optional[Number] = None  # 9


@dataclass
class RemarksData(FiveDigitCodes):
    codes: List[Code] = field(default_factory=[])  # type: ignore
    dewpoint_decimal: Optional[Number] = None
    maximum_temperature_24: Optional[Number] = None
    minimum_temperature_24: Optional[Number] = None
    precip_hourly: Optional[Number] = None
    sea_level_pressure: Optional[Number] = None
    snow_depth: Optional[Number] = None
    temperature_decimal: Optional[Number] = None


@dataclass
class ReportData:
    raw: str
    sanitized: str
    station: Optional[str]
    time: Optional[Timestamp]
    remarks: Optional[str]


@dataclass
class SharedData:
    altimeter: Optional[Number]
    clouds: List[Cloud]
    flight_rules: str
    other: List[str]
    visibility: Optional[Number]
    wind_direction: Optional[Number]
    wind_gust: Optional[Number]
    wind_speed: Optional[Number]
    wx_codes: List[Code]


@dataclass
class MetarData(ReportData, SharedData):
    dewpoint: Optional[Number]
    relative_humidity: Optional[float]
    remarks_info: Optional[RemarksData]
    runway_visibility: List[str]
    temperature: Optional[Number]
    wind_variable_direction: List[Number]
    density_altitude: Optional[int] = None
    pressure_altitude: Optional[int] = None


@dataclass
class TafLineData(SharedData):
    end_time: Optional[Timestamp]
    icing: List[str]
    probability: Optional[Number]
    raw: str
    sanitized: str
    start_time: Optional[Timestamp]
    transition_start: Optional[Timestamp]
    turbulence: List[str]
    type: str
    wind_shear: Optional[str]


@dataclass
class TafData(ReportData):
    forecast: List[TafLineData]
    start_time: Optional[Timestamp]
    end_time: Optional[Timestamp]
    max_temp: Optional[str] = None
    min_temp: Optional[str] = None
    alts: Optional[List[str]] = None
    temps: Optional[List[str]] = None
    remarks_info: Optional[RemarksData] = None


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
    aircraft: Union[Aircraft, str, None] = None
    altitude: Union[Number, str, None] = None
    clouds: Optional[List[Cloud]] = None
    flight_visibility: Optional[Number] = None
    icing: Optional[Icing] = None
    location: Optional[Location] = None
    other: Optional[List[str]] = None
    temperature: Optional[Number] = None
    turbulence: Optional[Turbulence] = None
    type: Optional[str] = None
    wx_codes: Optional[List[Code]] = None


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
    haines: Optional[List[Number]] = None


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
    thunderstorm_6: Optional[Number] = None
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
