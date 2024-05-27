"""Contains the core parsing and indent functions of avwx."""

# stdlib
from __future__ import annotations

import datetime as dt
import math
import re
from calendar import monthrange
from contextlib import suppress
from copy import copy
from typing import TYPE_CHECKING, Any

# library
from dateutil.relativedelta import relativedelta

# module
from avwx.static.core import (
    CARDINALS,
    CLOUD_LIST,
    FRACTIONS,
    NUMBER_REPL,
    SPECIAL_NUMBERS,
    WIND_UNITS,
)
from avwx.structs import Cloud, Fraction, Number, Timestamp, Units

if TYPE_CHECKING:
    from collections.abc import Iterable


def dedupe(items: Iterable[Any], *, only_neighbors: bool = False) -> list[Any]:
    """Deduplicate a list while keeping order.

    If only_neighbors is True, dedupe will only check neighboring values.
    """
    ret: list[Any] = []
    for item in items:
        if (only_neighbors and ret and ret[-1] != item) or item not in ret:
            ret.append(item)
    return ret


def is_unknown(value: str) -> bool:
    """Return True if val represents and unknown value."""
    if not isinstance(value, str):
        raise TypeError
    if not value or value.upper() in {"UNKN", "UNK", "UKN"}:
        return True
    for char in value:
        if char not in ("/", "X", "."):
            break
    else:
        return True
    return False


def get_digit_list(data: list[str], from_index: int) -> tuple[list[str], list[str]]:
    """Return a list of items removed from a given list of strings
    that are all digits from 'from_index' until hitting a non-digit item.
    """
    ret = []
    data.pop(from_index)
    while len(data) > from_index and data[from_index].isdigit():
        ret.append(data.pop(from_index))
    return data, ret


def unpack_fraction(num: str) -> str:
    """Return unpacked fraction string 5/2 -> 2 1/2."""
    numbers = [int(n) for n in num.split("/") if n]
    if len(numbers) != 2 or numbers[0] <= numbers[1]:
        return num
    numerator, denominator = numbers
    over = numerator // denominator
    rem = numerator % denominator
    return f"{over} {rem}/{denominator}"


def remove_leading_zeros(num: str) -> str:
    """Strip zeros while handling -, M, and empty strings."""
    if not num:
        return num
    if num.startswith("M"):
        ret = "M" + num[1:].lstrip("0")
    elif num.startswith("-"):
        ret = "-" + num[1:].lstrip("0")
    else:
        ret = num.lstrip("0")
    return "0" if ret in ("", "M", "-") else ret


SPOKEN_POSTFIX = (
    (" zero zero zero", " thousand"),
    (" zero zero", " hundred"),
)


def spoken_number(num: str, *, literal: bool = False) -> str:
    """Return the spoken version of a number.

    If literal, no conversion to hundreds/thousands

    Ex: 1.2 -> one point two
        1 1/2 -> one and one half
        25000 -> two five thousand
    """
    ret = []
    for part in num.split():
        if part in FRACTIONS:
            ret.append(FRACTIONS[part])
        else:
            val = " ".join(NUMBER_REPL[char] for char in part if char in NUMBER_REPL)
            if not literal:
                for target, replacement in SPOKEN_POSTFIX:
                    if val.endswith(target):
                        val = val[: -len(target)] + replacement
            ret.append(val)
    return " and ".join(ret)


def make_fraction(
    num: str,
    repr: str | None = None,  # noqa: A002
    *,
    literal: bool = False,
    speak_prefix: str = "",
) -> Fraction:
    """Return a fraction dataclass for numbers with / in them."""
    num_str, den_str = num.split("/")
    # 2-1/2 but not -2 1/2
    if "-" in num_str and not num_str.startswith("-"):
        num_str = num_str.replace("-", " ")
    denominator = int(den_str)
    # Multiply multi-digit numerator
    if len(num_str) > 1:
        numerator = int(num_str[:-1]) * denominator + int(num_str[-1])
        num = f"{numerator}/{denominator}"
    else:
        numerator = int(num_str)
    value = numerator / denominator
    unpacked = unpack_fraction(num)
    spoken = speak_prefix + spoken_number(unpacked, literal=literal)
    return Fraction(repr or num, value, spoken, numerator, denominator, unpacked)


