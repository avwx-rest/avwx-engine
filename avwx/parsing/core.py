"""Core parsing and utility functions."""

from __future__ import annotations

import datetime as dt
import math
import re
from calendar import monthrange
from contextlib import suppress
from copy import copy
from typing import TYPE_CHECKING, Any

from dateutil.relativedelta import relativedelta

from avwx.static.core import (
    CARDINALS,
    CLOUD_LIST,
    FRACTIONS,
    NUMBER_REPL,
    SPECIAL_NUMBERS,
    WIND_UNITS,
)
from avwx.structs import Cloud, Timestamp
from avwx.units import Measurement

if TYPE_CHECKING:
    from collections.abc import Iterable


# ---------------------------------------------------------------------------
# General utilities
# ---------------------------------------------------------------------------


def dedupe(items: Iterable[Any], *, only_neighbors: bool = False) -> list[Any]:
    """Deduplicate a list while keeping order.

    If *only_neighbors* is True only neighbouring duplicates are removed.
    """
    ret: list[Any] = []
    for item in items:
        if (only_neighbors and ret and ret[-1] != item) or item not in ret:
            ret.append(item)
    return ret


def is_unknown(value: str) -> bool:
    """Return True if *value* represents an unknown / missing value."""
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
    """Remove and return consecutive digit-only items starting at *from_index*."""
    ret = []
    data.pop(from_index)
    while len(data) > from_index and data[from_index].isdigit():
        ret.append(data.pop(from_index))
    return data, ret


# ---------------------------------------------------------------------------
# Spoken-number helpers  (kept for speech / translation layers)
# ---------------------------------------------------------------------------


def unpack_fraction(num: str) -> str:
    """Return an unpacked fraction string: ``5/2`` → ``2 1/2``."""
    numbers = [int(n) for n in num.split("/") if n]
    if len(numbers) != 2 or numbers[0] <= numbers[1]:
        return num
    numerator, denominator = numbers
    over = numerator // denominator
    rem = numerator % denominator
    return f"{over} {rem}/{denominator}"


def remove_leading_zeros(num: str) -> str:
    """Strip leading zeros, handling ``-``, ``M``, and empty strings."""
    if not num:
        return num
    if num.startswith("M"):
        ret = "M" + num[1:].lstrip("0")
    elif num.startswith("-"):
        ret = "-" + num[1:].lstrip("0")
    else:
        ret = num.lstrip("0")
    return "0" if ret in ("", "M", "-") else ret


_SPOKEN_POSTFIX = (
    (" zero zero zero", " thousand"),
    (" zero zero", " hundred"),
)


def spoken_number(num: str, *, literal: bool = False) -> str:
    """Return the spoken representation of a number string.

    Examples::

        spoken_number("1.2")   -> "one point two"
        spoken_number("25000") -> "two five thousand"
    """
    ret = []
    for part in num.split():
        if part in FRACTIONS:
            ret.append(FRACTIONS[part])
        else:
            val = " ".join(NUMBER_REPL[char] for char in part if char in NUMBER_REPL)
            if not literal:
                for target, replacement in _SPOKEN_POSTFIX:
                    if val.endswith(target):
                        val = val[: -len(target)] + replacement
            ret.append(val)
    return " and ".join(ret)


def spoken_measurement(m: Measurement, *, literal: bool = False) -> str:
    """Return the spoken representation of a Measurement's magnitude."""
    mag = m.magnitude
    if mag == int(mag):
        return spoken_number(str(int(mag)), literal=literal)
    return spoken_number(str(mag), literal=literal)


# ---------------------------------------------------------------------------
# Token helpers used across parsers
# ---------------------------------------------------------------------------


def find_first_in_list(txt: str, str_list: list[str]) -> int:
    """Return the index of the earliest occurrence of any item from *str_list* in *txt*.

    Returns -1 if nothing found.
    """
    start = len(txt) + 1
    for item in str_list:
        if start > txt.find(item) > -1:
            start = txt.find(item)
    return start if len(txt) + 1 > start > -1 else -1


def is_timestamp(item: str) -> bool:
    return len(item) == 7 and item[-1] == "Z" and item[:-1].isdigit()


def is_timerange(item: str) -> bool:
    return len(item) == 9 and item[4] == "/" and item[:4].isdigit() and item[5:].isdigit()


def is_possible_temp(temp: str) -> bool:
    return all((char.isdigit() or char == "M") for char in temp)


# ---------------------------------------------------------------------------
# Measurement construction
# ---------------------------------------------------------------------------


