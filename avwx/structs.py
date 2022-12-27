"""
Contains dataclasses to hold report data
"""

# pylint: disable=missing-class-docstring,missing-function-docstring,too-many-instance-attributes

# stdlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Type, TypeVar, Union

# module
from avwx.load_utils import LazyLoad


try:
    from shapely.geometry import Point, Polygon  # type: ignore
except ModuleNotFoundError:
    Point, Polygon = None, None

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


CodeType = TypeVar("CodeType", bound="Code")  # pylint: disable=invalid-name


@dataclass
class Code:
    repr: str
    value: str

    @classmethod
    def from_dict(
        cls: Type[CodeType],
        key: Optional[str],
        codes: Dict[str, str],
        default: Optional[str] = None,
        error: bool = True,
    ) -> Optional[CodeType]:
        """Load a code from a known key and value dict"""
        if not key:
            return None
        try:
            value = codes.get(key)
        except KeyError as exc:
            if error:
                raise KeyError(f"No code found for {key}") from exc
            value = default
        return cls(key, value or "Unknown")


@dataclass
class Coord:
    lat: float
    lon: float
    repr: Optional[str] = None

    @property
    def pair(self) -> Tuple[float, float]:
        return self.lat, self.lon

    @property
    def point(self) -> Point:
        if Point is None:
            raise ModuleNotFoundError("Install avwx-engine[shape] to use this feature")
        return Point(self.lat, self.lon)

    @staticmethod
    def to_dms(value: float) -> Tuple[int, int, int]:
        """Convert a coordinate decimal value to degree, minute, second"""
        minute, second = divmod(abs(value) * 3600, 60)
        degree, minute = divmod(minute, 60)
        if value < 0:
            degree *= -1
        return int(degree), int(minute), int(second)


@dataclass
class Cloud:
    repr: str
    type: Optional[str] = None
    base: Optional[int] = None
    top: Optional[int] = None
    modifier: Optional[str] = None


@dataclass
class RunwayVisibility:
    repr: str
    runway: str
    visibility: Optional[Number]
    variable_visibility: List[Number]
    trend: Optional[Code]


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
    runway_visibility: List[RunwayVisibility]
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
class Bulletin:
    repr: str
    type: Code
    country: str
    number: int


@dataclass
class Movement:
    repr: str
    direction: Optional[Number]
    speed: Optional[Number]


@dataclass
class AirSigObservation:
    type: Optional[Code]
    start_time: Optional[Timestamp]
    end_time: Optional[Timestamp]
    position: Optional[Coord]
    floor: Optional[Number]
    ceiling: Optional[Number]
    coords: List[Coord]
    bounds: List[str]
    movement: Optional[Movement]
    intensity: Optional[Code]
    other: List[str]

    @property
    def poly(self) -> Optional[Polygon]:
        if Polygon is None:
            raise ModuleNotFoundError("Install avwx-engine[shape] to use this feature")
        if len(self.coords) > 2:
            return Polygon([c.pair for c in self.coords])
        return None


@dataclass
class AirSigmetData(ReportData):
    bulletin: Bulletin
    issuer: str
    correction: Optional[str]
    area: str
    type: str
    start_time: Optional[Timestamp]
    end_time: Optional[Timestamp]
    body: str
    region: str
    observation: Optional[AirSigObservation]
    forecast: Optional[AirSigObservation]


@dataclass
class Qualifiers:
    repr: str
    fir: str
    subject: Optional[Code]
    condition: Optional[Code]
    traffic: Optional[Code]
    purpose: List[Code]
    scope: List[Code]
    lower: Optional[Number]
    upper: Optional[Number]
    coord: Optional[Coord]
    radius: Optional[Number]


@dataclass
class NotamData(ReportData):
    number: Optional[str]
    replaces: Optional[str]
    type: Optional[Code]
    qualifiers: Optional[Qualifiers]
    start_time: Optional[Timestamp]
    end_time: Optional[Timestamp]
    schedule: Optional[str]
    body: str
    lower: Optional[Number]
    upper: Optional[Number]


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


@dataclass
class Sanitization:
    removed: List[str] = field(default_factory=list)
    replaced: Dict[str, str] = field(default_factory=dict)
    duplicates_found: bool = False
    extra_spaces_found: bool = False
    extra_spaces_needed: bool = False

    @property
    def errors_found(self) -> bool:
        return bool(
            self.removed
            or self.replaced
            or self.duplicates_found
            or self.extra_spaces_found
            or self.extra_spaces_needed
        )

    def log(self, item: str, replacement: Optional[str] = None) -> None:
        """Log a changed item. Calling without a replacement assumes removal"""
        item = item.strip()
        if not item:
            return
        if replacement is None:
            self.removed.insert(0, item)
            return
        replacement = replacement.strip()
        if not replacement:
            self.removed.insert(0, item)
        elif item != replacement:
            self.replaced[item] = replacement

    def log_list(self, before: List[str], after: List[str]) -> None:
        """Log list differences. Assumes that list length and order haven't changed"""
        for item, replacement in zip(before, after):
            if item != replacement:
                self.log(item, replacement)
