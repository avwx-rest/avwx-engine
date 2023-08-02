"""
TAF sanitization support
"""

# module
from .cleaners.base import CleanerListType
from .cleaners.cleaners import OnlySlashes, TrimWxCode
from .cleaners.joined import (
    JoinedCloud,
    JoinedTimestamp,
    JoinedWind,
    JoinedTafNewLine,
    JoinedMinMaxTemperature,
)
from .cleaners.remove import RemoveFromTaf, RemoveTafAmend
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
    SeparatedTafTimePrefix,
    SeparatedMinMaxTemperaturePrefix,
)
from .cleaners.visibility import VisibilityGreaterThan
from .cleaners.wind import (
    DoubleGust,
    EmptyWind,
    MisplaceWindKT,
    NonGGust,
    RemoveVrbLeadingDigits,
    WindLeadingMistype,
)
from .base import sanitize_list_with, sanitize_string_with


TAF_REPL = {
    **CURRENT,
    "Z/ ": "Z ",
    " PROBB": " PROB",
    " PROBN": " PROB",
    " PROB3P": "PROB30",
    " TMM": " TNM",
    " TMN": " TNM",
    " TXN": " TXM",
    " TNTN": " TN",
    " TXTX": " TX",
    " TXX": " TX",
}


clean_taf_string = sanitize_string_with(TAF_REPL)


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
    SeparatedTafTimePrefix,
    SeparatedMinMaxTemperaturePrefix,
    RemoveFromTaf,
    ReplaceItem,
    RemoveTafAmend,
    VisibilityGreaterThan,
    MisplaceWindKT,
    DoubleGust,
    WindLeadingMistype,
    NonGGust,
    RemoveVrbLeadingDigits,
    JoinedCloud,
    JoinedTimestamp,
    JoinedWind,
    JoinedTafNewLine,
    JoinedMinMaxTemperature,
    ### Other wind fixes
]

clean_taf_list = sanitize_list_with(CLEANERS)
