"""
Contains the core parsing and indent functions of avwx
"""

# pylint: disable=redefined-builtin

# stdlib
import datetime as dt
from calendar import monthrange
from copy import copy
from typing import List, Tuple

# library
from dateutil.relativedelta import relativedelta

# module
from avwx.static.core import (
    CARDINALS,
    CLOUD_LIST,
    FRACTIONS,
    NUMBER_REPL,
    SPECIAL_NUMBERS,
)
from avwx.structs import Cloud, Fraction, Number, Timestamp, Units


def dedupe(items: list, only_neighbors: bool = False) -> list:
    """
    Deduplicate a list while keeping order
    
    If only_neighbors is True, dedupe will only check neighboring values
    """
    ret = []
    for item in items:
        if (only_neighbors and ret and ret[-1] != item) or item not in ret:
            ret.append(item)
    return ret


def is_unknown(val: str) -> bool:
    """
    Returns True if val represents and unknown value
    """
    if not isinstance(val, str):
        raise TypeError
    if not val or val.upper() in ("UNKN",):
        return True
    for char in val:
        if char not in ("/", "X", "."):
            break
    else:
        return True
    return False


def get_digit_list(alist: List[str], from_index: int) -> Tuple[List[str], List[str]]:
    """
    Returns a list of items removed from a given list of strings
    that are all digits from 'from_index' until hitting a non-digit item
    """
    ret = []
    alist.pop(from_index)
    while len(alist) > from_index and alist[from_index].isdigit():
        ret.append(alist.pop(from_index))
    return alist, ret


def unpack_fraction(num: str) -> str:
    """
    Returns unpacked fraction string 5/2 -> 2 1/2
    """
    nums = [int(n) for n in num.split("/") if n]
    if len(nums) == 2 and nums[0] > nums[1]:
        over = nums[0] // nums[1]
        rem = nums[0] % nums[1]
        return f"{over} {rem}/{nums[1]}"
    return num


def remove_leading_zeros(num: str) -> str:
    """
    Strips zeros while handling -, M, and empty strings
    """
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


