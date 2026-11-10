"""Bulk Service Tests."""

# library
import pytest

# module
from avwx.service import bulk

# tests
from .test_base import ServiceClassTest


class BulkServiceTest(ServiceClassTest):
    """Test bulk downloads from NOAA file server."""

    report_types: tuple[str, ...]
    # Feeds that are legitimately empty when nothing is active
    may_be_empty: tuple[str, ...] = ()

    @property
    def report_type(self) -> str:  # type: ignore
        return self.report_types[0]

    def test_fetch(self) -> None:
        """Test that reports are fetched from service."""
        reports = self.service_class(self.report_type).fetch()  # type: ignore
        assert isinstance(reports, list)
        assert bool(reports)

    async def test_async_fetch(self) -> None:
        """Test that reports are fetched from async service."""
        for report_type in self.report_types:
            service = self.service_class(report_type)
            reports = await service.async_fetch()  # type: ignore
            assert isinstance(reports, list)
            assert all(isinstance(r, str) for r in reports)
            if report_type not in self.may_be_empty:
                assert bool(reports)


class TestNOAABulk(BulkServiceTest):
    """Test bulk downloads from NOAA file server."""

    service_class = bulk.NoaaBulk
    report_types = (
        "metar",
        "taf",
        "aircraftreport",
        "airsigmet",
    )
    may_be_empty = ("airsigmet",)


_SIGMET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<response><data num_results="{n}">{items}</data></response>"""
_ITEM = "<AIRSIGMET><raw_text>{}</raw_text></AIRSIGMET>"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("  \n", []),
        (_SIGMET_XML.format(n=0, items=""), []),
        (_SIGMET_XML.format(n=1, items=_ITEM.format("ONE")), ["ONE"]),
        (_SIGMET_XML.format(n=2, items=_ITEM.format("ONE") + _ITEM.format("TWO")), ["ONE", "TWO"]),
    ],
)
def test_noaa_bulk_extract(raw: str, expected: list[str]) -> None:
    """Test NOAA bulk XML extraction handles empty, single, and multiple results."""
    assert bulk.NoaaBulk("airsigmet")._extract(raw) == expected


class TestIntlBulk(BulkServiceTest):
    """Test bulk downloads from NOAA file server."""

    service_class = bulk.NoaaIntl
    report_types = ("airsigmet",)


class TestOlbsBulk(BulkServiceTest):
    """Test bulk downloads from the Indian OLBS Flight Briefing page."""

    service_class = bulk.OlbsBulk
    report_types = ("metar",)
