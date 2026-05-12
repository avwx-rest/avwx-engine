"""TAF parsing.

A TAF (Terminal Aerodrome Forecast) is a 24-hour weather forecast for the area
5 statute miles from the reporting station.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from avwx.current.base import Report, get_wx_codes
from avwx.parsing import core, speech, summary
from avwx.parsing.remarks import parse as parse_remarks
from avwx.parsing.sanitization.taf import clean_taf_list, clean_taf_string
from avwx.parsing.translate.taf import translate_taf
from avwx.static.core import FLIGHT_RULES
from avwx.static.taf import TAF_NEWLINE, TAF_NEWLINE_STARTSWITH, TAF_RMK
from avwx.station import uses_na_format, valid_station
from avwx.structs import (
    FlightRules,
    Sanitization,
    TafData,
    TafLineData,
    TafLineRepr,
    TafRepr,
    TafTrans,
    Timestamp,
)
from avwx.units import Measurement

if TYPE_CHECKING:
    from datetime import date


class Taf(Report):
    """Manages TAF data for a single station."""

    data: TafData | None = None
    repr: TafRepr | None = None
    translations: TafTrans | None = None  # type: ignore

    async def _post_update(self) -> None:
        if self.code is None or self.raw is None:
            return
        self.data, self.repr, self.sanitization = parse(self.code, self.raw, self.issued)
        if self.data is None or self.repr is None:
            return
        self.translations = translate_taf(self.data, self.repr)

    def _post_parse(self) -> None:
        if self.code is None or self.raw is None:
            return
        self.data, self.repr, self.sanitization = parse(self.code, self.raw, self.issued)
        if self.data is None or self.repr is None:
            return
        self.translations = translate_taf(self.data, self.repr)

    @property
    def summary(self) -> list[str]:
        if not self.translations:
            self.update()
        if self.translations is None:
            return []
        return [summary.taf(trans) for trans in self.translations.forecast]

    @property
    def speech(self) -> str | None:
        if not self.data or not self.repr:
            self.update()
        return None if (self.data is None or self.repr is None) else speech.taf(self.data, self.repr)


# ---------------------------------------------------------------------------
# Line-level fixes
# ---------------------------------------------------------------------------

_LINE_FIXES = {
    "TEMP0": "TEMPO",
    "TEMP O": "TEMPO",
    "TMPO": "TEMPO",
    "TE MPO": "TEMPO",
    "TEMP ": "TEMPO ",
    "T EMPO": "TEMPO",
    " EMPO": " TEMPO",
    "TEMO": "TEMPO",
    "BECM G": "BECMG",
    "BEMCG": "BECMG",
    "BE CMG": "BECMG",
    "B ECMG": "BECMG",
    " BEC ": " BECMG ",
    "BCEMG": "BECMG",
    "BEMG": "BECMG",
}


def sanitize_line(txt: str, sans: Sanitization) -> str:
    for key, fix in _LINE_FIXES.items():
        if key in txt:
            txt = txt.replace(key, fix)
            sans.log(key, fix)
    for item in ("BECMG", "TEMPO"):
        if item in txt and f"{item} " not in txt:
            index = txt.find(item) + len(item)
            txt = f"{txt[:index]} {txt[index:]}"
            sans.extra_spaces_needed = True
    return txt


def get_taf_remarks(txt: str) -> tuple[str, str]:
    remarks_start = core.find_first_in_list(txt, TAF_RMK)
    if remarks_start == -1:
        return txt, ""
    return txt[:remarks_start].strip(), txt[remarks_start:]


def get_alt_ice_turb(
    data: list[str],
) -> tuple[list[str], Measurement | None, str | None, list[str], list[str]]:
    """Return remaining tokens, optional altimeter, raw altimeter repr, icing list, turbulence list."""
    altimeter: Measurement | None = None
    raw_alt: str | None = None
    icing: list[str] = []
    turbulence: list[str] = []
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item.startswith("QNH") and item[3:7].isdigit():
            raw = data.pop(i)[3:7]
            try:
                val = float(f"{raw[:2]}.{raw[2:]}") if raw[0] in ("2", "3") else float(raw)
                unit = "inHg" if raw[0] in ("2", "3") else "hPa"
                altimeter = Measurement(val, unit)
                raw_alt = item
            except ValueError:
                pass
        elif item.isdigit():
            if item[0] == "6":
                icing.append(data.pop(i))
            elif item[0] == "5":
                turbulence.append(data.pop(i))
    return data, altimeter, raw_alt, icing, turbulence


def is_normal_time(item: str) -> bool:
    return len(item) == 9 and item[4] == "/" and item[:4].isdigit() and item[5:].isdigit()


def starts_new_line(item: str) -> bool:
    if item in TAF_NEWLINE:
        return True
    return any(item.startswith(start) for start in TAF_NEWLINE_STARTSWITH)


def split_taf(txt: str) -> list[str]:
    lines = []
    split = txt.split()
    last_index = 0
    it = enumerate(split)
    next(it)
    for i, item in it:
        if (starts_new_line(item) and not split[i - 1].startswith("PROB")) or (
            is_normal_time(item) and not starts_new_line(split[i - 1])
        ):
            lines.append(" ".join(split[last_index:i]))
            last_index = i
    lines.append(" ".join(split[last_index:]))
    return lines


def get_type_and_times(
    data: list[str],
) -> tuple[list[str], str, str | None, str | None, str | None]:
    report_type, start_time, end_time, transition = "FROM", None, None, None
    if data and (data[0] in TAF_NEWLINE or (len(data[0]) == 6 and data[0].startswith("PROB"))):
        report_type = data.pop(0)
    if data:
        item, length = data[0], len(data[0])
        if is_normal_time(item):
            start_time, end_time = data.pop(0).split("/")
        elif len(data) >= 2 and length == 4 and len(data[1]) == 4 and item.isdigit() and data[1].isdigit():
            start_time = data.pop(0)
            end_time = data.pop(0)
        elif length == 6 and item.isdigit() and item[-2:] == "00":
            start_time = data.pop(0)[:4]
        elif length > 7 and item.startswith("FM"):
            report_type = "FROM"
            if "/" in item and item[2:].split("/")[0].isdigit() and item[2:].split("/")[1].isdigit():
                start_time, end_time = data.pop(0)[2:].split("/")
            elif item[2:8].isdigit():
                start_time = data.pop(0)[2:6]
            if data and len(data[0]) > 7 and data[0].startswith("TL") and data[0][2:8].isdigit():
                end_time = data.pop(0)[2:6]
        elif report_type == "BECMG" and length == 5:
            if item[-1] == "/" and item[:4].isdigit():
                start_time = data.pop(0)[:4]
            elif item[0] == "/" and item[1:].isdigit():
                end_time = data.pop(0)[1:]
    if report_type == "BECMG":
        transition, start_time, end_time = start_time, end_time, None
    return data, report_type, start_time, end_time, transition


def _is_tempo_or_prob(line: TafLineData) -> bool:
    return line.type == "TEMPO" or line.probability is not None


def _get_next_time(lines: list[TafLineData], target: str) -> Timestamp | None:
    for line in lines:
        if _is_tempo_or_prob(line):
            continue
        if target == "start_time" and line.type == "BECMG" and line.transition_start:
            return line.transition_start
        time = getattr(line, target, None)
        if time:
            return time  # type: ignore[return-value]
    return None


def find_missing_taf_times(
    lines: list[TafLineData],
    start: Timestamp | None,
    end: Timestamp | None,
) -> list[TafLineData]:
    """Fill in missing start/end times by looking at neighbouring lines."""
    if not lines:
        return lines
    lines[0] = lines[0].model_copy(update={"start_time": start})
    last_fm_line = 0
    for i, line in enumerate(lines):
        if _is_tempo_or_prob(line):
            continue
        last_fm_line = i
        for target, other, direction in (("start_time", "end_time", -1), ("end_time", "start_time", 1)):
            if not getattr(line, target):
                value = _get_next_time(lines[i::direction][1:], other)
                lines[i] = lines[i].model_copy(update={target: value})
                line = lines[i]  # noqa: PLW2901
    if last_fm_line:
        lines[last_fm_line] = lines[last_fm_line].model_copy(update={"end_time": end})
    if lines and not lines[0].end_time:
        lines[0] = lines[0].model_copy(update={"end_time": end})
    return lines


def get_wind_shear(data: list[str]) -> tuple[list[str], str | None]:
    shear = None
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item.startswith("WS") and item[5] == "/":
            shear = data.pop(i).replace("KT", "")
    return data, shear


def get_temp_min_and_max(
    data: list[str],
) -> tuple[list[str], str | None, str | None]:
    temp_max, temp_min = "", ""
    for i, item in reversed(list(enumerate(data))):
        if len(item) > 6 and item[0] == "T" and "/" in item:
            if item[1] == "X":
                temp_max = data.pop(i)
            elif item[1] == "N":
                temp_min = data.pop(i)
            elif item[1] == "M" or item[1].isdigit():
                if temp_min:
                    if int(temp_min[2 : temp_min.find("/")].replace("M", "-")) > int(
                        item[1 : item.find("/")].replace("M", "-")
                    ):
                        temp_max, temp_min = f"TX{temp_min[2:]}", f"TN{item[1:]}"
                    else:
                        temp_max = f"TX{item[1:]}"
                else:
                    temp_min = f"TN{item[1:]}"
                data.pop(i)
    return data, temp_max or None, temp_min or None


def get_oceania_temp_and_alt(data: list[str]) -> tuple[list[str], list[str], list[str]]:
    tlist: list[str] = []
    qlist: list[str] = []
    if "T" in data:
        data, tlist = core.get_digit_list(data, data.index("T"))
    if "Q" in data:
        data, qlist = core.get_digit_list(data, data.index("Q"))
    return data, tlist, qlist


def get_taf_flight_rules(lines: list[TafLineData]) -> list[TafLineData]:
    """Assign flight rules to each line, inheriting visibility/clouds from earlier lines."""
    for i, line in enumerate(lines):
        temp_vis: Measurement | None = line.visibility
        temp_cloud = line.clouds
        is_clear = False
        vis_repr: str | None = None

        for report in reversed(lines[: i + 1]):
            if _is_tempo_or_prob(report):
                continue
            if not temp_vis:
                temp_vis = report.visibility
            if "SKC" in report.other or "CLR" in report.other:
                is_clear = True
            elif not temp_cloud:
                temp_cloud = report.clouds
            if temp_vis and temp_cloud is not None:
                break

        if is_clear:
            temp_cloud = []

        # Detect CAVOK by magnitude (9999 m set by parser for CAVOK tokens)
        if temp_vis and temp_vis.magnitude >= 9999 and "m" in temp_vis.unit:
            vis_repr = "CAVOK"

        condition = core.get_flight_rules(temp_vis, vis_repr, core.get_ceiling(temp_cloud))
        lines[i] = lines[i].model_copy(update={"flight_rules": FlightRules(FLIGHT_RULES[condition])})

    return lines


def fix_report_header(report: str) -> str:
    split_report = report.split()
    header_length = min(len(split_report), 6)
    headers = list(split_report[:header_length])
    fixed_headers = []
    for target in ("TAF", "AMD", "COR"):
        with suppress(ValueError):
            headers.remove(target)
            fixed_headers.append(target)
    return " ".join(fixed_headers + headers + split_report[header_length:])


def _is_possible_start_end_time_slash(item: str) -> bool:
    return len(item) == 5 and (
        (item[-1] == "/" and item[:4].isdigit()) or (item[0] == "/" and item[1:].isdigit())
    )


def parse(
    station: str,
    report: str,
    issued: date | None = None,
) -> tuple[TafData | None, TafRepr | None, Sanitization | None]:
    """Parse a TAF report string into ``(TafData, TafRepr, Sanitization)``."""
    if not report:
        return None, None, None
    valid_station(station)
    report = fix_report_header(report)
    is_amended, is_correction = False, False
    while len(report) > 3 and report[:4] in ("TAF ", "AMD ", "COR "):
        if report[:3] == "AMD":
            is_amended = True
        elif report[:3] == "COR":
            is_correction = True
        report = report[4:]
    sans = Sanitization()
    sanitized = clean_taf_string(report, sans)
    _, new_station, time = core.get_station_and_time(sanitized[:20].split())
    if new_station is not None:
        station = new_station
    sanitized = sanitized.replace(station, "")
    if time:
        sanitized = sanitized.replace(time, "").strip()
    use_na = uses_na_format(station)
    sanitized, rmk = get_taf_remarks(sanitized)
    if rmk.startswith("AMD"):
        is_amended = True
    lines = split_taf(sanitized)
    parsed_lines, parsed_reprs = parse_lines(lines, use_na, sans, issued)
    max_temp: str | None = None
    min_temp: str | None = None
    start_time: Timestamp | None = None
    end_time: Timestamp | None = None
    if parsed_lines:
        other, max_temp, min_temp = get_temp_min_and_max(list(parsed_lines[-1].other))
        parsed_lines[-1] = parsed_lines[-1].model_copy(update={"other": other})
        if not (max_temp or min_temp):
            other, max_temp, min_temp = get_temp_min_and_max(list(parsed_lines[0].other))
            parsed_lines[0] = parsed_lines[0].model_copy(update={"other": other})
        start_time = parsed_lines[0].start_time
        end_time = parsed_lines[0].end_time
        parsed_lines[0] = parsed_lines[0].model_copy(update={"end_time": None})
        parsed_lines = find_missing_taf_times(parsed_lines, start_time, end_time)
        parsed_lines = get_taf_flight_rules(parsed_lines)
    alts: list[str] | None = None
    temps: list[str] | None = None
    if station[0] == "A" and parsed_lines:
        other, alts, temps = get_oceania_temp_and_alt(list(parsed_lines[-1].other))
        parsed_lines[-1] = parsed_lines[-1].model_copy(update={"other": other})
    for i, line in enumerate(parsed_lines):
        other_clean, wx_codes = get_wx_codes(list(line.other))
        parsed_lines[i] = parsed_lines[i].model_copy(update={"other": other_clean, "wx_codes": wx_codes})
        if i < len(parsed_reprs):
            parsed_reprs[i] = parsed_reprs[i].model_copy(update={"other": other_clean, "wx_codes": []})
    sanitized = " ".join(i for i in (station, time, sanitized) if i)
    struct = TafData(
        raw=report,
        sanitized=sanitized,
        station=station,
        time=core.make_timestamp(time, target_date=issued),
        remarks=rmk,
        remarks_info=parse_remarks(rmk),
        forecast=parsed_lines,
        start_time=start_time,
        end_time=end_time,
        is_amended=is_amended,
        is_correction=is_correction,
        max_temp=max_temp,
        min_temp=min_temp,
        alts=alts,
        temps=temps,
    )
    repr_struct = TafRepr(
        raw=report,
        sanitized=sanitized,
        station=station,
        time=time,
        remarks=rmk,
        forecast=parsed_reprs,
    )
    return struct, repr_struct, sans


def parse_lines(
    lines: list[str],
    use_na: bool,
    sans: Sanitization,
    issued: date | None = None,
) -> tuple[list[TafLineData], list[TafLineRepr]]:
    parsed_lines: list[TafLineData] = []
    parsed_reprs: list[TafLineRepr] = []
    prob = ""
    while lines:
        raw_line = lines[0].strip()
        line = sanitize_line(raw_line, sans)
        if line.startswith("PROB"):
            if len(line) == 6:
                prob = line
                line = ""
            elif len(line) > 6:
                prob = line[:6]
                line = line[6:].strip()
        if line:
            parsed_line, parsed_repr = parse_line(line, use_na, sans, issued)
            prob_value: float | None = None
            prob_repr: str | None = None
            if prob and " " not in prob:
                prob_repr = prob
                try:
                    prob_value = float(prob[4:])
                except ValueError:
                    pass
            sanitized = f"{prob} {parsed_line.sanitized}".strip() if prob else parsed_line.sanitized
            parsed_line = parsed_line.model_copy(
                update={"probability": prob_value, "raw": raw_line, "sanitized": sanitized}
            )
            parsed_repr = parsed_repr.model_copy(
                update={"probability": prob_repr, "raw": raw_line, "sanitized": sanitized}
            )
            prob = ""
            parsed_lines.append(parsed_line)
            parsed_reprs.append(parsed_repr)
        lines.pop(0)
    return parsed_lines, parsed_reprs


def parse_line(
    line: str,
    use_na: bool,
    sans: Sanitization,
    issued: date | None = None,
) -> tuple[TafLineData, TafLineRepr]:
    data: list[str] = core.dedupe(line.split())
    old_time = data[1] if len(data) > 1 and _is_possible_start_end_time_slash(data[1]) else None
    data = clean_taf_list(data, sans)
    if old_time and len(data) > 1 and data[1] == old_time.strip("/"):
        data[1] = old_time
    sanitized = " ".join(data)
    data, report_type, start_time, end_time, transition = get_type_and_times(data)
    data, wind_shear = get_wind_shear(data)
    data, wind_dir, wind_spd, wind_gust, wind_var, wind_unit, raw_wind, raw_vardir = core.get_wind(data)

    visibility: Measurement | None = None
    raw_vis: str | None = None
    clouds = []
    raw_clouds: list[str] = []

    if "CAVOK" in data:
        visibility = Measurement(9999, "m")
        raw_vis = "CAVOK"
        data = [t for t in data if t != "CAVOK"]
    else:
        data, visibility, raw_vis, _unit = core.get_visibility(data)
        data, clouds, raw_clouds = core.get_clouds(data)

    other, altimeter, raw_alt, icing, turbulence = get_alt_ice_turb(data)
    raw_wind_dir = core.wind_dir_repr(raw_wind)

    line_data = TafLineData(
        altimeter=altimeter,
        clouds=clouds,
        flight_rules=FlightRules.VFR,  # placeholder; set by get_taf_flight_rules
        other=other,
        visibility=visibility,
        wind_direction=wind_dir,
        wind_gust=wind_gust,
        wind_speed=wind_spd,
        wx_codes=[],
        end_time=core.make_timestamp(end_time, target_date=issued),
        icing=icing,
        probability=None,
        raw=line,
        sanitized=sanitized,
        start_time=core.make_timestamp(start_time, target_date=issued),
        transition_start=core.make_timestamp(transition, target_date=issued),
        turbulence=turbulence,
        type=report_type,
        wind_shear=wind_shear,
        wind_variable_direction=wind_var,
    )
    line_repr = TafLineRepr(
        altimeter=raw_alt,
        clouds=raw_clouds,
        other=other,
        visibility=raw_vis,
        wind_direction=raw_wind_dir,
        wind_gust=None,
        wind_speed=None,
        wx_codes=[],
        end_time=end_time,
        icing=icing,
        probability=None,
        raw=line,
        sanitized=sanitized,
        start_time=start_time,
        turbulence=turbulence,
        type=report_type,
        wind_shear=wind_shear,
        wind_variable_direction=[raw_vardir] if raw_vardir else None,
    )
    return line_data, line_repr