def make_number(
    num: str | None,
    repr: str | None = None,  # noqa: A002
    speak: str | None = None,
    *,
    literal: bool = False,
    special: dict | None = None,
    m_minus: bool = True,
) -> Number | Fraction | None:
    """Return a Number or Fraction dataclass for a number string.

    If literal, spoken string will not convert to hundreds/thousands.

    NOTE: Numerators are assumed to have a single digit. Additional are whole numbers.
    """
    if not num or is_unknown(num):
        return None
    # Check special
    with suppress(KeyError):
        item = (special or {}).get(num) or SPECIAL_NUMBERS[num]
        if isinstance(item, tuple):
            value, spoken = item
        else:
            value = item
            spoken = spoken_number(str(value), literal=literal)
        return Number(repr or num, value, spoken)
    # Check cardinal direction
    if num in CARDINALS:
        if not repr:
            repr = num  # noqa: A001
        num = str(CARDINALS[num])
    val_str = num
    # Remove unit suffixes
    if val_str.endswith("SM"):
        repr = val_str[:]  # noqa: A001
        val_str = val_str[:-2]
    # Remove spurious characters from the end
    num = num.rstrip("M.")
    num = num.replace("O", "0")
    num = num.replace("+", "")
    num = num.replace(",", "")
    # Handle Minus values with errors like 0M04
    if m_minus and "M" in num:
        val_str = num.replace("MM", "-").replace("M", "-")
        while val_str[0] != "-":
            val_str = val_str[1:]
    # Check value prefixes
    speak_prefix = ""
    if val_str.startswith("ABV "):
        speak_prefix += "above "
        val_str = val_str[4:]
    if val_str.startswith("BLW "):
        speak_prefix += "below "
        val_str = val_str[4:]
    if val_str.startswith("FL"):
        speak_prefix += "flight level "
        val_str, literal = val_str[2:], True
    if val_str.startswith("M"):
        speak_prefix += "less than "
        repr = repr or val_str  # noqa: A001
        val_str = val_str[1:]
    if val_str.startswith("P"):
        speak_prefix += "greater than "
        repr = repr or val_str  # noqa: A001
        val_str = val_str[1:]
    # Create Number
    if not val_str:
        return None
    ret: Number | Fraction | None = None
    # Create Fraction
    if "/" in val_str:
        ret = make_fraction(val_str, repr, literal=literal, speak_prefix=speak_prefix)
    else:
        # Overwrite float 0 due to "0.0" literal
        value = float(val_str) or 0 if "." in num else int(val_str)
        spoken = speak_prefix + spoken_number(speak or str(value), literal=literal)
        ret = Number(repr or num, value, spoken)
    # Null the value if "greater than"/"less than"
    if ret and not m_minus and repr and repr.startswith(("M", "P")):
        ret.value = None
    return ret


def find_first_in_list(txt: str, str_list: list[str]) -> int:
    """Return the index of the earliest occurrence of an item from a list in a string.

    Ex: find_first_in_list('foobar', ['bar', 'fin']) -> 3
    """
    start = len(txt) + 1
    for item in str_list:
        if start > txt.find(item) > -1:
            start = txt.find(item)
    return start if len(txt) + 1 > start > -1 else -1


def is_timestamp(item: str) -> bool:
    """Return True if the item matches the timestamp format."""
    return len(item) == 7 and item[-1] == "Z" and item[:-1].isdigit()


def is_timerange(item: str) -> bool:
    """Return True if the item is a TAF to-from time range."""
    return len(item) == 9 and item[4] == "/" and item[:4].isdigit() and item[5:].isdigit()


def is_possible_temp(temp: str) -> bool:
    """Return True if all characters are digits or 'M' for minus."""
    return all((char.isdigit() or char == "M") for char in temp)


_Numeric = int | float


def relative_humidity(temperature: _Numeric, dewpoint: _Numeric, unit: str = "C") -> float:
    """Calculate the relative humidity as a 0 to 1 percentage."""

    def saturation(value: _Numeric) -> float:
        """Return the saturation vapor pressure without the C constant for humidity calc."""
        return math.exp((17.67 * value) / (243.5 + value))

    if unit == "F":
        dewpoint = (dewpoint - 32) * 5 / 9
        temperature = (temperature - 32) * 5 / 9
    return saturation(dewpoint) / saturation(temperature)


# https://aviation.stackexchange.com/questions/47971/how-do-i-calculate-density-altitude-by-hand


def pressure_altitude(pressure: float, altitude: _Numeric, unit: str = "inHg") -> int:
    """Calculate the pressure altitude in feet. Converts pressure units."""
    if unit == "hPa":
        pressure *= 0.02953
    return round((29.92 - pressure) * 1000 + altitude)


