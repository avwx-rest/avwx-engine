"""
Contains METAR-specific functions for report parsing
"""

# pylint: disable=invalid-overridden-method

# stdlib
from datetime import date, datetime, timedelta, timezone
from typing import List, Tuple, Optional

# module
from avwx.current.base import Report, get_wx_codes
from avwx.parsing import core, remarks, sanitization, speech, summary
from avwx.parsing.translate.metar import translate_metar
from avwx.service import NOAA
from avwx.static.core import FLIGHT_RULES, IN_UNITS, NA_UNITS
from avwx.static.metar import METAR_RMK
from avwx.station import uses_na_format, valid_station
from avwx.structs import MetarData, MetarTrans, Number, RemarksData, Units


def get_remarks(txt: str) -> Tuple[List[str], str]:
    """Returns the report split into components and the remarks string

    Remarks can include items like RMK and on, NOSIG and on, and BECMG and on
    """
    txt = txt.replace("?", "").strip()
    # First look for Altimeter in txt
    alt_index = len(txt) + 1
    for item in [" A2", " A3", " Q1", " Q0", " Q9"]:
        index = txt.find(item)
        if len(txt) - 6 > index > -1 and txt[index + 2 : index + 6].isdigit():
            alt_index = index
    # Then look for earliest remarks 'signifier'
    sig_index = core.find_first_in_list(txt, METAR_RMK)
    if sig_index == -1:
        sig_index = len(txt) + 1
    if sig_index > alt_index > -1:
        return txt[: alt_index + 6].strip().split(), txt[alt_index + 7 :]
    if alt_index > sig_index > -1:
        return txt[:sig_index].strip().split(), txt[sig_index + 1 :]
    return txt.strip().split(), ""


def get_runway_visibility(data: List[str]) -> Tuple[List[str], List[str]]:
    """Returns the report list and the remove runway visibility list"""
    runway_vis = []
    for i, item in reversed(list(enumerate(data))):
        if (
            len(item) > 4
            and item[0] == "R"
            and (item[3] == "/" or item[4] == "/")
            and item[1:3].isdigit()
        ):
            runway_vis.append(data.pop(i))
    runway_vis.sort()
    return data, runway_vis


def parse_altimeter(value: str) -> Optional[Number]:
    """Parse an altimeter string into a Number"""
    if not value or len(value) < 4:
        return None
    # QNH3003INS
    if len(value) >= 7 and value.endswith("INS"):
        return core.make_number(value[-7:-5] + "." + value[-5:-3], value, literal=True)
    number = value.replace(".", "")
    # Q1000/10
    if "/" in number:
        number = number.split("/")[0]
    if number.startswith("QNH"):
        number = "Q" + number[1:]
    if not (len(number) in (4, 5) and number[-4:].isdigit()):
        return None
    number = number.lstrip("AQ")
    if number[0] in ("2", "3"):
        number = number[:2] + "." + number[2:]
    elif number[0] not in ("0", "1"):
        return None
    return core.make_number(number, value, number, literal=True)


def get_altimeter(
    data: List[str], units: Units, version: str = "NA"
) -> Tuple[List[str], Optional[Number]]:
    """Returns the report list and the removed altimeter item

    Version is 'NA' (North American / default) or 'IN' (International)
    """
    values: List[Number] = []
    for _ in range(2):
        if not data:
            break
        value = parse_altimeter(data[-1])
        if value is None:
            break
        values.append(value)
        data.pop(-1)
    if not values:
        return data, None
    values.sort(key=lambda x: x.value or 0)
    altimeter = values[0 if version == "NA" else -1]
    if altimeter.value is not None:
        units.altimeter = "inHg" if altimeter.value < 100 else "hPa"
    return data, altimeter


def get_temp_and_dew(
    data: List[str],
) -> Tuple[List[str], Optional[Number], Optional[Number]]:
    """Returns the report list and removed temperature and dewpoint strings"""
    for i, item in reversed(list(enumerate(data))):
        if "/" in item:
            # ///07
            if item[0] == "/":
                item = "/" + item.lstrip("/")
            # 07///
            elif item[-1] == "/":
                item = item.rstrip("/") + "/"
            tempdew = item.split("/")
            if len(tempdew) != 2:
                continue
            valid = True
            for j, temp in enumerate(tempdew):
                if temp in ["MM", "XX"]:
                    tempdew[j] = ""
                elif not core.is_possible_temp(temp):
                    valid = False
                    break
            if valid:
                data.pop(i)
                temp, dew = tempdew
                return data, core.make_number(temp), core.make_number(dew)
    return data, None, None


