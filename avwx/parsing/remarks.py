"""
Contains functions for handling and translating remarks
"""

# pylint: disable=redefined-builtin

# stdlib
from contextlib import suppress
from typing import List, Optional, Tuple

# module
from avwx.parsing import core
from avwx.static.core import REMARKS_ELEMENTS, REMARKS_GROUPS, WX_TRANSLATIONS
from avwx.static.taf import PRESSURE_TENDENCIES
from avwx.structs import Code, FiveDigitCodes, Number, PressureTendency, RemarksData


Codes = List[str]


def decimal_code(code: str, repr: Optional[str] = None) -> Optional[Number]:
    """Parses a 4-digit decimal temperature representation

    Ex: 1045 -> -4.5    0237 -> 23.7
    """
    if not code:
        return None
    number = f"{'-' if code[0] == '1' else ''}{int(code[1:3])}.{code[3]}"
    return core.make_number(number, repr or code)


def temp_dew_decimal(codes: Codes) -> Tuple[Codes, Optional[Number], Optional[Number]]:
    """Returns the decimal temperature and dewpoint values"""
    temp, dew = None, None
    for i, code in reversed(list(enumerate(codes))):
        if len(code) in [5, 9] and code[0] == "T" and code[1:].isdigit():
            codes.pop(i)
            temp, dew = decimal_code(code[1:5]), decimal_code(code[5:])
            break
    return codes, temp, dew


def temp_minmax(codes: Codes) -> Tuple[Codes, Optional[Number], Optional[Number]]:
    """Returns the 24-hour minimum and maximum temperatures"""
    maximum, minimum = None, None
    for i, code in enumerate(codes):
        if len(code) == 9 and code[0] == "4" and code.isdigit():
            maximum, minimum = decimal_code(code[1:5]), decimal_code(code[5:])
            codes.pop(i)
            break
    return codes, maximum, minimum


def precip_snow(codes: Codes) -> Tuple[Codes, Optional[Number], Optional[Number]]:
    """Returns the hourly precipitation and snow depth"""
    precip, snow = None, None
    for i, code in reversed(list(enumerate(codes))):
        if len(code) != 5:
            continue
        # P0213
        if code[0] == "P" and code[1:].isdigit():
            precip = core.make_number(f"{code[1:3]}.{code[3:]}", code)
            codes.pop(i)
        # 4/012
        elif code[:2] == "4/" and code[2:].isdigit():
            snow = core.make_number(code[2:], code)
            codes.pop(i)
    return codes, precip, snow


def sea_level_pressure(codes: Codes) -> Tuple[Codes, Optional[Number]]:
    """Returns the sea level pressure always in hPa"""
    sea = None
    for i, code in enumerate(codes):
        if len(code) == 6 and code.startswith("SLP") and code[-3:].isdigit():
            value = f"{'9' if int(code[-3]) > 4 else '10'}{code[-3:-1]}.{code[-1]}"
            sea = core.make_number(value, code)
            codes.pop(i)
            break
    return codes, sea


def parse_pressure(code: str) -> PressureTendency:
    """Parse a 5-digit pressure tendency"""
    return PressureTendency(
        repr=code,
        tendency=PRESSURE_TENDENCIES[code[1]],
        change=float(f"{code[2:4]}.{code[4]}"),
    )


def parse_precipitation(code: str) -> Optional[Number]:
    """Parse a 5-digit precipitation amount"""
    return core.make_number(f"{code[1:3]}.{code[3:]}", code)


def five_digit_codes(codes: Codes) -> Tuple[Codes, FiveDigitCodes]:
    """Returns  a 5-digit min/max temperature code"""
    values = FiveDigitCodes()
    for i, code in reversed(list(enumerate(codes))):
        if len(code) == 5 and code.isdigit():
            key = int(code[0])
            if key == 1:
                values.maximum_temperature_6 = decimal_code(code[1:], code)
            elif key == 2:
                values.minimum_temperature_6 = decimal_code(code[1:], code)
            elif key == 5:
                values.pressure_tendency = parse_pressure(code)
            elif key == 6:
                values.precip_36_hours = parse_precipitation(code)
            elif key == 7:
                values.precip_24_hours = parse_precipitation(code)
            elif key == 9:
                values.sunshine_minutes = core.make_number(code[2:], code)
            else:
                continue
            codes.pop(i)
    return codes, values


def find_codes(rmk: str) -> Tuple[Codes, List[Code]]:
    """Find a remove known static codes from the starting remarks list"""
    ret = []
    for key, value in REMARKS_GROUPS.items():
        if key in rmk:
            ret.append(Code(key, value))
            rmk.replace(key, "")
    codes = [i for i in rmk.split() if i]
    for i, code in reversed(list(enumerate(codes))):
        with suppress(KeyError):
            ret.append(Code(code, REMARKS_ELEMENTS[code]))
            codes.pop(i)
        # Weather began/ended
        if (
            len(code) == 5
            and code[2] in ("B", "E")
            and code[3:].isdigit()
            and code[:2] in WX_TRANSLATIONS
        ):
            state = "began" if code[2] == "B" else "ended"
            value = f"{WX_TRANSLATIONS[code[:2]]} {state} at :{code[3:]}"
            ret.append(Code(code, value))
            codes.pop(i)
    ret.sort(key=lambda x: x.repr)
    return codes, ret


def parse(rmk: str) -> Optional[RemarksData]:
    """Finds temperature and dewpoint decimal values from the remarks"""
    if not rmk:
        return None
    codes, parsed_codes = find_codes(rmk)
    codes, temperature, dewpoint = temp_dew_decimal(codes)
    codes, max_temp, min_temp = temp_minmax(codes)
    codes, precip, snow = precip_snow(codes)
    codes, sea = sea_level_pressure(codes)
    codes, fivedigits = five_digit_codes(codes)
    return RemarksData(
        codes=parsed_codes,
        dewpoint_decimal=dewpoint,
        temperature_decimal=temperature,
        minimum_temperature_6=fivedigits.minimum_temperature_6,
        minimum_temperature_24=min_temp,
        maximum_temperature_6=fivedigits.maximum_temperature_6,
        maximum_temperature_24=max_temp,
        pressure_tendency=fivedigits.pressure_tendency,
        precip_36_hours=fivedigits.precip_36_hours,
        precip_24_hours=fivedigits.precip_24_hours,
        sunshine_minutes=fivedigits.sunshine_minutes,
        precip_hourly=precip,
        snow_depth=snow,
        sea_level_pressure=sea,
    )