def density_altitude(pressure: float, temperature: _Numeric, altitude: _Numeric, units: Units) -> int:
    """Calculate the density altitude in feet. Converts pressure and temperature units."""
    if units.temperature == "F":
        temperature = (temperature - 32) * 5 / 9
    if units.altimeter == "hPa":
        pressure *= 0.02953
    pressure_alt = pressure_altitude(pressure, altitude)
    standard = 15 - (2 * altitude / 1000)
    return round(((temperature - standard) * 120) + pressure_alt)


def get_station_and_time(
    data: list[str],
) -> tuple[list[str], str | None, str | None]:
    """Return the report list and removed station ident and time strings."""
    if not data:
        return data, None, None
    station = data.pop(0)
    if not data:
        return data, station, None
    q_time, r_time = data[0], None
    if data and q_time.endswith("Z") and q_time[:-1].isdigit():
        r_time = data.pop(0)
    elif data and len(q_time) == 6 and q_time.isdigit():
        r_time = f"{data.pop(0)}Z"
    return data, station, r_time


def is_wind(text: str) -> bool:
    """Return True if the text is likely a normal wind element."""
    # Ignore wind shear
    if text.startswith("WS"):
        return False
    # 09010KT, 09010G15KT
    if len(text) > 4:
        for ending in WIND_UNITS:
            unit_index = text.find(ending)
            if text.endswith(ending) and text[unit_index - 2 : unit_index].isdigit():
                return True
    # 09010  09010G15 VRB10
    if len(text) != 5 and (len(text) < 8 or "G" not in text or "/" in text):
        return False
    return text[:5].isdigit() or (text.startswith("VRB") and text[3:5].isdigit())


VARIABLE_DIRECTION_PATTERN = re.compile(r"\d{3}V\d{3}")


def is_variable_wind_direction(text: str) -> bool:
    """Return True if element looks like 350V040."""
    if len(text) < 7:
        return False
    return VARIABLE_DIRECTION_PATTERN.match(text[:7]) is not None


def separate_wind(text: str) -> tuple[str, str, str]:
    """Extract the direction, speed, and gust from a wind element."""
    direction, speed, gust = "", "", ""
    # Remove gust
    if "G" in text:
        g_index = text.find("G")
        start, end = g_index + 1, g_index + 3
        # 16006GP99KT ie gust greater than
        if "GP" in text:
            end += 1
        gust = text[start:end]
        text = text[:g_index] + text[end:]
    if text:
        # 10G18KT
        if len(text) == 2:
            speed = text
        else:
            direction = text[:3]
            speed = text[3:]
    return direction, speed, gust


def get_wind(
    data: list[str], units: Units
) -> tuple[
    list[str],
    Number | None,
    Number | None,
    Number | None,
    list[Number],
]:
    """Return the report list, direction string, speed string, gust string, and variable direction list."""
    direction, speed, gust = "", "", ""
    variable: list[Number] = []
    # Remove unit and split elements
    if data:
        item = copy(data[0])
        if is_wind(item):
            for key, unit in WIND_UNITS.items():
                if item.endswith(key):
                    units.wind_speed = unit
                    item = item.replace(key, "")
                    break
            direction, speed, gust = separate_wind(item)
            data.pop(0)
    # Separated Gust
    if data and 1 < len(data[0]) < 4 and data[0][0] == "G" and data[0][1:].isdigit():
        gust = data.pop(0)[1:]
    # Variable Wind Direction
    if data and is_variable_wind_direction(data[0]):
        for item in data.pop(0).split("V"):
            value = make_number(item, speak=item, literal=True)
            if value is not None:
                variable.append(value)
    # Convert to Number
    direction_value = make_number(direction, speak=direction, literal=True)
    speed_value = make_number(speed.strip("BV"), m_minus=False)
    gust_value = make_number(gust, m_minus=False)
    return data, direction_value, speed_value, gust_value, variable


