"""
"""

from avwx import core
from avwx.structs import AirepData

def parse(report: str) -> AirepData:
    """
    """
    if not report:
        return None
    clean = core.sanitize_report_string(report)
    wxdata, *_ = core.sanitize_report_list(clean.split())
    wxresp = {'raw': report, 'sanitized': ' '.join(wxdata)}
    print(wxdata)
    print(wxresp)
    return None
