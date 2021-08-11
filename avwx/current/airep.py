"""
"""

# pylint: skip-file
# mypy: ignore-errors

# stdlib
from datetime import date
from typing import List

# module
from avwx.current.base import Reports
from avwx.parsing import sanitization
from avwx.structs import AirepData


def parse(report: str, issued: date = None) -> AirepData:
    """"""
    if not report:
        return None
    clean = sanitization.sanitize_report_string(report)
    wxdata = sanitization.sanitize_report_list(clean.split())
    wxresp = {"raw": report, "sanitized": " ".join(wxdata)}
    print(wxdata)
    print(wxresp)
    return None


class Aireps(Reports):
    """Class to handle aircraft report data"""

    data: List[AirepData] = None

    @staticmethod
    def _report_filter(reports: List[str]) -> List[str]:
        """Removes PIREPs before updating raw_reports"""
        return [r for r in reports if r.startswith("ARP")]

    async def _post_update(self):
        self.data = []
        for report in self.raw:
            parse(report, self.issued)

    def _post_parse(self):
        self.data = []
        for report in self.raw:
            parse(report, self.issued)