def get_visibility(data: list[str], units: Units) -> tuple[list[str], Number | None]:
    """Return the report list and removed visibility string."""
    visibility = ""
    if data:
        item = copy(data[0])
        # Vis reported in statue miles
        if item.endswith("SM"):  # 10SM
            if item[:-2].isdigit():
                visibility = str(int(item[:-2]))
            elif "/" in item:
                visibility = item[: item.find("SM")]  # 1/2SM
            else:
                visibility = item[:-2]
            data.pop(0)
            units.visibility = "sm"
        # Vis reported in meters
        elif len(item) == 4 and item.isdigit():
            visibility = data.pop(0)
            units.visibility = "m"
        elif 7 >= len(item) >= 5 and item[:4].isdigit() and (item[4] in ["M", "N", "S", "E", "W"] or item[4:] == "NDV"):
            visibility = data.pop(0)[:4]
            units.visibility = "m"
        elif len(item) == 5 and item[1:].isdigit() and item[0] in ["M", "P", "B"]:
            visibility = data.pop(0)[1:]
            units.visibility = "m"
        elif item.endswith("KM"):
            visibility = f"{item[:-2]}000"
            data.pop(0)
            units.visibility = "m"
        # Vis statute miles but split Ex: 2 1/2SM
        elif len(data) > 1 and data[1].endswith("SM") and "/" in data[1] and item.isdigit():
            vis1 = data.pop(0)  # 2
            vis2 = data.pop(0).replace("SM", "")  # 1/2
            visibility = str(int(vis1) * int(vis2[2]) + int(vis2[0])) + vis2[1:]  # 5/2
            units.visibility = "sm"
    return data, make_number(visibility, m_minus=False)


def sanitize_cloud(cloud: str) -> str:
    """Fix rare cloud layer issues."""
    if len(cloud) < 4:
        return cloud
    if not cloud[3].isdigit() and cloud[3] not in ("/", "-"):
        # Bad "O": FEWO03 -> FEW003
        if cloud[3] == "O":
            cloud = f"{cloud[:3]}0{cloud[4:]}"
        # Move modifiers to end: BKNC015 -> BKN015C
        elif cloud[3] != "U" and cloud[:4] not in {"BASE", "UNKN"}:
            cloud = cloud[:3] + cloud[4:] + cloud[3]
    return cloud


def _null_or_int(val: str | None) -> int | None:
    """Nullify unknown elements and convert ints."""
    return None if not isinstance(val, str) or is_unknown(val) else int(val)


_TOP_OFFSETS = ("-TOPS", "-TOP")


def make_cloud(cloud: str) -> Cloud:
    """Return a Cloud dataclass for a cloud string.

    This function assumes the input is potentially valid.
    """
    raw_cloud = cloud
    cloud_type = ""
    base: str | None = None
    top: str | None = None
    cloud = sanitize_cloud(cloud).replace("/", "")
    # Separate top
    for target in _TOP_OFFSETS:
        topi = cloud.find(target)
        if topi > -1:
            top, cloud = cloud[topi + len(target) :], cloud[:topi]
            break
    # Separate type
    ## BASE027
    if cloud.startswith("BASES"):
        cloud = cloud[5:]
    elif cloud.startswith("BASE"):
        cloud = cloud[4:]
    ## VV003
    elif cloud.startswith("VV"):
        cloud_type, cloud = cloud[:2], cloud[2:]
    ## FEW010
    elif len(cloud) >= 3 and cloud[:3] in CLOUD_LIST:
        cloud_type, cloud = cloud[:3], cloud[3:]
    ## BKN-OVC065
    if len(cloud) > 4 and cloud[0] == "-" and cloud[1:4] in CLOUD_LIST:
        cloud_type += cloud[:4]
        cloud = cloud[4:]
    # Separate base
    if len(cloud) >= 3 and cloud[:3].isdigit():
        base, cloud = cloud[:3], cloud[3:]
    elif len(cloud) >= 4 and cloud[:4] == "UNKN":
        cloud = cloud[4:]
    # Remainder is considered modifiers
    modifier = cloud or None
    # Make Cloud
    return Cloud(raw_cloud, cloud_type or None, _null_or_int(base), _null_or_int(top), modifier)


def get_clouds(data: list[str]) -> tuple[list[str], list]:
    """Return the report list and removed list of split cloud layers."""
    clouds = []
    for i, item in reversed(list(enumerate(data))):
        if item[:3] in CLOUD_LIST or item[:2] == "VV":
            cloud = data.pop(i)
            clouds.append(make_cloud(cloud))
    # Attempt cloud sort. Fails if None values are present
    try:
        clouds.sort(key=lambda cloud: (cloud.base, cloud.type))
    except TypeError:
        clouds.reverse()  # Restores original report order
    return data, clouds


def get_flight_rules(visibility: Number | None, ceiling: Cloud | None) -> int:
    """Return int based on current flight rules from parsed METAR data.

    0=VFR, 1=MVFR, 2=IFR, 3=LIFR

    Note: Common practice is to report no higher than IFR if visibility unavailable.
    """
    # Parse visibility
    vis: _Numeric
    if visibility is None:
        vis = 2
    elif visibility.repr == "CAVOK" or visibility.repr.startswith("P6"):
        vis = 10
    elif visibility.repr.startswith("M"):
        vis = 0
    elif visibility.value is None:
        vis = 2
    # Convert meters to miles
    elif len(visibility.repr) == 4:
        vis = (visibility.value or 0) * 0.000621371
    else:
        vis = visibility.value or 0
    # Parse ceiling
    cld = (ceiling.base if ceiling else 99) or 99
    # Determine flight rules
    if (vis <= 5) or (cld <= 30):
        if (vis < 3) or (cld < 10):
            if (vis < 1) or (cld < 5):
                return 3  # LIFR
            return 2  # IFR
        return 1  # MVFR
    return 0  # VFR