def get_relative_humidity(
    temperature: Optional[Number],
    dewpoint: Optional[Number],
    remarks_info: Optional[RemarksData],
    units: Units,
) -> Optional[float]:
    """Calculates relative humidity from preferred temperature and dewpoint"""
    if remarks_info is not None:
        temp = remarks_info.temperature_decimal or temperature
        dew = remarks_info.dewpoint_decimal or dewpoint
    else:
        temp = temperature
        dew = dewpoint
    if temp is None or temp.value is None:
        return None
    if dew is None or dew.value is None:
        return None
    return core.relative_humidity(temp.value, dew.value, units.temperature)


def sanitize(report: str) -> Tuple[str, str, List[str]]:
    """Returns a sanitized report, remarks, and elements ready for parsing"""
    clean = sanitization.sanitize_report_string(report)
    data, remark_str = get_remarks(clean)
    data = core.dedupe(data)
    data = sanitization.sanitize_report_list(data)
    clean = " ".join(data)
    if remark_str:
        clean += " " + remark_str
    return clean, remark_str, data


def parse(
    station: str, report: str, issued: date = None
) -> Tuple[Optional[MetarData], Optional[Units]]:
    """Returns MetarData and Units dataclasses with parsed data and their associated units"""
    valid_station(station)
    if not report:
        return None, None
    parser = parse_na if uses_na_format(station[:2]) else parse_in
    return parser(report, issued)


def parse_na(report: str, issued: date = None) -> Tuple[MetarData, Units]:
    """Parser for the North American METAR variant"""
    # pylint: disable=too-many-locals
    units = Units(**NA_UNITS)
    sanitized, remarks_str, data = sanitize(report)
    data, station, time = core.get_station_and_time(data)
    data, runway_visibility = get_runway_visibility(data)
    data, clouds = core.get_clouds(data)
    (
        data,
        wind_direction,
        wind_speed,
        wind_gust,
        wind_variable_direction,
    ) = core.get_wind(data, units)
    data, altimeter = get_altimeter(data, units, "NA")
    data, visibility = core.get_visibility(data, units)
    data, temperature, dewpoint = get_temp_and_dew(data)
    condition = core.get_flight_rules(visibility, core.get_ceiling(clouds))
    other, wx_codes = get_wx_codes(data)
    remarks_info = remarks.parse(remarks_str)
    humidity = get_relative_humidity(temperature, dewpoint, remarks_info, units)
    struct = MetarData(
        altimeter=altimeter,
        clouds=clouds,
        dewpoint=dewpoint,
        flight_rules=FLIGHT_RULES[condition],
        other=other,
        raw=report,
        relative_humidity=humidity,
        remarks_info=remarks_info,
        remarks=remarks_str,
        runway_visibility=runway_visibility,
        sanitized=sanitized,
        station=station,
        temperature=temperature,
        time=core.make_timestamp(time, target_date=issued),
        visibility=visibility,
        wind_direction=wind_direction,
        wind_gust=wind_gust,
        wind_speed=wind_speed,
        wind_variable_direction=wind_variable_direction,
        wx_codes=wx_codes,
    )
    return struct, units


