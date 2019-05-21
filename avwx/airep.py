"""
"""

from avwx import _core
from avwx.structs import AirepData


def parse(report: str) -> AirepData:
    """
    """
    if not report:
        return None
    clean = _core.sanitize_report_string(report)
    wxdata = _core.sanitize_report_list(clean.split())
    wxresp = {"raw": report, "sanitized": " ".join(wxdata)}
    print(wxdata)
    print(wxresp)
    return None
