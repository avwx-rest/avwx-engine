"""
Contains METAR-specific functions for report parsing
"""

# module
from avwx.current.base import Report
from avwx.parsing import core, remarks, speech, summary, translate
from avwx.static import FLIGHT_RULES, IN_UNITS, NA_UNITS
from avwx.station import uses_na_format, valid_station
from avwx.structs import MetarData, Units


def parse(station: str, report: str) -> (MetarData, Units):
    """
    Returns MetarData and Units dataclasses with parsed data and their associated units
    """
    valid_station(station)
    if not report:
        return None, None
    return parse_na(report) if uses_na_format(station[:2]) else parse_in(report)


def parse_na(report: str) -> (MetarData, Units):
    """
    Parser for the North American METAR variant
    """
    units = Units(**NA_UNITS)
    wxresp = {"raw": report}
    clean = core.sanitize_report_string(report)
    wxdata, wxresp["remarks"] = core.get_remarks(clean)
    wxdata = core.dedupe(wxdata)
    wxdata = core.sanitize_report_list(wxdata)
    wxresp["sanitized"] = " ".join(wxdata + [wxresp["remarks"]])
    wxdata, wxresp["station"], wxresp["time"] = core.get_station_and_time(wxdata)
    wxdata, wxresp["runway_visibility"] = core.get_runway_visibility(wxdata)
    wxdata, wxresp["clouds"] = core.get_clouds(wxdata)
    (
        wxdata,
        wxresp["wind_direction"],
        wxresp["wind_speed"],
        wxresp["wind_gust"],
        wxresp["wind_variable_direction"],
    ) = core.get_wind(wxdata, units)
    wxdata, wxresp["altimeter"] = core.get_altimeter(wxdata, units, "NA")
    wxdata, wxresp["visibility"] = core.get_visibility(wxdata, units)
    wxresp["other"], wxresp["temperature"], wxresp["dewpoint"] = core.get_temp_and_dew(
        wxdata
    )
    condition = core.get_flight_rules(
        wxresp["visibility"], core.get_ceiling(wxresp["clouds"])
    )
    wxresp["flight_rules"] = FLIGHT_RULES[condition]
    wxresp["remarks_info"] = remarks.parse(wxresp["remarks"])
    wxresp["time"] = core.make_timestamp(wxresp["time"])
    return MetarData(**wxresp), units


def parse_in(report: str) -> (MetarData, Units):
    """
    Parser for the International METAR variant
    """
    units = Units(**IN_UNITS)
    wxresp = {"raw": report}
    clean = core.sanitize_report_string(report)
    wxdata, wxresp["remarks"] = core.get_remarks(clean)
    wxdata = core.dedupe(wxdata)
    wxdata = core.sanitize_report_list(wxdata)
    wxresp["sanitized"] = " ".join(wxdata + [wxresp["remarks"]])
    wxdata, wxresp["station"], wxresp["time"] = core.get_station_and_time(wxdata)
    wxdata, wxresp["runway_visibility"] = core.get_runway_visibility(wxdata)
    if "CAVOK" not in wxdata:
        wxdata, wxresp["clouds"] = core.get_clouds(wxdata)
    (
        wxdata,
        wxresp["wind_direction"],
        wxresp["wind_speed"],
        wxresp["wind_gust"],
        wxresp["wind_variable_direction"],
    ) = core.get_wind(wxdata, units)
    wxdata, wxresp["altimeter"] = core.get_altimeter(wxdata, units, "IN")
    if "CAVOK" in wxdata:
        wxresp["visibility"] = core.make_number("CAVOK")
        wxresp["clouds"] = []
        wxdata.remove("CAVOK")
    else:
        wxdata, wxresp["visibility"] = core.get_visibility(wxdata, units)
    wxresp["other"], wxresp["temperature"], wxresp["dewpoint"] = core.get_temp_and_dew(
        wxdata
    )
    condition = core.get_flight_rules(
        wxresp["visibility"], core.get_ceiling(wxresp["clouds"])
    )
    wxresp["flight_rules"] = FLIGHT_RULES[condition]
    wxresp["remarks_info"] = remarks.parse(wxresp["remarks"])
    wxresp["time"] = core.make_timestamp(wxresp["time"])
    return MetarData(**wxresp), units


class Metar(Report):
    """
    Class to handle METAR report data
    """

    def _post_update(self):
        self.data, self.units = parse(self.station, self.raw)
        self.translations = translate.metar(self.data, self.units)

    @property
    def summary(self) -> str:
        """
        Condensed report summary created from translations
        """
        if not self.translations:
            self.update()
        return summary.metar(self.translations)

    @property
    def speech(self) -> str:
        """
        Report summary designed to be read by a text-to-speech program
        """
        if not self.data:
            self.update()
        return speech.metar(self.data, self.units)
