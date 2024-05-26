"""METAR sanitization support."""

# module
from avwx.parsing.sanitization.base import sanitize_list_with, sanitize_string_with
from avwx.parsing.sanitization.cleaners.base import CleanerListType
from avwx.parsing.sanitization.cleaners.cleaners import OnlySlashes, TrimWxCode
from avwx.parsing.sanitization.cleaners.joined import (
    JoinedCloud,
    JoinedRunwayVisibility,
    JoinedTimestamp,
    JoinedWind,
)
from avwx.parsing.sanitization.cleaners.remove import RemoveFromMetar
from avwx.parsing.sanitization.cleaners.replace import CURRENT, ReplaceItem
from avwx.parsing.sanitization.cleaners.separated import (
    SeparatedAltimeterLetter,
    SeparatedCloudAltitude,
    SeparatedCloudQualifier,
    SeparatedDistance,
    SeparatedFirstTemperature,
    SeparatedSecondTemperature,
    SeparatedTemperatureTrailingDigit,
    SeparatedWindUnit,
)
from avwx.parsing.sanitization.cleaners.visibility import RunwayVisibilityUnit, VisibilityGreaterThan
from avwx.parsing.sanitization.cleaners.wind import (
    DoubleGust,
    EmptyWind,
    MisplaceWindKT,
    NonGGust,
    RemoveVrbLeadingDigits,
    WindLeadingMistype,
)

METAR_REPL = {
    **CURRENT,
    "Z/ ": "Z ",
}


clean_metar_string = sanitize_string_with(METAR_REPL)


CLEANERS: CleanerListType = [
    OnlySlashes,
    EmptyWind,
    TrimWxCode,
    SeparatedDistance,
    SeparatedFirstTemperature,
    SeparatedCloudAltitude,
    SeparatedSecondTemperature,
    SeparatedAltimeterLetter,
    SeparatedTemperatureTrailingDigit,
    SeparatedWindUnit,
    SeparatedCloudQualifier,
    RemoveFromMetar,
    ReplaceItem,
    VisibilityGreaterThan,
    MisplaceWindKT,
    RunwayVisibilityUnit,
    DoubleGust,
    WindLeadingMistype,
    NonGGust,
    RemoveVrbLeadingDigits,
    JoinedCloud,
    JoinedTimestamp,
    JoinedWind,
    JoinedRunwayVisibility,
    ### Other wind fixes
]

clean_metar_list = sanitize_list_with(CLEANERS)
