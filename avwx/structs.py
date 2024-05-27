"""Contains dataclasses to hold report data."""

# stdlib
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

# module
from avwx.exceptions import MissingExtraModule
from avwx.load_utils import LazyLoad
from avwx.static.core import IN_UNITS, NA_UNITS

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self
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
    def from_icao(cls, code: str) -> Self:
        """Load an Aircraft from an ICAO aircraft code."""
        try:
            return cls(code=code, type=AIRCRAFT[code])
        except KeyError as key_error:
            msg = f"{code} is not a known aircraft code"
            raise ValueError(msg) from key_error


@dataclass
class Units:
    accumulation: str
    altimeter: str
    altitude: str
    temperature: str
    visibility: str
    wind_speed: str

    @classmethod
    def international(cls) -> Self:
        """Create default internation units."""
        return cls(**IN_UNITS)

    @classmethod
    def north_american(cls) -> Self:
        """Create default North American units."""
        return cls(**NA_UNITS)


@dataclass
class Number:
    repr: str
    value: int | float | None
    spoken: str


@dataclass
class Fraction(Number):
    numerator: int
    denominator: int
    normalized: str


@dataclass
class Timestamp:
    repr: str
    dt: datetime | None


@dataclass
class Code:
    repr: str
    value: str

    @classmethod
    def from_dict(
        cls,
        key: str | None,
        codes: dict[str, str],
        *,
        default: str | None = None,
        error: bool = True,
    ) -> Self | None:
        """Load a code from a known key and value dict."""
        value: str | None
        if not key:
            return None
        try:
            value = codes[key]
        except KeyError as exc:
            if error:
                msg = f"No code found for {key}"
                raise KeyError(msg) from exc
            value = default
        return cls(key, value or "Unknown")

    @classmethod
    def from_list(
        cls,
        keys: str | None,
        codes: dict[str, str],
        *,
        exclusive: bool = False,
    ) -> list[Self]:
        """Load a list of codes from string characters."""
        if not keys:
            return []
        out = []
        for key in keys.strip():
            if value := codes.get(key):
                out.append(cls(key, value))
            elif exclusive:
                return []
        return out


@dataclass
class Coord:
    lat: float
    lon: float
    repr: str | None = None

    @property
    def pair(self) -> tuple[float, float]:
        return self.lat, self.lon

    @property
    def point(self) -> Point:
        if Point is None:
            extra = "shape"
            raise MissingExtraModule(extra)
        return Point(self.lat, self.lon)

    @staticmethod
    def to_dms(value: float) -> tuple[int, int, int]:
        """Convert a coordinate decimal value to degree, minute, second."""
        minute, second = divmod(abs(value) * 3600, 60)
        degree, minute = divmod(minute, 60)
        if value < 0:
            degree *= -1
        return int(degree), int(minute), int(second)


@dataclass
class Cloud:
    repr: str
    type: str | None = None
    base: int | None = None
    top: int | None = None
    modifier: str | None = None


@dataclass
class RunwayVisibility:
    repr: str
    runway: str
    visibility: Number | None
    variable_visibility: list[Number]
    trend: Code | None


@dataclass
class Location:
    repr: str
    station: str | None
    direction: Number | None
    distance: Number | None


@dataclass
class PressureTendency:
    repr: str
    tendency: str
    change: float


@dataclass
class FiveDigitCodes:
    maximum_temperature_6: Number | None = None  # 1
    minimum_temperature_6: Number | None = None  # 2
    pressure_tendency: PressureTendency | None = None  # 5
    precip_36_hours: Number | None = None  # 6
    precip_24_hours: Number | None = None  # 7
    sunshine_minutes: Number | None = None  # 9


@dataclass
class RemarksData(FiveDigitCodes):
    codes: list[Code] = field(default_factory=list)
    dewpoint_decimal: Number | None = None
    maximum_temperature_24: Number | None = None
    minimum_temperature_24: Number | None = None
    precip_hourly: Number | None = None
    sea_level_pressure: Number | None = None
    snow_depth: Number | None = None
    temperature_decimal: Number | None = None


