"""TAF sanitization support."""

# module
from avwx.parsing.sanitization.base import sanitize_list_with, sanitize_string_with
from avwx.parsing.sanitization.cleaners.base import CleanerListType
from avwx.parsing.sanitization.cleaners.cleaners import OnlySlashes, TrimWxCode
from avwx.parsing.sanitization.cleaners.joined import (
    JoinedCloud,
    JoinedMinMaxTemperature,
    JoinedTafNewLine,
    JoinedTimestamp,
    JoinedWind,
)
from avwx.parsing.sanitization.cleaners.remove import RemoveFromTaf, RemoveTafAmend
from avwx.parsing.sanitization.cleaners.replace import CURRENT, ReplaceItem
from avwx.parsing.sanitization.cleaners.separated import (
    SeparatedAltimeterLetter,
    SeparatedCloudAltitude,
    SeparatedCloudQualifier,
    SeparatedDistance,
    SeparatedFirstTemperature,
    SeparatedMinMaxTemperaturePrefix,
    SeparatedSecondTemperature,
    SeparatedTafTimePrefix,
    SeparatedTemperatureTrailingDigit,
    SeparatedWindUnit,
)
from avwx.parsing.sanitization.cleaners.visibility import VisibilityGreaterThan
from avwx.parsing.sanitization.cleaners.wind import (
    DoubleGust,
    EmptyWind,
    MisplaceWindKT,
    NonGGust,
    RemoveVrbLeadingDigits,
    WindLeadingMistype,
)

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