def spoken_number(num: str, literal: bool = False) -> str:
    """
    Returns the spoken version of a number

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


def make_number(
    num: str,
    repr: str = None,
    speak: str = None,
    literal: bool = False,
    special: dict = None,
) -> Number:
    """
    Returns a Number or Fraction dataclass for a number string

    If literal, spoken string will not convert to hundreds/thousands

    NOTE: Numerators are assumed to have a single digit. Additional are whole numbers
    """
    if not num or is_unknown(num):
        return None
    # Check special
    if special is not None and num in special:
        return Number(repr or num, *special[num])
    if num in SPECIAL_NUMBERS:
        return Number(repr or num, *SPECIAL_NUMBERS[num])
    # Check cardinal direction
    if num in CARDINALS:
        if not repr:
            repr = num
        num = str(CARDINALS[num])
    # Remove spurious characters from the end
    num = num.rstrip("M.")
    num = num.replace("O", "0")
    num = num.replace("+", "")
    # Create Fraction
    if "/" in num:
        nmr, dnm = num.split("/")
        dnm = int(dnm)
        # Multiply multi-digit numerator
        if len(nmr) > 1:
            nmr = int(nmr[:-1]) * dnm + int(nmr[-1])
            num = f"{nmr}/{dnm}"
        else:
            nmr = int(nmr)
        unpacked = unpack_fraction(num)
        spoken = spoken_number(unpacked, literal)
        return Fraction(repr or num, nmr / dnm, spoken, nmr, dnm, unpacked)
    # Handle Minus values with errors like 0M04
    if "M" in num:
        val = num.replace("M", "-")
        while val[0] != "-":
            val = val[1:]
    else:
        val = num
    # Create Number
    if not val:
        return None
    if "." in num:
        val = float(val)
        # Overwrite float 0 due to "0.0" literal
        if not val:
            val = 0
    else:
        val = int(val)
    return Number(repr or num, val, spoken_number(speak or str(val), literal))


def find_first_in_list(txt: str, str_list: List[str]) -> int:
    """
    Returns the index of the earliest occurrence of an item from a list in a string

    Ex: find_first_in_list('foobar', ['bar', 'fin']) -> 3
    """
    start = len(txt) + 1
    for item in str_list:
        if start > txt.find(item) > -1:
            start = txt.find(item)
    return start if len(txt) + 1 > start > -1 else -1


def is_timestamp(item: str) -> bool:
    """
    Returns True if the item matches the timestamp format
    """
    return len(item) == 7 and item[-1] == "Z" and item[:-1].isdigit()


def is_timerange(item: str) -> bool:
    """
    Returns True if the item is a TAF to-from time range
    """
    return (
        len(item) == 9 and item[4] == "/" and item[:4].isdigit() and item[5:].isdigit()
    )


def is_possible_temp(temp: str) -> bool:
    """
    Returns True if all characters are digits or 'M' (for minus)
    """
    for char in temp:
        if not (char.isdigit() or char == "M"):
            return False
    return True


def get_station_and_time(data: List[str]) -> Tuple[List[str], str, str]:
    """
    Returns the report list and removed station ident and time strings
    """
    if not data:
        return data, None, None
    station = data.pop(0)
    if not data:
        return data, station, None
    qtime, rtime = data[0], None
    if data and qtime.endswith("Z") and qtime[:-1].isdigit():
        rtime = data.pop(0)
    elif data and len(qtime) == 6 and qtime.isdigit():
        rtime = data.pop(0) + "Z"
    return data, station, rtime


def get_wind(
    data: List[str], units: Units
) -> Tuple[List[str], Number, Number, Number, List[Number]]:
    """
    Returns the report list and removed:
    Direction string, speed string, gust string, variable direction list
    """
    direction, speed, gust = "", "", ""
    variable = []
    if data:
        item = copy(data[0])
        for rep in ["(E)"]:
            item = item.replace(rep, "")
        for replacements in (("O", "0"), ("/", ""), ("LKT", "KT"), ("GG", "G")):
            item = item.replace(*replacements)
        # 09010KT, 09010G15KT
        if (
            item.endswith("KT")
            or item.endswith("KTS")
            or item.endswith("MPS")
            or item.endswith("KMH")
            or (
                (
                    len(item) == 5
                    or (len(item) >= 8 and item.find("G") != -1)
                    and item.find("/") == -1
                )
                and (
                    item[:5].isdigit()
                    or (item.startswith("VRB") and item[3:5].isdigit())
                )
            )
        ):
            # In order of frequency
            if item.endswith("KT"):
                item = item.replace("KT", "")
            elif item.endswith("KTS"):
                item = item.replace("KTS", "")
            elif item.endswith("MPS"):
                units.wind_speed = "m/s"
                item = item.replace("MPS", "")
            elif item.endswith("KMH"):
                units.wind_speed = "km/h"
                item = item.replace("KMH", "")
            direction = item[:3]
            if "G" in item:
                g_index = item.find("G")
                gust = item[g_index + 1 :]
                speed = item[3:g_index]
            else:
                speed = item[3:]
            direction = item[:3]
            data.pop(0)
    # Separated Gust
    if data and 1 < len(data[0]) < 4 and data[0][0] == "G" and data[0][1:].isdigit():
        gust = data.pop(0)[1:]
    # Variable Wind Direction
    if (
        data
        and len(data[0]) == 7
        and data[0][:3].isdigit()
        and data[0][3] == "V"
        and data[0][4:].isdigit()
    ):
        variable = [
            make_number(i, speak=i, literal=True) for i in data.pop(0).split("V")
        ]
    # Convert to Number
    direction = make_number(direction, speak=direction, literal=True)
    speed = make_number(speed.strip("BV"))
    gust = make_number(gust)
    return data, direction, speed, gust, variable


def get_visibility(data: List[str], units: Units) -> Tuple[List[str], Number]:
    """
    Returns the report list and removed visibility string
    """
    visibility = ""
    if data:
        item = copy(data[0])
        # Vis reported in statue miles
        if item.endswith("SM"):  # 10SM
            if item in ("P6SM", "M1/4SM", "M1/8SM"):
                visibility = item[:-2]
            elif item[:-2].isdigit():
                visibility = str(int(item[:-2]))
            elif "/" in item:
                visibility = item[: item.find("SM")]  # 1/2SM
            data.pop(0)
            units.visibility = "sm"
        # Vis reported in meters
        elif len(item) == 4 and item.isdigit():
            visibility = data.pop(0)
            units.visibility = "m"
        elif (
            7 >= len(item) >= 5
            and item[:4].isdigit()
            and (item[4] in ["M", "N", "S", "E", "W"] or item[4:] == "NDV")
        ):
            visibility = data.pop(0)[:4]
            units.visibility = "m"
        elif len(item) == 5 and item[1:].isdigit() and item[0] in ["M", "P", "B"]:
            visibility = data.pop(0)[1:]
            units.visibility = "m"
        elif item.endswith("KM") and item[:-2].isdigit():
            visibility = item[:-2] + "000"
            data.pop(0)
            units.visibility = "m"
        # Vis statute miles but split Ex: 2 1/2SM
        elif (
            len(data) > 1
            and data[1].endswith("SM")
            and "/" in data[1]
            and item.isdigit()
        ):
            vis1 = data.pop(0)  # 2
            vis2 = data.pop(0).replace("SM", "")  # 1/2
            visibility = str(int(vis1) * int(vis2[2]) + int(vis2[0])) + vis2[1:]  # 5/2
            units.visibility = "sm"
    return data, make_number(visibility)


def sanitize_cloud(cloud: str) -> str:
    """
    Fix rare cloud layer issues
    """
    if len(cloud) < 4:
        return cloud
    if not cloud[3].isdigit() and cloud[3] not in ("/", "-"):
        if cloud[3] == "O":
            cloud = cloud[:3] + "0" + cloud[4:]  # Bad "O": FEWO03 -> FEW003
        elif cloud[3] != "U":  # Move modifiers to end: BKNC015 -> BKN015C
            cloud = cloud[:3] + cloud[4:] + cloud[3]
    return cloud


def make_cloud(cloud: str) -> Cloud:
    """
    Returns a Cloud dataclass for a cloud string

    This function assumes the input is potentially valid
    """
    els = {"type": None, "base": None, "top": None, "modifier": None}
    _c = sanitize_cloud(cloud).replace("/", "")
    # Separate top
    topi = _c.find("-TOP")
    if topi > -1:
        els["top"], _c = _c[topi + 4 :], _c[:topi]
    # Separate type
    ## VV003
    if _c.startswith("VV"):
        els["type"], _c = _c[:2], _c[2:]
    ## FEW010
    elif len(_c) >= 3 and _c[:3] in CLOUD_LIST:
        els["type"], _c = _c[:3], _c[3:]
    ## BKN-OVC065
    if len(_c) > 4 and _c[0] == "-" and _c[1:4] in CLOUD_LIST:
        els["type"] += _c[:4]
        _c = _c[4:]
    # Separate base
    if len(_c) >= 3 and _c[:3].isdigit():
        els["base"], _c = _c[:3], _c[3:]
    elif len(_c) >= 4 and _c[:4] == "UNKN":
        _c = _c[4:]
    # Remainder is considered modifiers
    if _c:
        els["modifier"] = _c
    # Nullify unknown elements and convert ints
    for key, val in els.items():
        if not isinstance(val, str):
            continue
        if is_unknown(val):
            els[key] = None
        elif val.isdigit():
            els[key] = int(val)
    # Make Cloud
    return Cloud(cloud, **els)


def get_clouds(data: List[str]) -> Tuple[List[str], list]:
    """
    Returns the report list and removed list of split cloud layers
    """
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


def get_flight_rules(vis: Number, ceiling: Cloud) -> int:
    """
    Returns int based on current flight rules from parsed METAR data

    0=VFR, 1=MVFR, 2=IFR, 3=LIFR

    Note: Common practice is to report IFR if visibility unavailable
    """
    # Parse visibility
    if not vis:
        return 2
    if vis.repr == "CAVOK" or vis.repr.startswith("P6"):
        vis = 10
    elif vis.repr.startswith("M"):
        vis = 0
    # Convert meters to miles
    elif len(vis.repr) == 4:
        vis = vis.value * 0.000621371
    else:
        vis = vis.value
    # Parse ceiling
    cld = ceiling.base if ceiling else 99
    # Determine flight rules
    if (vis <= 5) or (cld <= 30):
        if (vis < 3) or (cld < 10):
            if (vis < 1) or (cld < 5):
                return 3  # LIFR
            return 2  # IFR
        return 1  # MVFR
    return 0  # VFR


def get_ceiling(clouds: List[Cloud]) -> Cloud:
    """
    Returns ceiling layer from Cloud-List or None if none found

    Assumes that the clouds are already sorted lowest to highest

    Only 'Broken', 'Overcast', and 'Vertical Visibility' are considered ceilings

    Prevents errors due to lack of cloud information (eg. '' or 'FEW///')
    """
    for cloud in clouds:
        if cloud.base and cloud.type in ("OVC", "BKN", "VV"):
            return cloud
    return None


def parse_date(
    date: str,
    hour_threshold: int = 200,
    time_only: bool = False,
    target: dt.date = None,
) -> dt.datetime:
    """
    Parses a report timestamp in ddhhZ or ddhhmmZ format

    If time_only, assumes hhmm format with current or previous day

    This function assumes the given timestamp is within the hour threshold from current date
    """
    # Format date string
    date = date.strip("Z")
    if not date.isdigit():
        return None
    if time_only:
        if len(date) != 4:
            return None
        ihour = 0
    else:
        if len(date) == 4:
            date += "00"
        if len(date) != 6:
            return None
        ihour = 2
    # Create initial guess
    if target:
        target = dt.datetime(
            target.year, target.month, target.day, tzinfo=dt.timezone.utc
        )
    else:
        target = dt.datetime.now(tz=dt.timezone.utc)
    day = target.day if time_only else int(date[0:2])
    hour = int(date[ihour : ihour + 2])
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
            minute=int(date[ihour + 2 : ihour + 4]) % 60,
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
    timestamp: str, time_only: bool = False, target_date: dt.date = None
) -> Timestamp:
    """
    Returns a Timestamp dataclass for a report timestamp in ddhhZ or ddhhmmZ format
    """
    if not timestamp:
        return None
    date_obj = parse_date(timestamp, time_only=time_only, target=target_date)
    return Timestamp(timestamp, date_obj)