@dataclass
class ReportData:
    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None


@dataclass
class SharedData:
    altimeter: Number | None
    clouds: list[Cloud]
    flight_rules: str
    other: list[str]
    visibility: Number | None
    wind_direction: Number | None
    wind_gust: Number | None
    wind_speed: Number | None
    wx_codes: list[Code]


@dataclass
class MetarData(ReportData, SharedData):
    dewpoint: Number | None
    relative_humidity: float | None
    remarks_info: RemarksData | None
    runway_visibility: list[RunwayVisibility]
    temperature: Number | None
    wind_variable_direction: list[Number]
    density_altitude: int | None = None
    pressure_altitude: int | None = None


@dataclass
class TafLineData(SharedData):
    end_time: Timestamp | None
    icing: list[str]
    probability: Number | None
    raw: str
    sanitized: str
    start_time: Timestamp | None
    transition_start: Timestamp | None
    turbulence: list[str]
    type: str
    wind_shear: str | None
    wind_variable_direction: list[Number] | None


@dataclass
class TafData(ReportData):
    forecast: list[TafLineData]
    start_time: Timestamp | None
    end_time: Timestamp | None
    max_temp: str | None = None
    min_temp: str | None = None
    alts: list[str] | None = None
    temps: list[str] | None = None
    remarks_info: RemarksData | None = None


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
    forecast: list[TafLineTrans]
    max_temp: str
    min_temp: str
    remarks: dict


@dataclass
class Turbulence:
    severity: str
    floor: Number | None = None
    ceiling: Number | None = None


@dataclass
class Icing(Turbulence):
    type: str | None = None


@dataclass
class PirepData(ReportData):
    aircraft: Aircraft | str | None = None
    altitude: Number | str | None = None
    clouds: list[Cloud] | None = None
    flight_visibility: Number | None = None
    icing: Icing | None = None
    location: Location | None = None
    other: list[str] | None = None
    temperature: Number | None = None
    turbulence: Turbulence | None = None
    type: str | None = None
    wx_codes: list[Code] | None = None


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
    direction: Number | None
    speed: Number | None


MIN_POLY_SIZE = 2


@dataclass
class AirSigObservation:
    type: Code | None
    start_time: Timestamp | None
    end_time: Timestamp | None
    position: Coord | None
    floor: Number | None
    ceiling: Number | None
    coords: list[Coord]
    bounds: list[str]
    movement: Movement | None
    intensity: Code | None
    other: list[str]

    @property
    def poly(self) -> Polygon | None:
        if Polygon is None:
            extra = "shape"
            raise MissingExtraModule(extra)
        return Polygon([c.pair for c in self.coords]) if len(self.coords) > MIN_POLY_SIZE else None


@dataclass
class AirSigmetData(ReportData):
    bulletin: Bulletin
    issuer: str
    correction: str | None
    area: str
    type: str
    start_time: Timestamp | None
    end_time: Timestamp | None
    body: str
    region: str
    observation: AirSigObservation | None
    forecast: AirSigObservation | None


@dataclass
class Qualifiers:
    repr: str
    fir: str
    subject: Code | None
    condition: Code | None
    traffic: Code | None
    purpose: list[Code]
    scope: list[Code]
    lower: Number | None
    upper: Number | None
    coord: Coord | None
    radius: Number | None


@dataclass
class NotamData(ReportData):
    number: str | None
    replaces: str | None
    type: Code | None
    qualifiers: Qualifiers | None
    start_time: Timestamp | Code | None
    end_time: Timestamp | Code | None
    schedule: str | None
    body: str
    lower: Number | None
    upper: Number | None


@dataclass
class GfsPeriod:
    time: Timestamp
    temperature: Number
    dewpoint: Number
    cloud: Code
    temperature_minmax: Number | None = None
    precip_chance_12: Number | None = None
    precip_amount_12: Code | None = None
    thunderstorm_12: Number | None = None
    severe_storm_12: Number | None = None
    freezing_precip: Number | None = None
    precip_type: Code | None = None
    snow: Number | None = None


