"""
METAR sanitization support
"""

# module
from .cleaners.base import CleanerListType
from .cleaners.cleaners import OnlySlashes, TrimWxCode
from .cleaners.joined import (
    JoinedCloud,
    JoinedTimestamp,
    JoinedWind,
    JoinedRunwayVisibility,
)
from .cleaners.remove import RemoveFromMetar
from .cleaners.replace import CURRENT, ReplaceItem
from .cleaners.separated import (
    SeparatedDistance,
    SeparatedFirstTemperature,
    SeparatedCloudAltitude,
    SeparatedSecondTemperature,
    SeparatedAltimeterLetter,
    SeparatedTemperatureTrailingDigit,
    SeparatedWindUnit,
    SeparatedCloudQualifier,
)
from .cleaners.visibility import RunwayVisibilityUnit, VisibilityGreaterThan
from .cleaners.wind import (
    DoubleGust,
    EmptyWind,
    MisplaceWindKT,
    NonGGust,
    RemoveVrbLeadingDigits,
    WindLeadingMistype,
)
from .base import sanitize_list_with, sanitize_string_with


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
