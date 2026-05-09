"""Pydantic models for all report data types.

Design principles
-----------------
* Physical measurements (:class:`~avwx.units.Measurement`) carry their own
  unit so callers never need a side-channel ``Units`` object.
* Every main report type exposes a *data* model (typed values) and a *repr*
  model (raw string tokens from the original report).
* All models are ``frozen=True`` — report data is immutable after parsing.
* :class:`FlightRules` is a :class:`~enum.StrEnum` so it integrates cleanly
  with FastAPI/FastMCP schema generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, TypeAlias

from pydantic import BaseModel, ConfigDict

from avwx.exceptions import MissingExtraModule
from avwx.load_utils import LazyLoad
from avwx.units import Measurement

if TYPE_CHECKING:
    pass

try:
    from shapely.geometry import Point, Polygon
except ModuleNotFoundError:
    Point, Polygon = TypeAlias, TypeAlias  # type: ignore[assignment,misc]

AIRCRAFT = LazyLoad("aircraft")


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------

_FROZEN: ConfigDict = ConfigDict(frozen=True)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class FlightRules(StrEnum):
    VFR = "VFR"
    MVFR = "MVFR"
    IFR = "IFR"
    LIFR = "LIFR"


# ---------------------------------------------------------------------------
# Primitive value types (non-physical)
# ---------------------------------------------------------------------------


class Code(BaseModel):
    """A raw token paired with its human-readable translation."""

    model_config = _FROZEN

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
    ) -> "Code | None":
        """Load a code from a known key/value mapping."""
        if not key:
            return None
        try:
            value = codes[key]
        except KeyError as exc:
            if error:
                msg = f"No code found for {key}"
                raise KeyError(msg) from exc
            value = default
        return cls(repr=key, value=value or "Unknown")

    @classmethod
    def from_list(
        cls,
        keys: str | None,
        codes: dict[str, str],
        *,
        exclusive: bool = False,
    ) -> list["Code"]:
        """Load a list of codes from individual characters of *keys*."""
        if not keys:
            return []
        out: list[Code] = []
        for key in keys.strip():
            if value := codes.get(key):
                out.append(cls(repr=key, value=value))
            elif exclusive:
                return []
        return out


class Timestamp(BaseModel):
    """A report timestamp with its raw string and parsed datetime."""

    model_config = _FROZEN

    repr: str
    dt: datetime | None


class ReportData(BaseModel):
    """Minimal report data shared by all report types."""

    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None


class Aircraft(BaseModel):
    """ICAO aircraft type."""

    model_config = _FROZEN

    code: str
    type: str

    @classmethod
    def from_icao(cls, code: str) -> "Aircraft":
        try:
            return cls(code=code, type=AIRCRAFT[code])
        except KeyError as exc:
            msg = f"{code} is not a known aircraft code"
            raise ValueError(msg) from exc


# ---------------------------------------------------------------------------
# Coordinate / geographic types
# ---------------------------------------------------------------------------


class Coord(BaseModel):
    """Geographic coordinate pair, optionally with a raw string repr."""

    model_config = _FROZEN

    lat: float
    lon: float
    repr: str | None = None

    @property
    def pair(self) -> tuple[float, float]:
        return self.lat, self.lon

    @property
    def point(self) -> Any:  # Polygon type is optional
        if Point is None:
            raise MissingExtraModule("shape")
        return Point(self.lat, self.lon)

    @staticmethod
    def to_dms(value: float) -> tuple[int, int, int]:
        """Convert a decimal coordinate value to (degree, minute, second)."""
        minute, second = divmod(abs(value) * 3600, 60)
        degree, minute = divmod(minute, 60)
        if value < 0:
            degree *= -1
        return int(degree), int(minute), int(second)


# ---------------------------------------------------------------------------
# Cloud
# ---------------------------------------------------------------------------


class Cloud(BaseModel):
    """A parsed cloud layer with typed altitude measurements."""

    model_config = _FROZEN

    type: str | None = None
    base: Measurement | None = None  # feet AGL
    top: Measurement | None = None   # feet AGL
    modifier: str | None = None


# ---------------------------------------------------------------------------
# Runway visibility
# ---------------------------------------------------------------------------


class RunwayVisibility(BaseModel):
    model_config = _FROZEN

    runway: str
    visibility: Measurement | None
    variable_visibility: list[Measurement]
    trend: Code | None


# ---------------------------------------------------------------------------
# Location (PIREP)
# ---------------------------------------------------------------------------


class Location(BaseModel):
    model_config = _FROZEN

    repr: str
    station: str | None
    direction: Measurement | None  # degrees
    distance: Measurement | None   # nautical miles


# ---------------------------------------------------------------------------
# Turbulence / Icing (PIREP)
# ---------------------------------------------------------------------------


class Turbulence(BaseModel):
    model_config = _FROZEN

    severity: str
    floor: Measurement | None = None
    ceiling: Measurement | None = None


class Icing(Turbulence):
    type: str | None = None


# ---------------------------------------------------------------------------
# Pressure tendency (remarks)
# ---------------------------------------------------------------------------


class PressureTendency(BaseModel):
    model_config = _FROZEN

    repr: str
    tendency: str
    change: Measurement  # pressure change amount


# ---------------------------------------------------------------------------
# Remarks
# ---------------------------------------------------------------------------


class FiveDigitCodes(BaseModel):
    model_config = _FROZEN

    maximum_temperature_6: Measurement | None = None
    minimum_temperature_6: Measurement | None = None
    pressure_tendency: PressureTendency | None = None
    precip_36_hours: Measurement | None = None
    precip_24_hours: Measurement | None = None
    sunshine_minutes: float | None = None
    severe_storm_12: Measurement | None = None


class RemarksData(FiveDigitCodes):
    codes: list[Code] = []
    dewpoint_decimal: Measurement | None = None
    maximum_temperature_24: Measurement | None = None
    minimum_temperature_24: Measurement | None = None
    precip_hourly: Measurement | None = None
    sea_level_pressure: Measurement | None = None
    snow_depth: Measurement | None = None
    temperature_decimal: Measurement | None = None


# ---------------------------------------------------------------------------
# Shared METAR/TAF data fields
# ---------------------------------------------------------------------------


class SharedData(BaseModel):
    """Fields common to METAR and individual TAF forecast lines."""

    model_config = _FROZEN

    altimeter: Measurement | None
    clouds: list[Cloud]
    flight_rules: FlightRules
    other: list[str]
    visibility: Measurement | None
    wind_direction: Measurement | None  # degrees
    wind_gust: Measurement | None
    wind_speed: Measurement | None
    wx_codes: list[Code]


class SharedRepr(BaseModel):
    """Raw string tokens for fields common to METAR and TAF lines."""

    model_config = _FROZEN

    altimeter: str | None
    clouds: list[str]
    other: list[str]
    visibility: str | None
    wind_direction: str | None
    wind_gust: str | None
    wind_speed: str | None
    wx_codes: list[str]


# ---------------------------------------------------------------------------
# METAR
# ---------------------------------------------------------------------------


class MetarData(SharedData):
    """Fully-typed METAR data.  All physical values are :class:`~avwx.units.Measurement`."""

    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    dewpoint: Measurement | None
    relative_humidity: float | None
    remarks_info: RemarksData | None
    runway_visibility: list[RunwayVisibility]
    temperature: Measurement | None
    wind_variable_direction: list[Measurement]
    density_altitude: Measurement | None = None
    pressure_altitude: Measurement | None = None


class MetarRepr(SharedRepr):
    """Raw token strings parallel to :class:`MetarData` — one per parsed field."""

    raw: str
    sanitized: str
    station: str | None
    time: str | None
    remarks: str | None
    dewpoint: str | None
    runway_visibility: list[str]
    temperature: str | None
    wind_variable_direction: list[str]


# ---------------------------------------------------------------------------
# TAF
# ---------------------------------------------------------------------------


class TafLineData(SharedData):
    end_time: Timestamp | None
    icing: list[str]
    probability: float | None
    raw: str
    sanitized: str
    start_time: Timestamp | None
    transition_start: Timestamp | None
    turbulence: list[str]
    type: str
    wind_shear: str | None
    wind_variable_direction: list[Measurement] | None


class TafLineRepr(SharedRepr):
    end_time: str | None
    icing: list[str]
    probability: str | None
    raw: str
    sanitized: str
    start_time: str | None
    turbulence: list[str]
    type: str
    wind_shear: str | None
    wind_variable_direction: list[str] | None


class TafData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    forecast: list[TafLineData]
    start_time: Timestamp | None
    end_time: Timestamp | None
    is_amended: bool
    is_correction: bool
    max_temp: str | None = None
    min_temp: str | None = None
    alts: list[str] | None = None
    temps: list[str] | None = None
    remarks_info: RemarksData | None = None


class TafRepr(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: str | None
    remarks: str | None
    forecast: list[TafLineRepr]


# ---------------------------------------------------------------------------
# Translation output structs  (kept as frozen Pydantic models)
# ---------------------------------------------------------------------------


class ReportTrans(BaseModel):
    model_config = _FROZEN

    altimeter: str
    clouds: str
    wx_codes: str
    visibility: str


class MetarTrans(ReportTrans):
    dewpoint: str
    remarks: dict[str, str]
    temperature: str
    wind: str


class TafLineTrans(ReportTrans):
    icing: str
    turbulence: str
    wind: str
    wind_shear: str


class TafTrans(BaseModel):
    model_config = _FROZEN

    forecast: list[TafLineTrans]
    max_temp: str
    min_temp: str
    remarks: dict[str, str]


# ---------------------------------------------------------------------------
# PIREP
# ---------------------------------------------------------------------------


class PirepData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    aircraft: Aircraft | str | None = None
    altitude: Measurement | str | None = None
    clouds: list[Cloud] | None = None
    flight_visibility: Measurement | None = None
    icing: Icing | None = None
    location: Location | None = None
    other: list[str] | None = None
    temperature: Measurement | None = None
    turbulence: Turbulence | None = None
    type: str | None = None
    wx_codes: list[Code] | None = None


class AirepData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None


# ---------------------------------------------------------------------------
# AIRMET / SIGMET
# ---------------------------------------------------------------------------


class Bulletin(BaseModel):
    model_config = _FROZEN

    repr: str
    type: Code
    country: str
    number: int


class Movement(BaseModel):
    model_config = _FROZEN

    repr: str
    direction: Measurement | None
    speed: Measurement | None


MIN_POLY_SIZE = 2


class AirSigObservation(BaseModel):
    model_config = _FROZEN

    type: Code | None
    start_time: Timestamp | None
    end_time: Timestamp | None
    position: Coord | None
    floor: Measurement | None
    ceiling: Measurement | None
    coords: list[Coord]
    bounds: list[str]
    movement: Movement | None
    intensity: Code | None
    other: list[str]

    @property
    def poly(self) -> Any:
        if Polygon is None:
            raise MissingExtraModule("shape")
        return Polygon([c.pair for c in self.coords]) if len(self.coords) > MIN_POLY_SIZE else None


class AirSigmetData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
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


# ---------------------------------------------------------------------------
# NOTAM
# ---------------------------------------------------------------------------


class Qualifiers(BaseModel):
    model_config = _FROZEN

    repr: str
    fir: str
    subject: Code | None
    condition: Code | None
    traffic: Code | None
    purpose: list[Code]
    scope: list[Code]
    lower: Measurement | None
    upper: Measurement | None
    coord: Coord | None
    radius: Measurement | None


class NotamData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    number: str | None
    replaces: str | None
    type: Code | None
    qualifiers: Qualifiers | None
    start_time: Timestamp | Code | None
    end_time: Timestamp | Code | None
    schedule: str | None
    body: str
    lower: Measurement | None
    upper: Measurement | None


# ---------------------------------------------------------------------------
# GFS forecasts
# ---------------------------------------------------------------------------


class GfsPeriod(BaseModel):
    model_config = _FROZEN

    time: Timestamp
    temperature: Measurement
    dewpoint: Measurement
    cloud: Code
    temperature_minmax: Measurement | None = None
    precip_chance_12: float | None = None
    precip_amount_12: Code | None = None
    thunderstorm_12: float | None = None
    severe_storm_12: float | None = None
    freezing_precip: float | None = None
    precip_type: Code | None = None
    snow: float | None = None


class MavPeriod(GfsPeriod):
    wind_direction: Measurement | None = None
    wind_speed: Measurement | None = None
    precip_chance_6: float | None = None
    precip_amount_6: Code | None = None
    thunderstorm_6: float | None = None
    severe_storm_6: float | None = None
    ceiling: Code | None = None
    visibility: Code | None = None
    vis_obstruction: Code | None = None


class MexPeriod(GfsPeriod):
    precip_chance_24: float | None = None
    precip_amount_24: Code | None = None
    thunderstorm_24: float | None = None
    severe_storm_24: float | None = None
    rain_snow_mix: float | None = None
    snow_amount_24: Code | None = None


class MavData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    forecast: list[MavPeriod]


class MexData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    forecast: list[MexPeriod]


# ---------------------------------------------------------------------------
# NBM forecasts
# ---------------------------------------------------------------------------


class NbmPeriod(BaseModel):
    model_config = _FROZEN

    time: Timestamp
    temperature: Measurement | None = None
    dewpoint: Measurement | None = None
    sky_cover: float | None = None
    wind_direction: Measurement | None = None
    wind_speed: Measurement | None = None
    wind_gust: Measurement | None = None
    snow_level: Measurement | None = None
    precip_duration: float | None = None
    freezing_precip: float | None = None
    snow: float | None = None
    sleet: float | None = None
    rain: float | None = None
    solar_radiation: float | None = None
    wave_height: Measurement | None = None


class NbhsShared(NbmPeriod):
    ceiling: Measurement | None = None
    visibility: Measurement | None = None
    cloud_base: Measurement | None = None
    mixing_height: Measurement | None = None
    transport_wind_direction: Measurement | None = None
    transport_wind_speed: Measurement | None = None
    haines: float | None = None


class NbhPeriod(NbhsShared):
    precip_chance_1: float | None = None
    precip_chance_6: float | None = None
    precip_amount_1: Measurement | None = None
    thunderstorm_1: float | None = None
    snow_amount_1: Measurement | None = None
    icing_amount_1: Measurement | None = None


class NbsPeriod(NbhsShared):
    temperature_minmax: Measurement | None = None
    precip_chance_6: float | None = None
    precip_chance_12: float | None = None
    precip_amount_6: Measurement | None = None
    precip_amount_12: Measurement | None = None
    precip_duration: float | None = None
    thunderstorm_3: float | None = None
    thunderstorm_6: float | None = None
    thunderstorm_12: float | None = None
    snow_amount_6: Measurement | None = None
    icing_amount_6: Measurement | None = None


class NbePeriod(NbmPeriod):
    temperature_minmax: Measurement | None = None
    precip_chance_12: float | None = None
    precip_amount_12: Measurement | None = None
    precip_amount_24: Measurement | None = None
    thunderstorm_12: float | None = None
    snow_amount_12: Measurement | None = None
    snow_amount_24: Measurement | None = None
    icing_amount_12: Measurement | None = None


class NbxPeriod(NbmPeriod):
    precip_chance_12: float | None = None
    precip_amount_12: Measurement | None = None
    precip_amount_24: Measurement | None = None
    snow_amount_12: Measurement | None = None
    icing_amount_12: Measurement | None = None


class NbhData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    forecast: list[NbhPeriod]


class NbsData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    forecast: list[NbsPeriod]


class NbeData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    forecast: list[NbePeriod]


class NbxData(BaseModel):
    model_config = _FROZEN

    raw: str
    sanitized: str
    station: str | None
    time: Timestamp | None
    remarks: str | None
    forecast: list[NbxPeriod]


# ---------------------------------------------------------------------------
# Sanitization log  (mutable — used only during parsing)
# ---------------------------------------------------------------------------


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
        """Log a changed item.  Calling without a replacement assumes removal."""
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
        """Log list differences (assumes length and order are unchanged)."""
        for item, replacement in zip(before, after, strict=True):
            if item != replacement:
                self.log(item, replacement)
