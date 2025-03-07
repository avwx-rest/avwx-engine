"""
A METAR (Meteorological Aerodrome Report) is the surface weather observed at
most controlled (and some uncontrolled) airports. They are updated once per
hour or when conditions change enough to warrant an update, and the
observations are valid for one hour after the report was issued or until the
next report is issued.
"""

# stdlib
from __future__ import annotations

from contextlib import suppress
from datetime import date, datetime, timedelta, timezone

# module
from avwx.current.base import Report, get_wx_codes
from avwx.parsing import core, remarks, speech, summary
from avwx.parsing.sanitization.metar import clean_metar_list, clean_metar_string
from avwx.parsing.translate.metar import translate_metar
from avwx.service import Noaa
from avwx.static.core import FLIGHT_RULES
from avwx.static.metar import METAR_RMK
from avwx.station import uses_na_format, valid_station
from avwx.structs import (
    Code,
    MetarData,
    MetarTrans,
    Number,
    RemarksData,
    RunwayVisibility,
    Sanitization,
    Units,
)


class Metar(Report):
    """The Metar class offers an object-oriented approach to managing METAR data
    for a single station.

    Below is typical usage for fetching and pulling METAR data for KJFK.

    ```python
    >>> from avwx import Metar
    >>> kjfk = Metar("KJFK")
    >>> kjfk.station.name
    'John F Kennedy International Airport'
    >>> kjfk.update()
    True
    >>> kjfk.last_updated
    datetime.datetime(2018, 3, 4, 23, 36, 6, 62376)
    >>> kjfk.raw
    'KJFK 042251Z 32023G32KT 10SM BKN060 04/M08 A3008 RMK AO2 PK WND 32032/2251 SLP184 T00441078'
    >>> kjfk.data.flight_rules
    'VFR'
    >>> kjfk.translations.remarks
    {'AO2': 'Automated with precipitation sensor', 'SLP184': 'Sea level pressure: 1018.4 hPa', 'T00441078': 'Temperature 4.4°C and dewpoint -7.8°C'}
    ```

    The `parse` and `from_report` methods can parse a report string if you want
    to override the normal fetching process. Here's an example of a really bad
    day.

    ```python
    >>> from avwx import Metar
    >>> report = 'KSFO 031254Z 36024G55KT 320V040 1/8SM R06/0200D +TS VCFC OVC050 BKN040TCU 14/10 A2978 RMK AIRPORT CLOSED'
    >>> ksfo = Metar.from_report(report)
    True
    >>> ksfo.station.city
    'San Francisco'
    >>> ksfo.last_updated
    datetime.datetime(2018, 3, 4, 23, 54, 4, 353757, tzinfo=datetime.timezone.utc)
    >>> ksfo.data.flight_rules
    'LIFR'
    >>> ksfo.translations.clouds
    'Broken layer at 4000ft (Towering Cumulus), Overcast layer at 5000ft - Reported AGL'
    >>> ksfo.summary
    'Winds N-360 (variable 320 to 040) at 24kt gusting to 55kt, Vis 0.125sm, Temp 14C, Dew 10C, Alt 29.78inHg, Heavy Thunderstorm, Vicinity Funnel Cloud, Broken layer at 4000ft (Towering Cumulus), Overcast layer at 5000ft'
    ```
    """

    data: MetarData | None = None
    translations: MetarTrans | None = None

    async def _pull_from_default(self) -> None:
        """Check for a more recent report from NOAA."""
        service = Noaa(self.__class__.__name__.lower())
        if self.code is None:
            return
        report = await service.async_fetch(self.code)
        if report is not None:
            data, units, sans = parse(self.code, report, self.issued)
            if not data or data.time is None or data.time.dt is None:
                return
            if not self.data or self.data.time is None or self.data.time.dt is None or data.time.dt > self.data.time.dt:
                self.data, self.units, self.sanitization = data, units, sans
                self.source = service.root

    @property
    def _should_check_default(self) -> bool:
        """Return True if pulled from regional source and potentially out of date."""
        if isinstance(self.service, Noaa) or self.source is None:
            return False

        if self.data is None or self.data.time is None or self.data.time.dt is None:
            return True
        time_since = datetime.now(tz=timezone.utc) - self.data.time.dt
        return time_since > timedelta(minutes=90)

    def _calculate_altitudes(self) -> None:
        """Add the pressure and density altitudes to data if all fields are available."""
        if self.data is None or self.station is None or self.units is None:
            return
        # Select decimal temperature if available
        temp = self.data.temperature
        if self.data.remarks_info is not None:
            temp = self.data.remarks_info.temperature_decimal or temp
        alt = self.data.altimeter
        if temp is None or temp.value is None or alt is None or alt.value is None:
            return
        elev = self.station.elevation_ft
        if elev is None:
            return
        self.data.pressure_altitude = core.pressure_altitude(alt.value, elev, self.units.altimeter)
        self.data.density_altitude = core.density_altitude(alt.value, temp.value, elev, self.units)

    async def _post_update(self) -> None:
        if self.code is None or self.raw is None:
            return
        self.data, self.units, self.sanitization = parse(self.code, self.raw, self.issued)
        if self._should_check_default:
            await self._pull_from_default()
        if self.data is None or self.units is None:
            return
        self._calculate_altitudes()
        self.translations = translate_metar(self.data, self.units)

    def _post_parse(self) -> None:
        if self.code is None or self.raw is None:
            return
        self.data, self.units, self.sanitization = parse(self.code, self.raw, self.issued)
        if self.data is None or self.units is None:
            return
        self._calculate_altitudes()
        self.translations = translate_metar(self.data, self.units)

    @staticmethod
    def sanitize(report: str) -> str:
        """Sanitize a METAR string."""
        return sanitize(report)[0]

    @property
    def summary(self) -> str | None:
        """Condensed report summary created from translations."""
        if not self.translations:
            self.update()
        return None if self.translations is None else summary.metar(self.translations)

    @property
    def speech(self) -> str | None:
        """Report summary designed to be read by a text-to-speech program."""
        if not self.data:
            self.update()
        if self.data is None or self.units is None:
            return None
        return speech.metar(self.data, self.units)


