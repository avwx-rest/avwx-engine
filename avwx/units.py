"""Unit types and Measurement wrapper for typed physical quantities.

All parsed physical values (wind speed, visibility, temperature, …) are
returned as :class:`Measurement` objects so the numeric magnitude and its
unit travel together.  Consumers can convert freely::

    speed = Measurement(10, "kt")
    speed.to("m/s")          # Measurement(5.144..., 'm / s')
    speed.quantity           # pint.Quantity(10, 'knot')

Unit strings used throughout the library are defined as :class:`StrEnum`
members so the valid options are self-documenting and API-schema-friendly.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

import pint
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

# ---------------------------------------------------------------------------
# Unit registry
# ---------------------------------------------------------------------------

_ureg = pint.UnitRegistry()

# Aviation-specific aliases that Pint doesn't know by default.
_ureg.define("sm = mile")  # statute miles
_ureg.define("kt = knot")  # knots (avoids collision with kilo-tonne)
_ureg.define("inHg = inch_Hg")  # inches of mercury


def _parse_unit(value: float | int, unit: str) -> pint.Quantity:
    return _ureg.Quantity(value, unit)


# ---------------------------------------------------------------------------
# Unit enums
# ---------------------------------------------------------------------------


class WindUnit(StrEnum):
    KNOTS = "kt"
    METERS_PER_SECOND = "m/s"
    KMH = "km/h"
    MPH = "mph"


class VisibilityUnit(StrEnum):
    STATUTE_MILES = "sm"
    METERS = "m"
    KILOMETERS = "km"


class AltimeterUnit(StrEnum):
    INHG = "inHg"
    HPA = "hPa"


class TemperatureUnit(StrEnum):
    CELSIUS = "degC"
    FAHRENHEIT = "degF"


class AltitudeUnit(StrEnum):
    FEET = "ft"
    METERS = "m"


class AccumulationUnit(StrEnum):
    INCHES = "in"
    MILLIMETERS = "mm"


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------


class Measurement:
    """A physical quantity that is Pydantic-serialisable and Pint-backed.

    Serialises to ``{"magnitude": float, "unit": str}`` so FastAPI / FastMCP
    consumers get self-describing values with no side-channel unit lookup.

    Conversion is first-class::

        m = Measurement(9000, "m")
        m.to("sm")          # Measurement(5.592..., 'sm')
        m.to("km")          # Measurement(9.0, 'km')
    """

    __slots__ = ("_q", "_unit_str")

    def __init__(self, magnitude: float | int, unit: str) -> None:
        self._q: pint.Quantity = _parse_unit(magnitude, unit)
        self._unit_str: str = unit

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def magnitude(self) -> float:
        return float(self._q.magnitude)

    @property
    def unit(self) -> str:
        return self._unit_str

    @property
    def quantity(self) -> pint.Quantity:
        return self._q

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to(self, unit: str | StrEnum) -> "Measurement":
        """Return a new Measurement converted to *unit*."""
        target = str(unit)
        converted = self._q.to(target)
        return Measurement(float(converted.magnitude), target)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Measurement):
            try:
                return bool(self._q == other._q.to(self._q.units))
            except pint.DimensionalityError:
                return False
        return NotImplemented

    def __repr__(self) -> str:
        return f"Measurement({self.magnitude!r}, {self.unit!r})"

    def __hash__(self) -> int:
        return hash((self.magnitude, self.unit))

    # ------------------------------------------------------------------
    # Pydantic v2 integration
    # ------------------------------------------------------------------

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type,  # noqa: ARG003
        handler: GetCoreSchemaHandler,  # noqa: ARG003
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                info_arg=False,
                return_schema=core_schema.dict_schema(),
            ),
        )

    @classmethod
    def _validate(cls, v: Any) -> "Measurement":
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            return cls(v["magnitude"], v["unit"])
        if isinstance(v, pint.Quantity):
            return cls(float(v.magnitude), str(v.units))
        msg = f"Cannot construct Measurement from {type(v).__name__}"
        raise ValueError(msg)

    @staticmethod
    def _serialize(v: "Measurement") -> dict[str, Any]:
        return {"magnitude": v.magnitude, "unit": v.unit}