def parse_in(report: str, issued: date = None) -> Tuple[MetarData, Units]:
    """Parser for the International METAR variant"""
    # pylint: disable=too-many-locals
    units = Units(**IN_UNITS)
    sanitized, remarks_str, data = sanitize(report)
    data, station, time = core.get_station_and_time(data)
    data, runway_visibility = get_runway_visibility(data)
    if "CAVOK" not in data:
        data, clouds = core.get_clouds(data)
    (
        data,
        wind_direction,
        wind_speed,
        wind_gust,
        wind_variable_direction,
    ) = core.get_wind(data, units)
    data, altimeter = get_altimeter(data, units, "IN")
    if "CAVOK" in data:
        visibility = core.make_number("CAVOK")
        clouds = []
        data.remove("CAVOK")
    else:
        data, visibility = core.get_visibility(data, units)
    data, temperature, dewpoint = get_temp_and_dew(data)
    condition = core.get_flight_rules(visibility, core.get_ceiling(clouds))
    other, wx_codes = get_wx_codes(data)
    remarks_info = remarks.parse(remarks_str)
    humidity = get_relative_humidity(temperature, dewpoint, remarks_info, units)
    struct = MetarData(
        altimeter=altimeter,
        clouds=clouds,
        dewpoint=dewpoint,
        flight_rules=FLIGHT_RULES[condition],
        other=other,
        raw=report,
        relative_humidity=humidity,
        remarks_info=remarks_info,
        remarks=remarks_str,
        runway_visibility=runway_visibility,
        sanitized=sanitized,
        station=station,
        temperature=temperature,
        time=core.make_timestamp(time, target_date=issued),
        visibility=visibility,
        wind_direction=wind_direction,
        wind_gust=wind_gust,
        wind_speed=wind_speed,
        wind_variable_direction=wind_variable_direction,
        wx_codes=wx_codes,
    )
    return struct, units


class Metar(Report):
    """Class to handle METAR report data"""

    data: Optional[MetarData] = None
    translations: Optional[MetarTrans] = None

    async def _pull_from_default(self) -> None:
        """Checks for a more recent report from NOAA. Only sync"""
        service = NOAA(self.__class__.__name__.lower())
        if self.icao is None:
            return
        report = await service.async_fetch(self.icao)
        if report is not None:
            data, units = parse(self.icao, report, self.issued)
            if not data or data.time is None or data.time.dt is None:
                return
            if (
                not self.data
                or self.data.time is None
                or self.data.time.dt is None
                or data.time.dt > self.data.time.dt
            ):
                self.data, self.units = data, units
                self.source = service.root

    @property
    def _should_check_default(self) -> bool:
        """Returns True if pulled from regional source and potentially out of date"""
        if isinstance(self.service, NOAA) or self.source is None:
            return False

        if self.data is None or self.data.time is None or self.data.time.dt is None:
            return True
        time_since = datetime.now(tz=timezone.utc) - self.data.time.dt
        return time_since > timedelta(minutes=90)

    def _calculate_altitudes(self):
        """Adds the pressure and density altitudes to data if all fields are available"""
        if self.data is None:
            return
        # Select decimal temperature if available
        temp = self.data.temperature
        if self.data.remarks_info is not None:
            temp = self.data.remarks_info.temperature_decimal or temp
        alt = self.data.altimeter
        if temp is None or temp.value is None or alt is None or alt.value is None:
            return
        alt, temp = alt.value, temp.value
        elev = self.station.elevation_ft
        if elev is None:
            return
        self.data.pressure_altitude = core.pressure_altitude(
            alt, elev, self.units.altimeter
        )
        self.data.density_altitude = core.density_altitude(alt, temp, elev, self.units)

    async def _post_update(self):
        if self.icao is None or self.raw is None:
            return
        self.data, self.units = parse(self.icao, self.raw, self.issued)
        if self._should_check_default:
            await self._pull_from_default()
        if self.data is None or self.units is None:
            return
        self._calculate_altitudes()
        self.translations = translate_metar(self.data, self.units)

    def _post_parse(self):
        if self.icao is None or self.raw is None:
            return
        self.data, self.units = parse(self.icao, self.raw, self.issued)
        if self.data is None or self.units is None:
            return
        self._calculate_altitudes()
        self.translations = translate_metar(self.data, self.units)

    @staticmethod
    def sanitize(report: str) -> str:
        """Sanitizes a METAR string"""
        return sanitize(report)[0]

    @property
    def summary(self) -> Optional[str]:
        """Condensed report summary created from translations"""
        if not self.translations:
            self.update()
        if self.translations is None:
            return None
        return summary.metar(self.translations)

    @property
    def speech(self) -> Optional[str]:
        """Report summary designed to be read by a text-to-speech program"""
        if not self.data:
            self.update()
        if self.data is None or self.units is None:
            return None
        return speech.metar(self.data, self.units)