def get_ceiling(clouds: list[Cloud]) -> Cloud | None:
    """Return ceiling layer from Cloud-List or None if none found.

    Assumes that the clouds are already sorted lowest to highest.

    Only 'Broken', 'Overcast', and 'Vertical Visibility' are considered ceilings.

    Prevents errors due to lack of cloud information (eg. '' or 'FEW///')
    """
    return next((c for c in clouds if c.base and c.type in {"OVC", "BKN", "VV"}), None)


def is_altitude(value: str) -> bool:
    """Return True if the value is a possible altitude."""
    if len(value) < 5:
        return False
    if value.startswith("SFC/"):
        return True
    if value.startswith("FL") and value[2:5].isdigit():
        return True
    first, *_ = value.split("/")
    return bool(first[-2:] == "FT" and first[-5:-2].isdigit())


def make_altitude(
    value: str,
    units: Units,
    repr: str | None = None,  # noqa: A002
    *,
    force_fl: bool = False,
) -> tuple[Number | None, Units]:
    """Convert altitude string into a number."""
    if not value:
        return None, units
    raw = repr or value
    for end in ("FT", "M"):
        if value.endswith(end):
            force_fl = False
            units.altitude = end.lower()
            value = value.removesuffix(end)
    # F430
    if value[0] == "F" and value[1:].isdigit():
        value = f"FL{value[1:]}"
    if force_fl and value[:2] != "FL":
        value = f"FL{value}"
    return make_number(value, repr=raw), units


def parse_date(
    date: str,
    hour_threshold: int = 200,
    *,
    time_only: bool = False,
    target: dt.date | None = None,
) -> dt.datetime | None:
    """Parse a report timestamp in ddhhZ or ddhhmmZ format.

    If time_only, assumes hhmm format with current or previous day.

    This function assumes the given timestamp is within the hour threshold from current date.
    """
    # Format date string
    date = date.strip("Z")
    if not date.isdigit():
        return None
    if time_only:
        if len(date) != 4:
            return None
        index_hour = 0
    else:
        if len(date) == 4:
            date += "00"
        if len(date) != 6:
            return None
        index_hour = 2
    # Create initial guess
    if target:
        target = dt.datetime(target.year, target.month, target.day, tzinfo=dt.timezone.utc)
    else:
        target = dt.datetime.now(tz=dt.timezone.utc)
    day = target.day if time_only else int(date[:2])
    hour = int(date[index_hour : index_hour + 2])
    # Handle situation where next month has less days than current month
    # Shifted value makes sure that a month shift doesn't happen twice
    shifted = False
    if day > monthrange(target.year, target.month)[1]:
        target += relativedelta(months=-1)
        shifted = True
    try:
        guess = target.replace(
            day=day,
            hour=hour % 24,
            minute=int(date[index_hour + 2 : index_hour + 4]) % 60,
            second=0,
            microsecond=0,
        )
    except ValueError:
        return None
    # Handle overflow hour
    if hour > 23:
        guess += dt.timedelta(days=1)
    # Handle changing months if not already shifted
    if not shifted:
        hourdiff = (guess - target) / dt.timedelta(minutes=1) / 60
        if hourdiff > hour_threshold:
            guess += relativedelta(months=-1)
        elif hourdiff < -hour_threshold:
            guess += relativedelta(months=+1)
    return guess


def make_timestamp(
    timestamp: str | None,
    *,
    time_only: bool = False,
    target_date: dt.date | None = None,
) -> Timestamp | None:
    """Return a Timestamp dataclass for a report timestamp in ddhhZ or ddhhmmZ format."""
    if not timestamp:
        return None
    date_obj = parse_date(timestamp, time_only=time_only, target=target_date)
    return Timestamp(timestamp, date_obj)


def is_runway_visibility(item: str) -> bool:
    """Return True if the item is a runway visibility range string."""
    return (
        len(item) > 4
        and item[0] == "R"
        and (item[3] == "/" or item[4] == "/")
        and item[1:3].isdigit()
        and "CLRD" not in item  # R28/CLRD70 Runway State
    )