def _preprocess_num(num: str) -> tuple[str, str, str]:
    """Return (val_str, repr_override, speak_prefix) after stripping prefixes."""
    val_str = num
    repr_override = ""
    speak_prefix = ""

    # Remove unit suffixes
    if val_str.endswith("SM"):
        repr_override = val_str
        val_str = val_str[:-2]

    # Cleanup
    num_clean = num.rstrip("M.").replace("O", "0").replace("+", "").replace(",", "")

    # Handle "M" for minus
    if "M" in num_clean and not num_clean.startswith("-"):
        val_str = num_clean.replace("MM", "-").replace("M", "-")
        while val_str and val_str[0] != "-":
            val_str = val_str[1:]

    if val_str.startswith("ABV "):
        speak_prefix += "above "
        val_str = val_str[4:]
    if val_str.startswith("BLW "):
        speak_prefix += "below "
        val_str = val_str[4:]
    if val_str.startswith("FL"):
        speak_prefix += "flight level "
        val_str = val_str[2:]
    if val_str.startswith("M"):
        speak_prefix += "less than "
        repr_override = repr_override or val_str
        val_str = val_str[1:]
    if val_str.startswith("P"):
        speak_prefix += "greater than "
        repr_override = repr_override or val_str
        val_str = val_str[1:]

    return val_str, repr_override, speak_prefix


def make_measurement(
    num: str | None,
    unit: str,
    repr_override: str | None = None,  # noqa: A002
) -> tuple[Measurement | None, str | None]:
    """Parse *num* into a ``(Measurement, repr_str)`` pair.

    Returns ``(None, None)`` for unknown or empty input.
    The *repr_str* is the raw token suitable for storing in a ``*Repr`` model.
    """
    if not num or is_unknown(num):
        return None, None

    raw_repr = repr_override or num

    # Cardinal direction
    if num in CARDINALS:
        raw_repr = raw_repr or num
        num = str(CARDINALS[num])

    val_str = num.rstrip("M.").replace("O", "0").replace("+", "").replace(",", "")

    # Handle M-prefix minus sign
    if "M" in val_str and not val_str.startswith("-"):
        val_str = val_str.replace("MM", "-").replace("M", "-")
        while val_str and val_str[0] != "-":
            val_str = val_str[1:]

    # Strip special prefixes (M = less-than, P = greater-than)
    magnitude: float | None = None
    for prefix in ("M", "P"):
        if val_str.startswith(prefix):
            val_str = val_str[1:]
            break

    with suppress(KeyError):
        item = SPECIAL_NUMBERS[num]
        magnitude = item[0] if isinstance(item, tuple) else float(item)

    if magnitude is None:
        if not val_str:
            return None, None
        with suppress(ValueError):
            magnitude = float(val_str) if "." in val_str else float(int(val_str))

    if magnitude is None:
        return None, None

    return Measurement(magnitude, unit), raw_repr


# ---------------------------------------------------------------------------
# Atmospheric calculations
# ---------------------------------------------------------------------------

_Numeric = int | float


def relative_humidity(temperature: _Numeric, dewpoint: _Numeric, unit: str = "degC") -> float:
    """Return relative humidity (0–1) from temperature and dewpoint."""

    def saturation(value: _Numeric) -> float:
        return math.exp((17.67 * value) / (243.5 + value))

    if unit in ("degF", "F"):
        dewpoint = (dewpoint - 32) * 5 / 9
        temperature = (temperature - 32) * 5 / 9
    return saturation(dewpoint) / saturation(temperature)


def pressure_altitude(pressure: Measurement, altitude: _Numeric) -> Measurement:
    """Return pressure altitude as a :class:`~avwx.units.Measurement` in feet."""
    p_inhg = float(pressure.to("inHg").magnitude)
    result = round((29.92 - p_inhg) * 1000 + altitude)
    return Measurement(result, "ft")


def density_altitude(
    pressure: Measurement,
    temperature: Measurement,
    altitude: _Numeric,
) -> Measurement:
    """Return density altitude as a :class:`~avwx.units.Measurement` in feet."""
    temp_c = float(temperature.to("degC").magnitude)
    pressure_alt = pressure_altitude(pressure, altitude)
    standard = 15 - (2 * altitude / 1000)
    result = round(((temp_c - standard) * 120) + pressure_alt.magnitude)
    return Measurement(result, "ft")


# ---------------------------------------------------------------------------
# Station / time extraction
# ---------------------------------------------------------------------------