@dataclass
class MavPeriod(GfsPeriod):
    wind_direction: Number | None = None
    wind_speed: Number | None = None
    precip_chance_6: Number | None = None
    precip_amount_6: Code | None = None
    thunderstorm_6: Number | None = None
    severe_storm_6: Number | None = None
    ceiling: Code | None = None
    visibility: Code | None = None
    vis_obstruction: Code | None = None


@dataclass
class MexPeriod(GfsPeriod):
    precip_chance_24: Number | None = None
    precip_amount_24: Code | None = None
    thunderstorm_24: Number | None = None
    severe_storm_24: Number | None = None
    rain_snow_mix: Number | None = None
    snow_amount_24: Code | None = None


@dataclass
class MavData(ReportData):
    forecast: list[MavPeriod]


@dataclass
class MexData(ReportData):
    forecast: list[MexPeriod]


@dataclass
class NbmUnits(Units):
    duration: str
    solar_radiation: str
    wave_height: str


@dataclass
class NbmPeriod:
    time: Timestamp
    temperature: Number | None = None
    dewpoint: Number | None = None
    sky_cover: Number | None = None
    wind_direction: Number | None = None
    wind_speed: Number | None = None
    wind_gust: Number | None = None
    snow_level: Number | None = None
    precip_duration: Number | None = None
    freezing_precip: Number | None = None
    snow: Number | None = None
    sleet: Number | None = None
    rain: Number | None = None
    solar_radiation: Number | None = None
    wave_height: Number | None = None


@dataclass
class NbhsShared(NbmPeriod):
    ceiling: Number | None = None
    visibility: Number | None = None
    cloud_base: Number | None = None
    mixing_height: Number | None = None
    transport_wind_direction: Number | None = None
    transport_wind_speed: Number | None = None
    haines: list[Number] | None = None


@dataclass
class NbhPeriod(NbhsShared):
    precip_chance_1: Number | None = None
    precip_chance_6: Number | None = None
    precip_amount_1: Number | None = None
    thunderstorm_1: Number | None = None
    snow_amount_1: Number | None = None
    icing_amount_1: Number | None = None


@dataclass
class NbsPeriod(NbhsShared):
    temperature_minmax: Number | None = None
    precip_chance_6: Number | None = None
    precip_chance_12: Number | None = None
    precip_amount_6: Number | None = None
    precip_amount_12: Number | None = None
    precip_duration: Number | None = None
    thunderstorm_3: Number | None = None
    thunderstorm_6: Number | None = None
    thunderstorm_12: Number | None = None
    snow_amount_6: Number | None = None
    icing_amount_6: Number | None = None


@dataclass
class NbePeriod(NbmPeriod):
    temperature_minmax: Number | None = None
    precip_chance_12: Number | None = None
    precip_amount_12: Number | None = None
    precip_amount_24: Number | None = None
    thunderstorm_12: Number | None = None
    snow_amount_12: Number | None = None
    snow_amount_24: Number | None = None
    icing_amount_12: Number | None = None


@dataclass
class NbxPeriod(NbmPeriod):
    precip_chance_12: Number | None = None
    precip_amount_12: Number | None = None
    precip_amount_24: Number | None = None
    snow_amount_12: Number | None = None
    icing_amount_12: Number | None = None


@dataclass
class NbhData(ReportData):
    forecast: list[NbhPeriod]


@dataclass
class NbsData(ReportData):
    forecast: list[NbsPeriod]


@dataclass
class NbeData(ReportData):
    forecast: list[NbePeriod]


@dataclass
class NbxData(ReportData):
    forecast: list[NbxPeriod]


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
    """Tracks changes made during the sanitization process."""

    removed: list[str] = field(default_factory=list)
    replaced: dict[str, str] = field(default_factory=dict)
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

    def log(self, item: str, replacement: str | None = None) -> None:
        """Log a changed item. Calling without a replacement assumes removal."""
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

    def log_list(self, before: list[str], after: list[str]) -> None:
        """Log list differences. Assumes that list length and order haven't changed."""
        for item, replacement in zip(before, after, strict=True):
            if item != replacement:
                self.log(item, replacement)
