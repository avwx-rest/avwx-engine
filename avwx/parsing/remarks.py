"""Functions for parsing and translating METAR/TAF remarks."""

from __future__ import annotations

from contextlib import suppress

from avwx.static.core import REMARKS_ELEMENTS, REMARKS_GROUPS, WX_TRANSLATIONS
from avwx.static.taf import PRESSURE_TENDENCIES
from avwx.structs import Code, FiveDigitCodes, PressureTendency, RemarksData
from avwx.units import Measurement

Codes = list[str]


def _decimal_temp(code: str) -> Measurement | None:
    """Parse a 4-digit decimal temperature code.

    Examples::

        1045 → -4.5 °C
        0237 → 23.7 °C
    """
    if not code:
        return None
    sign = -1 if code[0] == "1" else 1
    value = sign * float(f"{int(code[1:3])}.{code[3]}")
    return Measurement(value, "degC")


def temp_dew_decimal(
    codes: Codes,
) -> tuple[Codes, Measurement | None, Measurement | None]:
    """Extract optional decimal temperature/dewpoint from remarks tokens."""
    temp, dew = None, None
    for i, code in reversed(list(enumerate(codes))):
        if len(code) in {5, 9} and code[0] == "T" and code[1:].isdigit():
            codes.pop(i)
            temp = _decimal_temp(code[1:5])
            dew = _decimal_temp(code[5:]) if len(code) == 9 else None
            break
    return codes, temp, dew


def temp_minmax(
    codes: Codes,
) -> tuple[Codes, Measurement | None, Measurement | None]:
    """Extract 24-hour min/max temperatures."""
    maximum, minimum = None, None
    for i, code in enumerate(codes):
        if len(code) == 9 and code[0] == "4" and code.isdigit():
            maximum = _decimal_temp(code[1:5])
            minimum = _decimal_temp(code[5:])
            codes.pop(i)
            break
    return codes, maximum, minimum


def precip_snow(
    codes: Codes,
) -> tuple[Codes, Measurement | None, Measurement | None]:
    """Extract hourly precipitation and snow depth."""
    precip: Measurement | None = None
    snow: Measurement | None = None
    for i, code in reversed(list(enumerate(codes))):
        if len(code) != 5:
            continue
        if code[0] == "P" and code[1:].isdigit():
            precip = Measurement(float(f"{code[1:3]}.{code[3:]}"), "in")
            codes.pop(i)
        elif code[:2] == "4/" and code[2:].isdigit():
            snow = Measurement(int(code[2:]), "in")
            codes.pop(i)
    return codes, precip, snow


def sea_level_pressure(codes: Codes) -> tuple[Codes, Measurement | None]:
    """Extract sea-level pressure (always in hPa)."""
    sea: Measurement | None = None
    for i, code in enumerate(codes):
        if len(code) == 6 and code.startswith("SLP") and code[-3:].isdigit():
            value = float(f"{'9' if int(code[-3]) > 4 else '10'}{code[-3:-1]}.{code[-1]}")
            sea = Measurement(value, "hPa")
            codes.pop(i)
            break
    return codes, sea


def _precip_measurement(code: str) -> Measurement | None:
    """Parse a 5-digit precipitation amount into inches."""
    try:
        return Measurement(float(f"{code[1:3]}.{code[3:]}"), "in")
    except ValueError:
        return None


def five_digit_codes(codes: Codes) -> tuple[Codes, FiveDigitCodes]:
    """Parse 5-digit remark codes into typed values."""
    maximums: dict[str, Measurement | None] = {}
    minimums: dict[str, Measurement | None] = {}
    pressure_tendency: PressureTendency | None = None
    precip_36: Measurement | None = None
    precip_24: Measurement | None = None
    sunshine: float | None = None

    for i, code in reversed(list(enumerate(codes))):
        if len(code) == 5 and code.isdigit():
            key = int(code[0])
            if key == 1:
                maximums["6h"] = _decimal_temp(code[1:])
            elif key == 2:
                minimums["6h"] = _decimal_temp(code[1:])
            elif key == 5:
                tendency = PRESSURE_TENDENCIES.get(code[1], "Unknown")
                change_val = float(f"{code[2:4]}.{code[4]}")
                pressure_tendency = PressureTendency(
                    repr=code,
                    tendency=tendency,
                    change=Measurement(change_val, "hPa"),
                )
            elif key == 6:
                precip_36 = _precip_measurement(code)
            elif key == 7:
                precip_24 = _precip_measurement(code)
            elif key == 9:
                with suppress(ValueError):
                    sunshine = float(code[2:])
            else:
                continue
            codes.pop(i)

    return codes, FiveDigitCodes(
        maximum_temperature_6=maximums.get("6h"),
        minimum_temperature_6=minimums.get("6h"),
        pressure_tendency=pressure_tendency,
        precip_36_hours=precip_36,
        precip_24_hours=precip_24,
        sunshine_minutes=sunshine,
    )


def find_codes(rmk: str) -> tuple[Codes, list[Code]]:
    """Extract and remove known static codes from the remarks string."""
    ret: list[Code] = []
    for key, value in REMARKS_GROUPS.items():
        if key in rmk:
            ret.append(Code(repr=key, value=value))
            rmk = rmk.replace(key, "")
    codes = [i for i in rmk.split() if i]
    for i, code in reversed(list(enumerate(codes))):
        with suppress(KeyError):
            ret.append(Code(repr=code, value=REMARKS_ELEMENTS[code]))
            codes.pop(i)
            continue
        if (
            len(code) == 5
            and code[2] in ("B", "E")
            and code[3:].isdigit()
            and code[:2] in WX_TRANSLATIONS
        ):
            state = "began" if code[2] == "B" else "ended"
            value = f"{WX_TRANSLATIONS[code[:2]]} {state} at :{code[3:]}"
            ret.append(Code(repr=code, value=value))
            codes.pop(i)
    ret.sort(key=lambda x: x.repr)
    return codes, ret


def parse(rmk: str) -> RemarksData | None:
    """Parse a remarks string into a :class:`~avwx.structs.RemarksData` model."""
    if not rmk:
        return None
    codes, parsed_codes = find_codes(rmk)
    codes, temperature, dewpoint = temp_dew_decimal(codes)
    codes, max_temp_24, min_temp_24 = temp_minmax(codes)
    codes, precip, snow = precip_snow(codes)
    codes, sea = sea_level_pressure(codes)
    codes, fivedigits = five_digit_codes(codes)
    return RemarksData(
        codes=parsed_codes,
        dewpoint_decimal=dewpoint,
        temperature_decimal=temperature,
        minimum_temperature_6=fivedigits.minimum_temperature_6,
        minimum_temperature_24=min_temp_24,
        maximum_temperature_6=fivedigits.maximum_temperature_6,
        maximum_temperature_24=max_temp_24,
        pressure_tendency=fivedigits.pressure_tendency,
        precip_36_hours=fivedigits.precip_36_hours,
        precip_24_hours=fivedigits.precip_24_hours,
        sunshine_minutes=fivedigits.sunshine_minutes,
        precip_hourly=precip,
        snow_depth=snow,
        sea_level_pressure=sea,
    )