def get_station_and_time(
    data: list[str],
) -> tuple[list[str], str | None, str | None]:
    """Return ``(remaining_tokens, station, time_str)``."""
    if not data:
        return data, None, None
    station = data.pop(0)
    if not data:
        return data, station, None
    q_time = data[0]
    r_time: str | None = None
    if q_time.endswith("Z") and q_time[:-1].isdigit():
        r_time = data.pop(0)
    elif len(q_time) == 6 and q_time.isdigit():
        r_time = f"{data.pop(0)}Z"
    return data, station, r_time


# ---------------------------------------------------------------------------
# Wind
# ---------------------------------------------------------------------------


def is_wind(text: str) -> bool:
    if text.startswith("WS"):
        return False
    if len(text) > 4:
        for ending in WIND_UNITS:
            unit_index = text.find(ending)
            if text.endswith(ending) and text[unit_index - 2 : unit_index].isdigit():
                return True
    if len(text) != 5 and (len(text) < 8 or "G" not in text or "/" in text):
        return False
    return text[:5].isdigit() or (text.startswith("VRB") and text[3:5].isdigit())


VARIABLE_DIRECTION_PATTERN = re.compile(r"\d{3}V\d{3}")


def is_variable_wind_direction(text: str) -> bool:
    if len(text) < 7:
        return False
    return VARIABLE_DIRECTION_PATTERN.match(text[:7]) is not None


def separate_wind(text: str) -> tuple[str, str, str]:
    direction, speed, gust = "", "", ""
    if "G" in text:
        g_index = text.find("G")
        start, end = g_index + 1, g_index + 3
        if "GP" in text:
            end += 1
        gust = text[start:end]
        text = text[:g_index] + text[end:]
    if text:
        if len(text) == 2:
            speed = text
        else:
            direction = text[:3]
            speed = text[3:]
    return direction, speed, gust


def get_wind(
    data: list[str],
) -> tuple[
    list[str],
    Measurement | None,  # direction (degrees)
    Measurement | None,  # speed
    Measurement | None,  # gust
    list[Measurement],   # variable directions
    str,                 # wind unit string (for repr / speech)
    str | None,          # raw wind token
    str | None,          # raw variable-direction token
]:
    """Extract wind elements and return typed Measurements plus raw tokens."""
    direction_str, speed_str, gust_str = "", "", ""
    wind_unit = "kt"
    raw_wind: str | None = None
    raw_vardir: str | None = None
    variable: list[Measurement] = []

    if data:
        item = copy(data[0])
        if is_wind(item):
            raw_wind = item
            for key, unit in WIND_UNITS.items():
                if item.endswith(key):
                    wind_unit = unit
                    item = item.replace(key, "")
                    break
            direction_str, speed_str, gust_str = separate_wind(item)
            data.pop(0)

    # Separated gust token
    if data and 1 < len(data[0]) < 4 and data[0][0] == "G" and data[0][1:].isdigit():
        gust_str = data.pop(0)[1:]

    # Variable wind direction
    if data and is_variable_wind_direction(data[0]):
        raw_vardir = data[0]
        for part in data.pop(0).split("V"):
            m, _ = make_measurement(part, "degree")
            if m is not None:
                variable.append(m)

    direction: Measurement | None = None
    if direction_str and direction_str != "VRB" and direction_str != "000":
        direction, _ = make_measurement(direction_str, "degree")
    elif direction_str in ("VRB", "000"):
        # Keep None for direction; special values handled by speech/translate
        pass

    speed: Measurement | None = None
    if speed_str:
        raw_speed = speed_str.strip("BV")
        speed, _ = make_measurement(raw_speed, wind_unit)

    gust: Measurement | None = None
    if gust_str:
        gust, _ = make_measurement(gust_str, wind_unit)

    return data, direction, speed, gust, variable, wind_unit, raw_wind, raw_vardir


def wind_dir_repr(raw_wind: str | None) -> str | None:
    """Extract the 3-character direction repr from a raw wind token.

    Returns "VRB", "000", or the numeric direction string.
    """
    if not raw_wind:
        return None
    for key in WIND_UNITS:
        clean = raw_wind.replace(key, "")
        if clean:
            return clean[:3]
    return None


# ---------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------


