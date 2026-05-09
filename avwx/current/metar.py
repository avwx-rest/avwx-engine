"""METAR parsing.

A METAR (Meteorological Aerodrome Report) is the surface weather observed at
most controlled (and some uncontrolled) airports. They are updated once per
hour or when conditions change enough to warrant an update, and the
observations are valid for one hour after the report was issued or until the
next report is issued.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import date, datetime, timedelta, timezone

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
    FlightRules,
    MetarData,
    MetarRepr,
    MetarTrans,
    RemarksData,
    RunwayVisibility,
    Sanitization,
)
from avwx.units import Measurement


class Metar(Report):
    """Manages METAR data for a single station.

    ```python
    >>> from avwx import Metar
    >>> kjfk = Metar("KJFK")
    >>> kjfk.update()
    True
    >>> kjfk.data.flight_rules
    <FlightRules.VFR: 'VFR'>
    >>> kjfk.data.wind_speed
    Measurement(23.0, 'kt')
    >>> kjfk.data.wind_speed.to("m/s")
    Measurement(11.83..., 'm / s')
    >>> kjfk.repr.wind_speed
    '23KT'
    ```
    """

    data: MetarData | None = None
    repr: MetarRepr | None = None
    translations: MetarTrans | None = None

    async def _pull_from_default(self) -> None:
        service = Noaa(self.__class__.__name__.lower())
        if self.code is None:
            return
        report = await service.async_fetch(self.code)
        if report is None:
            return
        data, repr_data, sans = parse(self.code, report, self.issued)
        if not data or data.time is None or data.time.dt is None:
            return
        if (
            not self.data
            or self.data.time is None
            or self.data.time.dt is None
            or data.time.dt > self.data.time.dt
        ):
            self.data, self.repr, self.sanitization = data, repr_data, sans
            self.source = service.root

    @property
    def _should_check_default(self) -> bool:
        if isinstance(self.service, Noaa) or self.source is None:
            return False
        if self.data is None or self.data.time is None or self.data.time.dt is None:
            return True
        return datetime.now(tz=timezone.utc) - self.data.time.dt > timedelta(minutes=90)

    def _calculate_altitudes(self) -> None:
        """Derive pressure altitude and density altitude when all inputs are available."""
        if self.data is None or self.station is None:
            return
        temp = self.data.temperature
        if self.data.remarks_info is not None:
            temp = self.data.remarks_info.temperature_decimal or temp
        alt = self.data.altimeter
        if temp is None or alt is None:
            return
        elev = self.station.elevation_ft
        if elev is None:
            return
        press_alt = core.pressure_altitude(alt, elev)
        dens_alt = core.density_altitude(alt, temp, elev)
        # Pydantic frozen models: rebuild with computed fields
        self.data = self.data.model_copy(
            update={"pressure_altitude": press_alt, "density_altitude": dens_alt}
        )

    async def _post_update(self) -> None:
        if self.code is None or self.raw is None:
            return
        self.data, self.repr, self.sanitization = parse(self.code, self.raw, self.issued)
        if self._should_check_default:
            await self._pull_from_default()
        if self.data is None:
            return
        self._calculate_altitudes()
        if self.data is not None:
            self.translations = translate_metar(self.data, self.repr)

    def _post_parse(self) -> None:
        if self.code is None or self.raw is None:
            return
        self.data, self.repr, self.sanitization = parse(self.code, self.raw, self.issued)
        if self.data is None:
            return
        self._calculate_altitudes()
        if self.data is not None:
            self.translations = translate_metar(self.data, self.repr)

    @staticmethod
    def sanitize(report: str) -> str:
        return sanitize(report)[0]

    @property
    def summary(self) -> str | None:
        if not self.translations:
            self.update()
        return None if self.translations is None else summary.metar(self.translations)

    @property
    def speech(self) -> str | None:
        if not self.data:
            self.update()
        if self.data is None or self.repr is None:
            return None
        return speech.metar(self.data, self.repr)


# ---------------------------------------------------------------------------
# Remarks split
# ---------------------------------------------------------------------------


def get_remarks(txt: str) -> tuple[list[str], str]:
    """Split the cleaned report into element tokens and the remarks string."""
    txt = txt.replace("?", "").strip()
    alt_index = len(txt) + 1
    for item in [" A2", " A3", " Q1", " Q0", " Q9"]:
        index = txt.find(item)
        if len(txt) - 6 > index > -1 and txt[index + 2 : index + 6].isdigit():
            alt_index = index
    sig_index = core.find_first_in_list(txt, METAR_RMK)
    if sig_index == -1:
        sig_index = len(txt) + 1
    if sig_index > alt_index > -1:
        return txt[: alt_index + 6].strip().split(), txt[alt_index + 7 :]
    if alt_index > sig_index > -1:
        return txt[:sig_index].strip().split(), txt[sig_index + 1 :]
    return txt.strip().split(), ""


# ---------------------------------------------------------------------------
# Runway visibility
# ---------------------------------------------------------------------------

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


def _parse_rvr_value(value: str) -> Measurement | None:
    if not value:
        return None
    # Strip prefix qualifiers like M, P, A
    if value[0] in _RVR_CODES and value[1:].isdigit():
        value = value[1:]
    try:
        return Measurement(int(value), "ft")
    except ValueError:
        return None


def parse_runway_visibility(value: str) -> RunwayVisibility:
    """Parse a runway visibility range string into a :class:`~avwx.structs.RunwayVisibility`."""
    trend: Code | None = None
    value = value.replace("FT", "")
    with suppress(KeyError):
        trend = Code(repr=value[-1], value=_RVR_CODES[value[-1]])
        value = value[:-1]
    runway, value, *_ = value[1:].split("/")
    if value:
        possible = [_parse_rvr_value(n) for n in value.split("V")]
        numbers = [n for n in possible if n is not None]
        visibility = numbers.pop() if len(numbers) == 1 else None
    else:
        visibility, numbers = None, []
    return RunwayVisibility(
        runway=runway,
        visibility=visibility,
        variable_visibility=numbers,
        trend=trend,
    )


def get_runway_visibility(data: list[str]) -> tuple[list[str], list[RunwayVisibility], list[str]]:
    """Extract runway visibility strings and return typed objects plus raw tokens."""
    raw_tokens: list[str] = []
    rvr_list: list[RunwayVisibility] = []
    for i, item in reversed(list(enumerate(data))):
        if core.is_runway_visibility(item):
            raw_tokens.append(data.pop(i))
            rvr_list.append(parse_runway_visibility(raw_tokens[-1]))
    rvr_list.sort(key=lambda x: x.runway)
    raw_tokens.sort()
    return data, rvr_list, raw_tokens


# ---------------------------------------------------------------------------
# Altimeter
# ---------------------------------------------------------------------------


def parse_altimeter(value: str | None) -> Measurement | None:
    """Parse an altimeter token into a :class:`~avwx.units.Measurement`."""
    if not value or len(value) < 4:
        return None
    if len(value) >= 7 and value.endswith("INS"):
        try:
            return Measurement(float(f"{value[-7:-5]}.{value[-5:-3]}"), "inHg")
        except ValueError:
            return None
    number = value.replace(".", "")
    if "/" in number:
        number = number.split("/")[0]
    if number.startswith("QNH"):
        number = f"Q{number[1:]}"
    if not (len(number) in {4, 5} and number[-4:].isdigit()):
        return None
    number = number.lstrip("AQ")
    try:
        if number[0] in ("2", "3"):
            val = float(f"{number[:2]}.{number[2:]}")
            return Measurement(val, "inHg")
        if number[0] in ("0", "1"):
            return Measurement(float(number), "hPa")
    except (ValueError, IndexError):
        pass
    return None


def get_altimeter(
    data: list[str],
    version: str = "NA",
) -> tuple[list[str], Measurement | None, str | None]:
    """Extract and return the altimeter value and its raw token."""
    values: list[tuple[Measurement, str]] = []
    for _ in range(2):
        if not data:
            break
        m = parse_altimeter(data[-1])
        if m is None:
            break
        values.append((m, data.pop(-1)))
    if not values:
        return data, None, None
    values.sort(key=lambda x: x[0].magnitude)
    altimeter, raw = values[0 if version == "NA" else -1]
    return data, altimeter, raw


# ---------------------------------------------------------------------------
# Temperature / dewpoint
# ---------------------------------------------------------------------------


def _parse_temp_token(tok: str) -> Measurement | None:
    if not tok or tok in ("MM", "XX"):
        return None
    sign = -1 if tok.startswith("M") else 1
    digits = tok.lstrip("M")
    try:
        return Measurement(sign * int(digits), "degC")
    except ValueError:
        return None


def get_temp_and_dew(
    data: list[str],
) -> tuple[list[str], Measurement | None, Measurement | None, str | None, str | None]:
    """Extract temperature and dewpoint tokens and return Measurements + raws."""
    for i, item in reversed(list(enumerate(data))):
        if "/" not in item:
            continue
        if item[0] == "/":
            item = "/" + item.lstrip("/")  # noqa: PLW2901
        elif item[-1] == "/":
            item = item.rstrip("/") + "/"  # noqa: PLW2901
        parts = item.split("/")
        if len(parts) != 2:
            continue
        temp_tok, dew_tok = parts
        if temp_tok not in ("MM", "XX") and not core.is_possible_temp(temp_tok):
            continue
        if dew_tok not in ("MM", "XX") and not core.is_possible_temp(dew_tok):
            continue
        data.pop(i)
        raw_temp = temp_tok if temp_tok not in ("MM", "XX") else None
        raw_dew = dew_tok if dew_tok not in ("MM", "XX") else None
        return data, _parse_temp_token(temp_tok), _parse_temp_token(dew_tok), raw_temp, raw_dew
    return data, None, None, None, None


def get_relative_humidity(
    temperature: Measurement | None,
    dewpoint: Measurement | None,
    remarks_info: RemarksData | None,
) -> float | None:
    """Calculate relative humidity from the best available temperature/dewpoint."""
    if remarks_info is not None:
        temp = remarks_info.temperature_decimal or temperature
        dew = remarks_info.dewpoint_decimal or dewpoint
    else:
        temp, dew = temperature, dewpoint
    if temp is None or dew is None:
        return None
    return core.relative_humidity(temp.magnitude, dew.magnitude, temp.unit)


# ---------------------------------------------------------------------------
# Sanitization entry point
# ---------------------------------------------------------------------------


def sanitize(report: str) -> tuple[str, str, list[str], Sanitization]:
    """Return (sanitized_report, remarks_str, token_list, sanitization_log)."""
    sans = Sanitization()
    clean = clean_metar_string(report, sans)
    data, remark_str = get_remarks(clean)
    data = core.dedupe(data)
    data = clean_metar_list(data, sans)
    clean = " ".join(data)
    if remark_str:
        clean += f" {remark_str}"
    return clean, remark_str, data, sans


# ---------------------------------------------------------------------------
# Parser entry points
# ---------------------------------------------------------------------------


def parse(
    station: str,
    report: str,
    issued: date | None = None,
    *,
    use_na: bool | None = None,
) -> tuple[MetarData | None, MetarRepr | None, Sanitization | None]:
    """Parse a METAR report string into ``(MetarData, MetarRepr, Sanitization)``."""
    valid_station(station)
    if not report:
        return None, None, None
    if use_na is None:
        use_na = uses_na_format(station[:2])
    parser = _parse_na if use_na else _parse_in
    return parser(report, issued)


def _parse_na(
    report: str, issued: date | None = None
) -> tuple[MetarData, MetarRepr, Sanitization]:
    sanitized, remarks_str, data, sans = sanitize(report)
    data, station, time_str = core.get_station_and_time(data)
    data, runway_vis, raw_rvr = get_runway_visibility(data)
    data, clouds, raw_clouds = core.get_clouds(data)
    data, wind_dir, wind_spd, wind_gust, wind_var, wind_unit, raw_wind, raw_vardir = core.get_wind(data)
    data, altimeter, raw_alt = get_altimeter(data, "NA")
    data, visibility, raw_vis, _vis_unit = core.get_visibility(data)
    data, temperature, dewpoint, raw_temp, raw_dew = get_temp_and_dew(data)
    condition = core.get_flight_rules(visibility, raw_vis, core.get_ceiling(clouds))
    other, wx_codes = get_wx_codes(data)
    remarks_info = remarks.parse(remarks_str)
    humidity = get_relative_humidity(temperature, dewpoint, remarks_info)

    raw_wind_dir = core.wind_dir_repr(raw_wind)

    struct = MetarData(
        altimeter=altimeter,
        clouds=clouds,
        dewpoint=dewpoint,
        flight_rules=FlightRules(FLIGHT_RULES[condition]),
        other=other,
        relative_humidity=humidity,
        remarks_info=remarks_info,
        remarks=remarks_str,
        runway_visibility=runway_vis,
        sanitized=sanitized,
        station=station,
        temperature=temperature,
        time=core.make_timestamp(time_str, target_date=issued),
        visibility=visibility,
        wind_direction=wind_dir,
        wind_gust=wind_gust,
        wind_speed=wind_spd,
        wind_variable_direction=wind_var,
        wx_codes=wx_codes,
    )
    repr_struct = MetarRepr(
        raw=report,
        sanitized=sanitized,
        station=station,
        time=time_str,
        remarks=remarks_str,
        altimeter=raw_alt,
        clouds=raw_clouds,
        dewpoint=raw_dew,
        other=other,
        runway_visibility=raw_rvr,
        temperature=raw_temp,
        visibility=raw_vis,
        wind_direction=raw_wind_dir,
        wind_gust=None,  # extracted from wind token
        wind_speed=None,  # extracted from wind token
        wind_variable_direction=[raw_vardir] if raw_vardir else [],
        wx_codes=[c.repr for c in wx_codes],
    )
    return struct, repr_struct, sans


def _parse_in(
    report: str, issued: date | None = None
) -> tuple[MetarData, MetarRepr, Sanitization]:
    sanitized, remarks_str, data, sans = sanitize(report)
    data, station, time_str = core.get_station_and_time(data)
    data, runway_vis, raw_rvr = get_runway_visibility(data)

    cavok = "CAVOK" in data
    if cavok:
        clouds = []
        raw_clouds: list[str] = []
    else:
        data, clouds, raw_clouds = core.get_clouds(data)

    data, wind_dir, wind_spd, wind_gust, wind_var, wind_unit, raw_wind, raw_vardir = core.get_wind(data)
    data, altimeter, raw_alt = get_altimeter(data, "IN")

    if cavok:
        visibility = Measurement(9999, "m")
        raw_vis: str | None = "CAVOK"
        data = [t for t in data if t != "CAVOK"]
    else:
        data, visibility, raw_vis, _vis_unit = core.get_visibility(data)

    data, temperature, dewpoint, raw_temp, raw_dew = get_temp_and_dew(data)
    condition = core.get_flight_rules(visibility, raw_vis, core.get_ceiling(clouds))
    other, wx_codes = get_wx_codes(data)
    remarks_info = remarks.parse(remarks_str)
    humidity = get_relative_humidity(temperature, dewpoint, remarks_info)

    raw_wind_dir: str | None = None
    if raw_wind:
        from avwx.static.core import WIND_UNITS  # noqa: PLC0415
        for key in WIND_UNITS:
            raw_wind_clean = raw_wind.replace(key, "")
            if raw_wind_clean:
                raw_wind_dir = raw_wind_clean[:3]
                break

    struct = MetarData(
        altimeter=altimeter,
        clouds=clouds,
        dewpoint=dewpoint,
        flight_rules=FlightRules(FLIGHT_RULES[condition]),
        other=other,
        relative_humidity=humidity,
        remarks_info=remarks_info,
        remarks=remarks_str,
        runway_visibility=runway_vis,
        sanitized=sanitized,
        station=station,
        temperature=temperature,
        time=core.make_timestamp(time_str, target_date=issued),
        visibility=visibility,
        wind_direction=wind_dir,
        wind_gust=wind_gust,
        wind_speed=wind_spd,
        wind_variable_direction=wind_var,
        wx_codes=wx_codes,
    )
    repr_struct = MetarRepr(
        raw=report,
        sanitized=sanitized,
        station=station,
        time=time_str,
        remarks=remarks_str,
        altimeter=raw_alt,
        clouds=raw_clouds,
        dewpoint=raw_dew,
        other=other,
        runway_visibility=raw_rvr,
        temperature=raw_temp,
        visibility=raw_vis,
        wind_direction=raw_wind_dir,
        wind_gust=None,
        wind_speed=None,
        wind_variable_direction=[raw_vardir] if raw_vardir else [],
        wx_codes=[c.repr for c in wx_codes],
    )
    return struct, repr_struct, sans
