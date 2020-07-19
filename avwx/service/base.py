"""
Service base class
"""

# stdlib
from typing import Tuple


class Service:
    """
    Base Service class for fetching reports
    """

    url: str = ""
    report_type: str
    _valid_types: Tuple[str] = tuple()

    def __init__(self, report_type: str):
        if report_type not in self._valid_types:
            raise ValueError(
                f"{report_type} is not a valid report type for {self.__class__.__name__}"
            )
        self.report_type = report_type