def get_visibility(
    data: list[str],
) -> tuple[list[str], Measurement | None, str | None, str]:
    """Extract visibility element and return ``(data, measurement, raw_repr, unit)``."""
    visibility: Measurement | None = None
    raw: str | None = None
    unit = "sm"

    if not data:
        return data, None, None, unit

    item = copy(data[0])

    if item.endswith("SM"):
        raw = item
        unit = "sm"
        if item[:-2].isdigit():
            vis_val = float(int(item[:-2]))
        elif "/" in item:
            frac = item[: item.find("SM")]
            parts = frac.split("/")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                vis_val = int(parts[0]) / int(parts[1])
            else:
                vis_val = float(frac.replace("/", "."))
        else:
            try:
                vis_val = float(item[:-2])
            except ValueError:
                return data, None, None, unit
        data.pop(0)
        visibility = Measurement(vis_val, unit)

    elif len(item) == 4 and item.isdigit():
        raw = item
        unit = "m"
        data.pop(0)
        visibility = Measurement(int(item), unit)

    elif 7 >= len(item) >= 5 and item[:4].isdigit() and (
        item[4] in {"M", "N", "S", "E", "W"} or item[4:] == "NDV"
    ):
        raw = item
        unit = "m"
        data.pop(0)
        visibility = Measurement(int(item[:4]), unit)

    elif len(item) == 5 and item[1:].isdigit() and item[0] in {"M", "P", "B"}:
        raw = item
        unit = "m"
        data.pop(0)
        visibility = Measurement(int(item[1:]), unit)

    elif item.endswith("KM"):
        raw = item
        unit = "m"
        data.pop(0)
        visibility = Measurement(int(item[:-2]) * 1000, unit)

    elif len(data) > 1 and data[1].endswith("SM") and "/" in data[1] and item.isdigit():
        # Split fraction: "2" "1/2SM" → 5/2 sm
        raw = f"{item} {data[1]}"
        unit = "sm"
        vis1 = int(data.pop(0))
        vis2 = data.pop(0).replace("SM", "")
        num, den = int(vis2[0]), int(vis2[2])
        vis_val = vis1 + num / den
        visibility = Measurement(vis_val, unit)

    # Special CAVOK: no visibility parsed, handled at caller
    return data, visibility, raw, unit


# ---------------------------------------------------------------------------
# Cloud parsing
# ---------------------------------------------------------------------------


def _null_or_int(val: str | None) -> int | None:
    return None if not isinstance(val, str) or is_unknown(val) else int(val)


def sanitize_cloud(cloud: str) -> str:
    if len(cloud) < 4:
        return cloud
    if not cloud[3].isdigit() and cloud[3] not in ("/", "-"):
        if cloud[3] == "O":
            cloud = f"{cloud[:3]}0{cloud[4:]}"
        elif cloud[3] != "U" and cloud[:4] not in {"BASE", "UNKN"}:
            cloud = cloud[:3] + cloud[4:] + cloud[3]
    return cloud


_TOP_OFFSETS = ("-TOPS", "-TOP")


def make_cloud(cloud: str) -> tuple[Cloud, str]:
    """Return ``(Cloud, raw_repr)`` for a cloud token."""
    raw_cloud = cloud
    cloud_type = ""
    base_str: str | None = None
    top_str: str | None = None

    cloud = sanitize_cloud(cloud).replace("/", "")

    for target in _TOP_OFFSETS:
        topi = cloud.find(target)
        if topi > -1:
            top_str, cloud = cloud[topi + len(target) :], cloud[:topi]
            break

    if cloud.startswith("BASES"):
        cloud = cloud[5:]
    elif cloud.startswith("BASE"):
        cloud = cloud[4:]
    elif cloud.startswith("VV"):
        cloud_type, cloud = cloud[:2], cloud[2:]
    elif len(cloud) >= 3 and cloud[:3] in CLOUD_LIST:
        cloud_type, cloud = cloud[:3], cloud[3:]

    if len(cloud) > 4 and cloud[0] == "-" and cloud[1:4] in CLOUD_LIST:
        cloud_type += cloud[:4]
        cloud = cloud[4:]

    if len(cloud) >= 3 and cloud[:3].isdigit():
        base_str, cloud = cloud[:3], cloud[3:]
    elif len(cloud) >= 4 and cloud[:4] == "UNKN":
        cloud = cloud[4:]

    modifier = cloud or None

    base_int = _null_or_int(base_str)
    top_int = _null_or_int(top_str)

    base = Measurement(base_int * 100, "ft") if base_int is not None else None
    top = Measurement(top_int * 100, "ft") if top_int is not None else None

    return (
        Cloud(type=cloud_type or None, base=base, top=top, modifier=modifier),
        raw_cloud,
    )


def get_clouds(data: list[str]) -> tuple[list[str], list[Cloud], list[str]]:
    """Return ``(remaining_data, clouds, raw_cloud_tokens)``."""
    clouds: list[Cloud] = []
    raws: list[str] = []
    for i, item in reversed(list(enumerate(data))):
        if item[:3] in CLOUD_LIST or item[:2] == "VV":
            cloud_token = data.pop(i)
            cloud, raw = make_cloud(cloud_token)
            clouds.append(cloud)
            raws.append(raw)
    try:
        paired = sorted(zip(clouds, raws), key=lambda p: (p[0].base.magnitude if p[0].base else 0, p[0].type))
        clouds, raws = [p[0] for p in paired], [p[1] for p in paired]
    except (TypeError, AttributeError):
        clouds.reverse()
        raws.reverse()
    return data, clouds, raws


