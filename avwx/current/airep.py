"""
"""

from avwx.current.base import Reports
from avwx.parsing import core
from avwx.structs import AirepData


def parse(report: str) -> AirepData:
    """
    """
    if not report:
        return None
    clean = core.sanitize_report_string(report)
    wxdata = core.sanitize_report_list(clean.split())
    wxresp = {"raw": report, "sanitized": " ".join(wxdata)}
    print(wxdata)
    print(wxresp)
    return None


class Aireps(Reports):
    """
    Class to handle aircraft report data
    """

    data: [AirepData] = None

    @staticmethod
    def _report_filter(reports: [str]) -> [str]:
        """
        Removes PIREPs before updating raw_reports
        """
        return [r for r in reports if r.startswith("ARP")]

    def _post_update(self):
        self.data = []
        for report in self.raw:
            parse(report)