def get_remarks(txt: str) -> tuple[list[str], str]:
    """Return the report split into components and the remarks string.

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


_RVR_CODES = {
    "M": "less than",
    "A": "greater than",
    "P": "greater than",
    "U": "increasing",
    "I": "increasing",
    "D": "decreasing",
    "F": "decreasing",
    "R": "decreasing",
    "N": "no change",
    "V": "variable",
}


def _parse_rvr_number(value: str) -> Number | None:
    if not value:
        return None
    raw, prefix = value, None
    with suppress(KeyError):
        prefix = _RVR_CODES[value[0]]
        value = value[1:]
    number = core.make_number(value, raw)
    if number is not None and prefix is not None:
        number.spoken = f"{prefix} {number.spoken}"
        number.value = None
    return number


def parse_runway_visibility(value: str) -> RunwayVisibility:
    """Parse a runway visibility range string."""
    raw, trend = value, None
    # TODO: update to check and convert units post visibility parse
    value = value.replace("FT", "")
    with suppress(KeyError):
        trend = Code(value[-1], _RVR_CODES[value[-1]])
        value = value[:-1]
    runway, value, *_ = value[1:].split("/")
    if value:
        possible_numbers = [_parse_rvr_number(n) for n in value.split("V")]
        numbers = [n for n in possible_numbers if n is not None]
        visibility = numbers.pop() if len(numbers) == 1 else None
    else:
        visibility, numbers = None, []
    return RunwayVisibility(
        repr=raw,
        runway=runway,
        visibility=visibility,
        variable_visibility=numbers,
        trend=trend,
    )


def get_runway_visibility(data: list[str]) -> tuple[list[str], list[RunwayVisibility]]:
    """Return the report list and the remove runway visibility list."""
    runway_vis = [
        parse_runway_visibility(data.pop(i))
        for i, item in reversed(list(enumerate(data)))
        if core.is_runway_visibility(item)
    ]
    runway_vis.sort(key=lambda x: x.runway)
    return data, runway_vis


def parse_altimeter(value: str | None) -> Number | None:
    """Parse an altimeter string into a Number."""
    if not value or len(value) < 4:
        return None
    # QNH3003INS
    if len(value) >= 7 and value.endswith("INS"):
        return core.make_number(f"{value[-7:-5]}.{value[-5:-3]}", value, literal=True)
    number = value.replace(".", "")
    # Q1000/10
    if "/" in number:
        number = number.split("/")[0]
    if number.startswith("QNH"):
        number = f"Q{number[1:]}"
    if not (len(number) in {4, 5} and number[-4:].isdigit()):
        return None
    number = number.lstrip("AQ")
    if number[0] in ("2", "3"):
        number = f"{number[:2]}.{number[2:]}"
    elif number[0] not in ("0", "1"):
        return None
    return core.make_number(number, value, number, literal=True)


def get_altimeter(data: list[str], units: Units, version: str = "NA") -> tuple[list[str], Number | None]:
    """Return the report list and the removed altimeter item.

    Version is 'NA' (North American / default) or 'IN' (International)
    """
    values: list[Number] = []
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
    data: list[str],
) -> tuple[list[str], Number | None, Number | None]:
    """Return the report list and removed temperature and dewpoint strings."""
    for i, item in reversed(list(enumerate(data))):
        if "/" in item:
            # ///07
            if item[0] == "/":
                item = "/" + item.lstrip("/")  # noqa: PLW2901
            # 07///
            elif item[-1] == "/":
                item = item.rstrip("/") + "/"  # noqa: PLW2901
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
    temperature: Number | None,
    dewpoint: Number | None,
    remarks_info: RemarksData | None,
    units: Units,
) -> float | None:
    """Calculate relative humidity from preferred temperature and dewpoint."""
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


def sanitize(report: str) -> tuple[str, str, list[str], Sanitization]:
    """Return a sanitized report, remarks, and elements ready for parsing."""
    sans = Sanitization()
    clean = clean_metar_string(report, sans)
    data, remark_str = get_remarks(clean)
    data = core.dedupe(data)
    data = clean_metar_list(data, sans)
    clean = " ".join(data)
    if remark_str:
        clean += f" {remark_str}"
    return clean, remark_str, data, sans


def parse(
    station: str,
    report: str,
    issued: date | None = None,
    use_na: bool | None = None,
) -> tuple[MetarData | None, Units | None, Sanitization | None]:
    """Return MetarData and Units dataclasses with parsed data and their associated units."""
    valid_station(station)
    if not report:
        return None, None, None
    if use_na is None:
        use_na = uses_na_format(station[:2])
    parser = parse_na if use_na else parse_in
    return parser(report, issued)


def parse_na(report: str, issued: date | None = None) -> tuple[MetarData, Units, Sanitization]:
    """Parser for the North American METAR variant."""
    units = Units.north_american()
    sanitized, remarks_str, data, sans = sanitize(report)
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
    return struct, units, sans


def parse_in(report: str, issued: date | None = None) -> tuple[MetarData, Units, Sanitization]:
    """Parser for the International METAR variant."""
    units = Units.international()
    sanitized, remarks_str, data, sans = sanitize(report)
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
    return struct, units, sans