# ---------------------------------------------------------------------------
# Flight rules
# ---------------------------------------------------------------------------


def get_flight_rules(
    visibility: Measurement | None,
    vis_repr: str | None,
    ceiling: Cloud | None,
) -> int:
    """Return flight rules index: 0=VFR, 1=MVFR, 2=IFR, 3=LIFR."""
    vis: float
    if visibility is None:
        vis = 2.0
    elif vis_repr in {"CAVOK"} or (vis_repr or "").startswith("P6"):
        vis = 10.0
    elif (vis_repr or "").startswith("M"):
        vis = 0.0
    else:
        mag = visibility.magnitude
        # Normalise to statute miles for the threshold comparison
        try:
            vis = float(visibility.to("sm").magnitude)
        except Exception:  # noqa: BLE001
            vis = mag * 0.000621371 if "m" in visibility.unit and "sm" not in visibility.unit else mag

    cld = 99.0
    if ceiling and ceiling.base:
        cld = ceiling.base.magnitude / 100.0  # convert ft back to hundreds for thresholds

    if (vis <= 5) or (cld <= 30):
        if (vis < 3) or (cld < 10):
            if (vis < 1) or (cld < 5):
                return 3  # LIFR
            return 2  # IFR
        return 1  # MVFR
    return 0  # VFR


def get_ceiling(clouds: list[Cloud]) -> Cloud | None:
    """Return the ceiling layer or None.

    Only BKN, OVC, and VV layers qualify as ceilings.
    """
    return next((c for c in clouds if c.base and c.type in {"OVC", "BKN", "VV"}), None)


# ---------------------------------------------------------------------------
# Altitude
# ---------------------------------------------------------------------------


def is_altitude(value: str) -> bool:
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
    unit: str = "ft",
    repr_override: str | None = None,  # noqa: A002
    *,
    force_fl: bool = False,
) -> tuple[Measurement | None, str]:
    """Parse an altitude string into a ``(Measurement, unit)`` pair."""
    if not value:
        return None, unit
    for end in ("FT", "M"):
        if value.endswith(end):
            force_fl = False
            unit = end.lower()
            value = value.removesuffix(end)
    if value and value[0] == "F" and value[1:].isdigit():
        value = f"FL{value[1:]}"
    if force_fl and not value.startswith("FL"):
        value = f"FL{value}"
    m, _ = make_measurement(value, unit, repr_override)
    return m, unit


# ---------------------------------------------------------------------------
# Date / time parsing
# ---------------------------------------------------------------------------


def parse_date(
    date: str,
    hour_threshold: int = 200,
    *,
    time_only: bool = False,
    target: dt.date | None = None,
) -> dt.datetime | None:
    """Parse a report timestamp in ddhhZ or ddhhmmZ format."""
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

    if target:
        target_dt = dt.datetime(target.year, target.month, target.day, tzinfo=dt.timezone.utc)
    else:
        target_dt = dt.datetime.now(tz=dt.timezone.utc)

    day = target_dt.day if time_only else int(date[:2])
    hour = int(date[index_hour : index_hour + 2])

    shifted = False
    if day > monthrange(target_dt.year, target_dt.month)[1]:
        target_dt += relativedelta(months=-1)
        shifted = True

    try:
        guess = target_dt.replace(
            day=day,
            hour=hour % 24,
            minute=int(date[index_hour + 2 : index_hour + 4]) % 60,
            second=0,
            microsecond=0,
        )
    except ValueError:
        return None

    if hour > 23:
        guess += dt.timedelta(days=1)

    if not shifted:
        hourdiff = (guess - target_dt) / dt.timedelta(minutes=1) / 60
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
    """Return a :class:`~avwx.structs.Timestamp` from a ddhhZ / ddhhmmZ string."""
    if not timestamp:
        return None
    date_obj = parse_date(timestamp, time_only=time_only, target=target_date)
    return Timestamp(repr=timestamp, dt=date_obj)


# ---------------------------------------------------------------------------
# Runway visibility detection
# ---------------------------------------------------------------------------


def is_runway_visibility(item: str) -> bool:
    return (
        len(item) > 4
        and item[0] == "R"
        and (item[3] == "/" or item[4] == "/")
        and item[1:3].isdigit()
        and "CLRD" not in item
    )
